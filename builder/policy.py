"""policy: policy as code for the payment part of a Freya collections call (brief-agnostic).

docs/research/sota-techniques.md T1 (offer guard), T2 (counters in code), T3 (state_line first), T20 (decide in code
what the brief decides), T22 (code-built read-back) and T26 (say what was done). The model no longer decides whether
an offer is allowed, how many attempts are left, which offer comes next, whether the read-back was confirmed or what
gets written: code does, from the brief's parameters, and the model only phrases what code decided.

Architecture (one product or up to N products, the same machine):

    prepare (code: register_product per product, init_negotiation)
      └─> negotiate (conversation; on_enter tts {{say_next}}; extracts topic, stance, offer_kind/date/amount)
            ├─ topic hardship/human/no_talk/paid/dispute ─> pol_<topic> (code)         ┐
            ├─ topic new_plan                            ─> xfer_restructuring        │ every pol_* node runs the
            ├─ offer_kind exact|vague                    ─> check_offer (code)        │ same core with one event,
            ├─ stance accept                             ─> accept_offer (code)       │ writes say_next/state_line
            ├─ stance too_much                           ─> too_much (code)           │ and routes on `route`
            └─ stance refuse                             ─> count_refusal (code)      ┘
      confirm (conversation; on_enter tts {{readback_line}}; extracts confirm yes|no|change)
            ├─ yes    ─> rec_next (code) ─> record_promise (api_request create_promise, values = the read-back)
            │                               ─> rec_after (code: ok / retry once / service_error) ─> ...
            ├─ change ─> change_offer (code: the new value goes through the offer guard, read back again)
            └─ no     ─> confirm_no (code: a flat refusal of the read-back offer)
      record_note loop (api_request add_note, only when the brief uses notes) ─> wrapup | finalize
      wrapup (conversation after a recorded promise; on_enter tts {{wrap_line}}; extracts wrap)
      hardship (conversation; on_enter tts {{say_next}}; support yes/no, a named offer still goes to check_offer)
      every ending: route == 'fin' and final_route == <key> ─> fin_<key> (freyalib.end_pair)

Per-product state lives in string variables written only by code: state_<pid> (open, agreed, refused, paid,
dispute, hardship, recorded, service_error), attempts_used_<pid>, too_much_<pid>, offered_floor_<pid>,
refused_offers_<pid>, agreed_<pid>, vague_asked_<pid>, checks_<pid>, fails_<pid>, noted_<pid>. The facts per product
(words_, full_, floor_, floor_name_, deadline_, ladder_) are written by the generator's prepare code through
register_product(). Every policy node ends by rewriting state_line, offer_question and clearing the extracted
variables (so a stale extraction never routes twice).

Everything a bank decides is a parameter: the texts (finished-sentence templates with [amount] [when] [date]
[deadline] [floor] [floor_name] [full] [words] [named] [past_due] [list] placeholders), the ladder rungs per
product, the floor and deadline, whether notes are used and with which reasons, the fin key per final state, the
retry limit, the holiday calendar. Nothing in this module names a holiday, an amount, a band or an outcome.

Standard library only. Every generated snippet: no '{{' or '}}', never raises, string flags for routing.
"""
from __future__ import annotations

import json
import re

import freyalib as fl

# ----------------------------------------------------------------------------------------------- parameters
STATES = ("open", "agreed", "refused", "paid", "dispute", "hardship", "recorded", "service_error")
AMOUNT_RULES = ("full", "floor", "full_or_floor")

# Generic wording. Every generator should pass the brief's own sentences (verbatim ones above all: the
# text-message sentence after a promise, the mobile-app sentence, the hardship sympathy line).
# Texts a brief decides: the generator MUST pass them (Policy() refuses to build without them), so no other bank's
# wording can reach a hidden brief's agent. The defaults below are neutral placeholders for tests and docs only.
REQUIRED_TEXTS = ("too_much_floor", "paid", "dispute", "hardship", "wrap_change", "human_first", "notalk_first", "recorded",
                  "anything_else", "vague", "after_deadline", "weekend_or_holiday", "below_floor")
REQUIRED_TEXTS_MULTI = ("question_all", "one_by_one", "next_product", "recorded_many", "rec_failed")
DEFAULT_TEXTS = {
    "today_word": "today",
    "on_date": "on [date]",
    "tomorrow_when": "",
    "today_when": "",
    "question": "Can you pay [amount] [when]?",
    "question_product": "For your [words], can you pay [amount] [when]?",
    "question_all": "Can you pay all of them today?",
    "weekend_or_holiday": "[named] is not a business day. The next business day is [date].",
    "after_deadline": "The latest date I can record is [deadline].",
    "before_today": "[named] has already passed.",
    "below_floor": "I cannot record [named]. The lowest amount I can record is [floor].",
    "above_full": "The past-due amount is [full], so I can record at most [full].",
    "above_full_again": "",   # optional: a repeated higher amount at the read-back (above_full='agree')
    "vague": "Which exact day would that be?",
    # a day or an amount cut off mid-word ('Monday the twenty', 'I accept the twenty'): asked again, never guessed
    "cutoff_day": "Sorry, I did not catch the day. Which day would that be?",
    "cutoff_amount": "Sorry, I did not catch that.",
    "vague_deadline": "The latest date I can record is [deadline].",
    "too_much_floor": "The lowest amount I can accept is [floor], the [floor_name].",
    "exhausted": "I understand.",
    "one_by_one": "Let us go through them one by one.",
    "next_product": "Your [words] has [past_due] past due.",
    "paid": "Thank you for letting me know. I will not take a promise for your [words].",
    "dispute": "Thank you for telling me. I will not take a promise for your [words].",
    "hardship": "I am sorry to hear that.",
    "human_first": "Is there anything I can help you with myself first?",
    "notalk_first": "I understand.",
    "readback_head": "To confirm: ",
    "readback_item": "[words], [amount], [when]",
    "readback_sep": "; ",
    "own_deadline": ", which is the latest date I can record for it",
    "moved_bd": ", the next business day",
    "readback_tail": ". Do you confirm?",
    "recorded": "Your promise is recorded.",
    "recorded_many": "Your promises for [list] are recorded.",
    "rec_failed": "I could not record the promise for your [words] because of a technical problem.",
    "anything_else": "Is there anything else I can help you with?",
    "wrap_change": "A recorded promise cannot be changed on this call.",
    "and": " and ",
}

# Extraction variables every policy node clears at its end (enum ones to 'none', value ones to '').
# The platform validates every variable a code node writes against the extraction schema: a value outside an enum
# ('none' for stance/confirm/wrap) or not matching the type ('' for a date or a float) is REJECTED and the old value
# stays (event function_call_complete.validation_errors; seen on Brief A PUB-10: stale offer_date re-fired check_offer
# every turn). So a clear writes a VALID neutral value: the enum's own neutral member, a sentinel date / amount.
CLEAR_ENUMS = {"stance": "other", "offer_kind": "none", "offer_for": "none", "topic": "none", "confirm": "other",
               "hs_answer": "none", "wrap": "other", "aside": "none",
               "offer_ref": "none", "day_refused": "none"}
CLEAR_VALUES = {"offer_date": "1900-01-01", "offer_amount": "0", "offer_when": "", "per_product": "", "customer_said": ""}
SENTINEL_YEAR = 1900
# the customer's own words for the day, resolved in code against the call's date (the platform's date extraction uses
# the real clock: 'tomorrow' arrived as a date before the call's today on Brief B PUB-12)
WHEN_DESC = ("The customer's OWN WORDS for WHEN they will pay, copied exactly as said (for example 'tomorrow', 'next Friday', "
             "'this Saturday', 'the 23rd', 'the sixth of November', 'end of the month', 'when my salary comes'). "
             "Empty when no day or period is mentioned in the latest message, and empty when the customer takes the day back "
             "in the same message before saying the new one ('on Friday, no sorry,' / 'tomorrow, I mean' and it stops): "
             "the corrected day is still to come. A day the customer says they CANNOT pay on is not their day: leave it out "
             "('I can't do Friday, but I can pay it in full' -> empty; 'not Friday, Monday' -> 'Monday').")
# a day turned down while an amount is still offered ('I can't do it this Friday, but I can pay that one in full' and
# the line stops): the amount stands and the day is still to come; the proposal's day is never filled back in
# (extended Brief B EXT-B-14, talkative: the read-back named the Friday the customer had just declined). Read only by
# check_one / offer_date_of; it routes nothing, so a bare 'no' still goes to the stance counter.
DAY_REFUSED_DESC = ("From the customer's LATEST message only. yes = they say the day the agent proposed, or today, does NOT "
                    "work for them ('I can't do Friday', 'not this Friday', 'not today', 'that day is no good'), whether or not "
                    "they also name an amount or another day; 'no, but I can pay it in full' in answer to a question that named "
                    "a day is yes too. none = anything else: a bare no with no amount and no other day, a customer correcting "
                    "their own words ('Friday, sorry, I mean Monday'), or no day turned down at all.")


# an amount named by reference instead of a number ('the minimum', 'the whole amount'): the extractor does not know the
# floor's value, so 'too much, but I can pay the minimum today' arrived with no amount and the guard read back the FULL
# amount (extended Brief A EXT-A-36). The reference is resolved in code against the product's floor / full amount.
VAGUE_STANCE_CLAUSE = (" Exception to anything above: 'I don't know the exact day (yet)', 'not sure which day', 'it varies' or "
                       "'sometime next week' is NOT a refusal, also right after the question for the exact day: it is a vague "
                       "offer (offer_kind vague).")
VAGUE_KIND_CLAUSE = (" After a question for the exact day, 'I don't know the exact day (yet)' or 'not sure which day' is vague.")
SAID_DESC = ("When the customer gives a reason in their LATEST message (a hardship such as illness, a bereavement or "
             "losing their job; why they dispute the debt; that they already paid, when or how; why they will not pay), "
             "that reason in a few of their own words, e.g. 'lost my job last month' or 'paid on Monday by bank transfer'. "
             "Empty when the message gives no reason.")
REF_DESC = ("Whether the customer's LATEST message names the payment amount BY REFERENCE instead of as a number. "
            "floor = the lowest amount the agent can accept, however they call it ('the minimum', 'the lowest amount', 'the "
            "lowest you can take', or the name the agent used for it). full = the whole past-due amount ('all of it', "
            "'the full amount', 'everything'). none = no such reference (also when they say a number).")


def _tpl(s):
    """'{amount}' -> '[amount]' so that generator templates may use either form; no braces reach the code."""
    return re.sub(r"\{(\w+)\}", r"[\1]", str(s))


def _pylit(obj):
    """A Python string literal holding json.dumps(obj), with every brace escaped (\\x7b / \\x7d): the platform
    refuses '{{' / '}}' in code, and a JSON dump of nested objects ends in '}}'."""
    s = json.dumps(obj, ensure_ascii=True)
    s = s.replace("\\", "\\\\").replace("'", "\\'").replace("{", "\\x7b").replace("}", "\\x7d")
    return "'" + s + "'"


# ----------------------------------------------------------------------------------------------- the core source
_CORE = r'''
P = json.loads(__P__)
def g(V, k, d=''):
    v = V.get(k)
    if v is None:
        return d
    s = str(v)
    return d if s.lower() in ('none', 'null') and d == '' else s
def num(x, d=None):
    try:
        s = str(x).replace(',', '').strip()
        if not s or s.lower() in ('none', 'null', 'nan'):
            return d
        m = re.search(r'-?\d+(\.\d+)?', s)
        return float(m.group(0)) if m else d
    except Exception:
        return d
def pdate(x):
    s = str(x or '').strip()
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', s)
    if not m or int(m.group(1)) <= 1900:   # 1900-01-01 is the 'cleared' sentinel (schema-valid date)
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None
def T(key, **kw):
    s = str(P['texts'].get(key) or '')
    for k, v in kw.items():
        s = s.replace('[' + k + ']', str(v))
    return s
def join(parts):
    return ' '.join([str(x).strip() for x in parts if str(x or '').strip()])
def pids(V):
    return [x for x in g(V, 'pids_csv').split(',') if x]
def pg(V, pid, k, d=''):
    return g(V, k + '_' + pid, d)
def pset(V, pid, k, v):
    V[k + '_' + pid] = str(v)
def today_of(V):
    d = pdate(g(V, 'today_iso')) or pdate(g(V, P['now_var']))
    return d or datetime.date(2000, 1, 1)
def when(V, d):
    if d == today_of(V):
        # optional ('' = off): 'today, Friday 16 October' (a simulated customer who said 'this Friday' on a Friday
        # heard a bare 'today', said no and the change loop moved the promise to the next Friday, EXT-A-38)
        return T('today_when', date=txt_short(d)) if T('today_when') else T('today_word')
    # optional ('' = off): 'tomorrow, Thursday 15 October' lets a customer who said 'tomorrow' recognise the day (a
    # simulated customer that does not know the call's date said 'not correct' to the bare date, EXT-A-11)
    if T('tomorrow_when') and d == today_of(V) + datetime.timedelta(days=1):
        return T('tomorrow_when', date=txt_short(d))
    return T('on_date', date=txt_short(d))
def dtext(V, d):
    return T('today_word') if d == today_of(V) else txt_short(d)
def full_of(V, pid):
    return num(pg(V, pid, 'full'), 0.0) or 0.0
def floor_of(V, pid):
    f = num(pg(V, pid, 'floor'))
    return full_of(V, pid) if f is None or f <= 0 else f
def deadline_of(V, pid):
    return pdate(pg(V, pid, 'deadline')) or today_of(V)
def state(V, pid):
    return pg(V, pid, 'state', 'open')
def multi(V):
    return bool(P['multi']) and len(pids(V)) > 1
def question(V, pid, a, d):
    key = 'question_product' if multi(V) else 'question'
    return T(key, amount=fmt(a), when=when(V, d), words=pg(V, pid, 'words'), date=txt_short(d))
def set_prop(V, pid, a, d):
    V['prop_pid'] = pid
    V['prop_amount'] = str(float(a))
    V['prop_date'] = d.isoformat()
    V['offer_question'] = question(V, pid, a, d)
def prop_of(V, pid):
    if g(V, 'prop_pid') == pid:
        a = num(g(V, 'prop_amount'))
        d = pdate(g(V, 'prop_date'))
        if a is not None and d is not None:
            return a, d
    t = today_of(V)
    return full_of(V, pid), (t if isbd(t) else next_bd(t))
def okey(a, d):
    return fmt(a) + '@' + d.isoformat()
def refused_list(V, pid):
    return [x for x in pg(V, pid, 'refused_offers').split(';') if x]
def ladder(V, pid):
    try:
        L = json.loads(pg(V, pid, 'ladder', '[]'))
        return L if isinstance(L, list) else []
    except Exception:
        return []
def rung(V, pid, i):
    r = ladder(V, pid)[i]
    rule = str(r[0])
    d = pdate(r[1]) or deadline_of(V, pid)
    if rule == 'floor':
        a = floor_of(V, pid)
    elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes':
        a = floor_of(V, pid)
    else:
        a = full_of(V, pid)
    return a, d
def back_route(V):
    return 'hardship' if g(V, 'mode') == 'hardship' else 'negotiate'
def say(V, text, route=None):
    V['say_next'] = text
    V['route'] = route or back_route(V)
def register_product(V, pid, words, full, floor, floor_name, deadline, rungs):
    pid = str(pid)
    ids = pids(V)
    if pid not in ids:
        ids.append(pid)
    V['pids_csv'] = ','.join(ids)
    pset(V, pid, 'words', words)
    pset(V, pid, 'full', float(full))
    pset(V, pid, 'floor', float(floor))
    pset(V, pid, 'floor_name', floor_name)
    pset(V, pid, 'deadline', deadline.isoformat())
    lad = []
    for r in rungs:
        rd = r[1]
        if rd > deadline:
            rd = deadline
        lad.append([str(r[0]), rd.isoformat()])
    pset(V, pid, 'ladder', json.dumps(lad))
    for k, v in (('state', 'open'), ('attempts_used', '0'), ('too_much', 'no'), ('offered_floor', 'no'),
                 ('refused_offers', ''), ('agreed', ''), ('vague_asked', 'no'), ('checks', '0'), ('fails', '0'),
                 ('noted', 'no')):
        pset(V, pid, k, v)
def init_negotiation(V, statement):
    ids = pids(V)
    V['mode'] = 'negotiate'
    V['stage'] = 'all' if multi(V) else 'one'
    V['cur_pid'] = ids[0] if ids else ''
    V['human_count'] = '0'
    V['notalk_count'] = '0'
    V['wrap_count'] = '0'
    V['wrap_human'] = '0'
    V['vague_all'] = 'no'
    V['hs_offer'] = 'no'
    V['same_change'] = '0'
    V['wrap_done'] = 'no'
    if ids:
        a, d = prop_of(V, ids[0])
        set_prop(V, ids[0], a, d)
    if V['stage'] == 'all':
        V['offer_question'] = T('question_all')
    V['say_next'] = statement
    V['route'] = 'negotiate'
    finish_turn(V)
def readback(V, ids):
    items = []
    for p in ids:
        parts = pg(V, p, 'agreed').split('|')
        a = num(parts[0], 0.0) if parts else 0.0
        d = pdate(parts[1]) if len(parts) > 1 else None
        tag = parts[2] if len(parts) > 2 else ''
        if d is None:
            continue
        s = T('readback_item', words=pg(V, p, 'words'), amount=fmt(a), when=when(V, d), date=txt_short(d))
        if tag == 'dl':
            s += T('own_deadline')
        elif tag == 'bd':
            s += T('moved_bd')
        items.append(s)
    return T('readback_head') + T('readback_sep').join(items) + T('readback_tail')
def under_way(V, pid):
    # the product's offer is already on the table (a ladder rung was spoken, or it is the product being asked about)
    if g(V, 'prop_pid') != pid or not g(V, 'offer_question'):
        return False
    k = int(num(pg(V, pid, 'attempts_used'), 0) or 0)
    return k >= 1 or (g(V, 'cur_pid') == pid and g(V, 'stage') == 'one')
def start_product(V, pid, prefix):
    if under_way(V, pid):
        # never restarted at rung 0: a claim settled ANOTHER product while this one's offer was on the table, and the
        # restart re-offered an offer already refused with attempts_used reset to 1 (extended Brief B EXT-B-12: the
        # same line ~130 times); the offer on the table is asked again, unchanged
        intro = '' if g(V, 'cur_pid') == pid else T('next_product', words=pg(V, pid, 'words'), past_due=fmt(full_of(V, pid)))
        V['stage'] = 'one'
        V['cur_pid'] = pid
        say(V, join([prefix, intro, V['offer_question']]), 'negotiate')
        return
    V['stage'] = 'one'
    V['cur_pid'] = pid
    if not ladder(V, pid):
        a, d = full_of(V, pid), deadline_of(V, pid)
    else:
        a, d = rung(V, pid, 0)
        pset(V, pid, 'attempts_used', 1)
    set_prop(V, pid, a, d)
    say(V, join([prefix, T('next_product', words=pg(V, pid, 'words'), past_due=fmt(full_of(V, pid))), V['offer_question']]), 'negotiate')
def advance(V, prefix=''):
    ids = pids(V)
    opn = [p for p in ids if state(V, p) == 'open']
    if opn and g(V, 'mode') == 'hardship':
        for p in opn:
            pset(V, p, 'state', 'hardship')
        opn = []
    if opn:
        start_product(V, opn[0], prefix)
        return
    agreed = [p for p in ids if state(V, p) == 'agreed']
    if agreed:
        V['readback_line'] = join([prefix, readback(V, agreed)])
        V['route'] = 'confirm'
        return
    note_next(V)
def agree(V, pid, a, d, tag='', move=True, prefix=''):
    pset(V, pid, 'state', 'agreed')
    pset(V, pid, 'agreed', str(float(a)) + '|' + d.isoformat() + '|' + tag)
    V['ok_pid'] = pid
    V['ok_amount'] = str(float(a))
    V['ok_date'] = d.isoformat()
    V['offer_verdict'] = 'ok'
    set_prop(V, pid, a, d)
    if move:
        advance(V, prefix)
def refuse(V, pid, prefix=''):
    if g(V, 'mode') == 'hardship':
        pset(V, pid, 'state', 'hardship')
        advance(V, '')
        return
    a0, d0 = prop_of(V, pid)
    rl = refused_list(V, pid)
    if okey(a0, d0) not in rl:
        rl.append(okey(a0, d0))
    pset(V, pid, 'refused_offers', ';'.join(rl))
    L = ladder(V, pid)
    k = int(num(pg(V, pid, 'attempts_used'), 0) or 0)
    while k < len(L):
        a, d = rung(V, pid, k)
        if okey(a, d) not in rl:
            break
        k += 1
    if k >= len(L):
        pset(V, pid, 'state', 'refused')
        V['offer_verdict'] = 'exhausted'
        advance(V, join([prefix, T('exhausted')]))
        return
    pset(V, pid, 'attempts_used', k + 1)
    set_prop(V, pid, a, d)
    V['next_offer_text'] = V['offer_question']
    say(V, join([prefix, V['offer_question']]), 'negotiate')
def too_much(V, pid, prefix=''):
    pset(V, pid, 'too_much', 'yes')
    a0, d0 = prop_of(V, pid)
    fl_ = floor_of(V, pid)
    if g(V, 'mode') != 'hardship' and pg(V, pid, 'offered_floor') != 'yes' and fl_ < a0 - 0.005:
        pset(V, pid, 'offered_floor', 'yes')
        set_prop(V, pid, fl_, d0)
        say(V, join([prefix, T('too_much_floor', floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words')), V['offer_question']]))
        return
    refuse(V, pid, prefix)
def check_one(V, pid, a, d, kind):
    if recorded_guard(V, pid):
        return
    n = int(num(pg(V, pid, 'checks'), 0) or 0) + 1
    pset(V, pid, 'checks', n)
    if n > int(P['max_checks']):
        pset(V, pid, 'state', 'hardship' if g(V, 'mode') == 'hardship' else 'refused')
        V['offer_verdict'] = 'loop_exhausted'
        advance(V, T('exhausted'))
        return
    pa, pd = prop_of(V, pid)
    t = today_of(V)
    dl = deadline_of(V, pid)
    dr = d is None and a is not None and kind != 'vague' and g(V, 'day_refused') == 'yes'
    if dr:
        # 'I can't do it this Friday, but I can pay it in full': the amount is offered, the day is not; the proposal's
        # day was just turned down, so it is never filled in (extended Brief B EXT-B-14); the brief's exact-day
        # question asks for it (the amount is kept in vague_amount for the answer)
        kind = 'vague'
    if kind == 'vague' or (a is None and d is None):
        V['offer_verdict'] = 'vague'
        # an amount named with the vague period ('500 next week') is still checked: below the floor -> the brief's line
        # and the floor, above the full amount -> the full amount (generated Brief A GEN-P-04: '500 next week' got
        # only 'which exact day?', and the deadline was then proposed for the full amount)
        pre, amt = '', num(pg(V, pid, 'vague_amount')) or pa
        if a is not None and a > 0:
            fl_, full = floor_of(V, pid), full_of(V, pid)
            if a < fl_ - 0.005:
                if pg(V, pid, 'offered_floor') == 'yes' and g(V, 'mode') != 'hardship':
                    V['offer_verdict'] = 'below_floor'
                    refuse(V, pid)
                    return
                pre = T('below_floor', named=fmt(a), floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words'))
                pset(V, pid, 'offered_floor', 'yes')
                amt = fl_
            elif a > full + 0.005:
                pre = T('above_full', full=fmt(full), named=fmt(a), words=pg(V, pid, 'words'))
                amt = full
            else:
                amt = a
            pset(V, pid, 'vague_amount', str(float(amt)))
        if pg(V, pid, 'vague_asked') != 'yes':
            pset(V, pid, 'vague_asked', 'yes')
            V['vague_pending'] = pid           # the next answer is the answer to 'which exact day?' (see ev_refuse)
            say(V, join([pre, T('vague')]))
            return
        if P.get('vague_again') == 'refuse' and not dr:   # the brief: no exact day after one ask = a non-answer (one attempt)
            # (an amount with a declined day is an offer, never a refusal: it gets the deadline below)
            refuse(V, pid)
            return
        set_prop(V, pid, amt, dl)
        say(V, join([pre, T('vague_deadline', deadline=txt_short(dl), words=pg(V, pid, 'words')), V['offer_question']]))
        return
    amt = pa if a is None or a <= 0 else a
    va = num(pg(V, pid, 'vague_amount'))
    if (a is None or a <= 0) and va and g(V, 'vague_prev') == pid:
        # '500 next week' / 'not Friday, but in full' -> 'which exact day?' -> 'Tuesday': the amount they named, on
        # that day (not the proposal's amount)
        amt = va
    day = pd if d is None else d
    pdl = pdate(pg(V, pid, 'part_deadline'))   # optional: a brief with a shorter last date for part payments
    if pdl and amt is not None and amt < full_of(V, pid) and pdl < dl:
        dl = pdl
    issues = []
    na, nd = amt, day
    if nd < t:
        issues.append(('before_today', T('before_today', named=txt_short(nd))))
        nd = t if isbd(t) else next_bd(t)
    elif nd > dl:
        issues.append(('after_deadline', T('after_deadline', deadline=txt_short(dl), named=txt_short(nd), words=pg(V, pid, 'words'))))
        nd = dl
    elif not isbd(nd):
        nb = next_bd(nd)
        if P['closed_day_move'] == 'before':
            nb = prev_bd(nd)
            if nb < t:
                nb = next_bd(nd)
        if nb > dl:
            nb = dl
        issues.append(('weekend_or_holiday', T('weekend_or_holiday', named=txt_short(nd), date=txt_short(nb))))
        nd = nb
    fl_ = floor_of(V, pid)
    full = full_of(V, pid)
    if na < fl_ - 0.005:
        if pg(V, pid, 'offered_floor') == 'yes' and g(V, 'mode') != 'hardship':
            V['offer_verdict'] = 'below_floor'
            refuse(V, pid)
            return
        issues.append(('below_floor', T('below_floor', named=fmt(na), floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words'))))
        pset(V, pid, 'offered_floor', 'yes')
        na = fl_
    elif na > full + 0.005:
        issues.append(('above_full', T('above_full', full=fmt(full), named=fmt(na), words=pg(V, pid, 'words'))))
        na = full
    if not issues:
        agree(V, pid, na, nd)
        return
    if P.get('above_full') == 'agree' and [x[0] for x in issues] == ['above_full']:
        pre = issues[0][1]
        if pg(V, pid, 'above_full_said') == okey(na, nd) and T('above_full_again'):
            # the customer repeats the same higher amount at the read-back: explain once more in other words (a customer
            # who heard 'I will record 310.50' kept answering 'No, 320', Brief C v3 EXT-C-09)
            pre = T('above_full_again', full=fmt(full), named=fmt(na if a is None else a), words=pg(V, pid, 'words'))
        pset(V, pid, 'above_full_said', okey(na, nd))
        agree(V, pid, na, nd, prefix=pre)   # the brief: above the full amount, record the full amount and say so
        V['offer_verdict'] = 'above_full'
        return
    V['offer_verdict'] = issues[0][0]
    set_prop(V, pid, na, nd)
    V['offer_text'] = join([x[1] for x in issues] + [V['offer_question']])
    say(V, V['offer_text'])
def offer_target(V):
    f = g(V, 'offer_for')
    ids = pids(V)
    order = P['ordinals']
    if f in order:
        i = order.index(f)
        if i < len(ids):
            return ids[i]
    return ''
def fit_day(V, p, dd):
    # one day named for several products: each product gets it, moved to the next business day or capped at its own
    # deadline (the read-back says so: tag 'bd' / 'dl')
    t = today_of(V)
    tag = ''
    dl = deadline_of(V, p)
    if dd < t:
        dd = t if isbd(t) else next_bd(t)
    if not isbd(dd):
        nb = next_bd(dd)
        if P['closed_day_move'] == 'before':   # the brief's rule for a closed day, as check_one applies it (Kestrel PUB-13)
            pb = prev_bd(dd)
            if pb >= t:
                nb = pb
        dd = nb
        tag = 'bd'
    if dd > dl:
        dd = dl
        tag = 'dl'
    return dd, tag
def moved_note(V, named, moved):
    # why a named day was moved: the read-back's ', the next business day' alone left the customer insisting on the
    # holiday (extended Brief B EXT-B-14)
    out = []
    for n, m in zip(named, moved):
        if n is None or m is None or n == m or n < today_of(V) or isbd(n):
            continue
        s = T('weekend_or_holiday', named=txt_short(n), date=txt_short(m))
        if s and s not in out:
            out.append(s)
    return join(out)
def all_offer(V, d):
    named, moved = [], []
    for p in [x for x in pids(V) if state(V, x) == 'open']:
        dd, tag = fit_day(V, p, d)
        if tag == 'bd':
            named.append(d)
            moved.append(dd)
        agree(V, p, full_of(V, p), dd, tag, move=False)
    V['offer_verdict'] = 'ok'
    advance(V, '')
    spoken_prefix(V, moved_note(V, named[:1], moved[:1]))
WDN = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
MON = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 'july': 7, 'august': 8,
       'september': 9, 'october': 10, 'november': 11, 'december': 12}
NUMW = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
        'nine': 9, 'ten': 10, 'fourteen': 14}
def _month_of(w):
    for k, v in MON.items():
        if w.startswith(k[:3]):
            return v
    return None
ORDW = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9,
        'tenth': 10, 'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14, 'fifteenth': 15, 'sixteenth': 16,
        'seventeenth': 17, 'eighteenth': 18, 'nineteenth': 19, 'twentieth': 20, 'thirtieth': 30}
def _ordinal_words(t):
    for tens, base in (('twenty', 20), ('thirty', 30)):
        for w, n in ORDW.items():
            if n < 10:
                t = t.replace(' %s %s ' % (tens, w), ' %dth ' % (base + n))
    for w in sorted(ORDW, key=len, reverse=True):
        t = t.replace(' %s ' % w, ' %dth ' % ORDW[w])
    return t
CARDW = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
         'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
         'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30}
CARD_RX = r'((?:twenty|thirty)(?: (?:one|two|three|four|five|six|seven|eight|nine))?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)'
MON_RX = r'(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)'
def _card_val(s):
    return sum([CARDW.get(x, 0) for x in s.split()])
def _cardinal_days(t):
    # a day said as a cardinal next to a month ('thirty October', 'October twenty six') -> '30 october'; only beside a
    # month name, so an amount ('twenty') is never read as a day
    t = re.sub(r' (?:the )?' + CARD_RX + r' (?:of )?' + MON_RX + r' ', lambda m: ' %d %s ' % (_card_val(m.group(1)), m.group(2)), t)
    t = re.sub(r' ' + MON_RX + r' (?:the )?' + CARD_RX + r' ', lambda m: ' %s %d ' % (m.group(1), _card_val(m.group(2))), t)
    # a tens word with its unit after a weekday or 'the' ('Friday twenty three', 'the thirty one'): a day of the month
    # (said in pieces, 'Friday twenty' / 'three' joins to this; Freya pieces PUB-04 read it as plain Friday)
    t = re.sub(r' (monday|tuesday|wednesday|thursday|friday|saturday|sunday|the) (twenty|thirty) (one|two|three|four|five|six|seven|eight|nine) ',
               lambda m: ' %s %dth ' % (m.group(1), CARDW[m.group(2)] + CARDW[m.group(3)]), t)
    return t
def cut_off(text):
    # the words stop on a bare tens word ('Monday the twenty', 'thirty...'): a day cut off mid-word
    t = ' ' + re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', str(text or '').lower())).strip() + ' '
    return bool(re.search(r' (twenty|thirty) $', t))
def resolve_when(V, text):
    # (date, kind) from the customer's OWN WORDS, relative to the call's today (never the real clock: the platform's
    # date extraction resolved 'tomorrow' with the real clock). kind: 'exact' (with a date), 'vague', or 'none'.
    t = ' ' + re.sub(r'[^a-z0-9 ]', ' ', str(text or '').lower()) + ' '
    t = _cardinal_days(_ordinal_words(re.sub(r'\s+', ' ', t)))
    if not t.strip():
        return None, 'none'
    today = today_of(V)
    D = datetime.timedelta
    if re.search(r' (twenty|thirty) $', t):
        # the words stop on a bare tens word ('I can pay on the twenty'): a cut-off day, never the 20th or the 30th
        # and never the extractor's guess (Freya talkative PUB-04 recorded the 20th for 'the twenty[-third]')
        return None, 'vague'
    if ' day after tomorrow ' in t:
        return today + D(2), 'exact'
    if ' tomorrow ' in t:
        return today + D(1), 'exact'
    # 'now' counts as today only next to a paying verb: 'too much for me right now' is not an offer for today (Freya PUB-06)
    if re.search(r' (today|tonight|this morning|this afternoon|this evening) ', t) or \
            re.search(r' (pay|paying|settle|clear|transfer|send|do)( it| that| this| them| everything| all of it| the money)? (right )?(now|straight away|immediately) ', t):
        return today, 'exact'
    m = re.search(r' in (\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|fourteen) (day|week|fortnight)s? ', t)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else NUMW.get(m.group(1), 1)
        n = n * (7 if m.group(2) == 'week' else 14 if m.group(2) == 'fortnight' else 1)
        return today + D(n), 'exact'
    m = re.search(r' (\d{1,2})(?:st|nd|rd|th)? (?:of )?([a-z]{3,9})(?: (\d{4}))? ', t)
    mo = _month_of(m.group(2)) if m else None
    if m and mo:
        y = int(m.group(3)) if m.group(3) else today.year
        try:
            d = datetime.date(y, mo, int(m.group(1)))
            if not m.group(3) and d < today - D(14):
                d = datetime.date(y + 1, mo, int(m.group(1)))
            return d, 'exact'
        except Exception:
            return None, 'vague'
    m = re.search(r' ([a-z]{3,9}) (?:the )?(\d{1,2})(?:st|nd|rd|th)? ', t)
    mo = _month_of(m.group(1)) if m else None
    if m and mo:
        try:
            d = datetime.date(today.year, mo, int(m.group(2)))
            if d < today - D(14):
                d = datetime.date(today.year + 1, mo, int(m.group(2)))
            return d, 'exact'
        except Exception:
            return None, 'vague'
    # a day of the month wins over a weekday said with it ('Monday the twenty-sixth' is the 26th, never the next
    # Monday): the read-back then names the date's real weekday, so a mismatch is the customer's to correct
    m = (re.search(r' (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday) (?:the )?(\d{1,2})(?:st|nd|rd|th)? ', t)
         or re.search(r' (?:the )?(\d{1,2})(?:st|nd|rd|th) ', t))
    if m:
        n = int(m.group(1))
        y, mo = today.year, today.month
        if n < today.day:
            mo += 1
            if mo > 12:
                mo, y = 1, y + 1
        try:
            return datetime.date(y, mo, n), 'exact'
        except Exception:
            return None, 'vague'
    # weekdays LAST: 'Monday the 26th' is the 26th (the number wins; PUB-07 looped on 'Monday 19 October' when the weekday matched first)
    m = re.search(r' (?:(this|next|coming|on|by) )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday) ', t)
    if m:
        wd = WDN.index(m.group(2))
        if P.get('weekday_rule') == 'first_after' and m.group(1) in ('this', 'next', 'coming'):
            delta = (wd - today.weekday()) % 7 or 7   # the first such weekday AFTER today, also when said on that weekday
        elif P.get('weekday_rule') == 'first_after_plus7':
            delta = (wd - today.weekday()) % 7 or 7   # bare / 'this X' = the first X after today; 'next X' = seven days later
            if m.group(1) == 'next':
                delta += 7
        elif m.group(1) == 'next':

            if P.get('weekday_rule') == 'first_after':
                delta = (wd - today.weekday()) % 7 or 7
            else:   # that weekday in the following calendar week
                delta = (7 - today.weekday()) + wd
        else:
            delta = (wd - today.weekday()) % 7
        return today + D(delta), 'exact'
    if re.search(r'(next week|week after next|end of (the )?month|end of month|this month|next month|when (my |the )?(salary|pay|wages|money)|'
                 r'after (my |the )?(pay|salary)|a few (days|weeks)|couple of (days|weeks)|soon|later|some ?time|not sure|maybe|'
                 r'next (few|couple)|beginning of|middle of|start of|mid )', t):
        return None, 'vague'
    return None, 'none'
def offer_date_of(V):
    # the customer's words first (offer_when, resolved in code); the extraction's offer_date only as a fallback and
    # never a date before the call's today
    w = g(V, 'offer_when')
    d, kind = resolve_when(V, w)
    prev = g(V, 'when_prev')
    if (kind != 'exact' or cut_off(prev)) and prev and w.strip():
        # a day said in pieces over two turns ('thirty...' / 'October.'; 'Monday the twenty' / 'sixth'): the last
        # turn's unresolved words joined with this turn's (Freya pieces PUB-13 lost 'thirty' and offered the deadline)
        # after a cut-off tens word the join comes first ('twenty' + 'sixth' is the 26th, not the 6th of next month)
        d2, k2 = resolve_when(V, prev + ' ' + w)
        if k2 == 'exact' and d2 is not None:
            d, kind = d2, k2
    if kind != 'exact' and w.strip():
        V['pending_when'] = w
        V['when_cutoff'] = 'yes' if cut_off(w) else ''
    refused_day = g(V, 'day_refused') == 'yes'
    if refused_day and kind == 'exact' and d is not None:
        # the words name the day that was turned down ('I can't do this Friday': the proposal's Friday, or today when
        # said on a Friday), not a day of their own
        said_today = re.search(r'\b(today|tonight|now|this (morning|afternoon|evening))\b', w.lower())
        if d == pdate(g(V, 'prop_date')) or (d == today_of(V) and not said_today):
            d, kind = None, 'none'
    if kind == 'exact' and d is not None:
        return d, 'exact'
    if kind == 'vague':
        return None, 'vague'
    if refused_day:
        # the customer turned a day down and their own words give no other day: an extracted date is that declined
        # day (or the real clock), never their day (extended Brief B EXT-B-14)
        return None, g(V, 'offer_kind')
    d = pdate(g(V, 'offer_date'))
    if d is not None and d < today_of(V):
        return None, 'vague'
    return d, g(V, 'offer_kind')
def ref_amount(V, pid, a):
    # an amount said by reference ('the minimum', 'all of it') resolved against the product's own facts
    if a is not None or not pid:
        return a
    r = g(V, 'offer_ref')
    if r == 'floor':
        return floor_of(V, pid)
    if r == 'full':
        return full_of(V, pid)
    return a
def spoken_prefix(V, pre):
    if not pre:
        return
    key = {'confirm': 'readback_line', 'wrapup': 'wrap_line'}.get(g(V, 'route'), 'say_next')
    V[key] = join([pre, g(V, key)])
def claims(V, words=False):
    # per_product: 'first=dispute;second=paid;third=pay@monday the 26th' (one extraction string, parsed here) ->
    # {pid: claim} or, with words=True, {pid: the customer's words for that product's day ('' when none)}
    out = {}
    ids = pids(V)
    order = P['ordinals']
    for part in g(V, 'per_product').lower().split(';'):
        if '=' not in part:
            continue
        k, v = [x.strip() for x in part.split('=', 1)]
        w = ''
        if '@' in v:
            v, w = [x.strip() for x in v.split('@', 1)]
        if k in order and order.index(k) < len(ids):
            out[ids[order.index(k)]] = w if words else v
    return out
def settle_claims(V):
    # one turn about several products ('the card is not mine, I paid the loan, the car loan today'): the paid and
    # disputed products are settled one by one (the single topic would have settled every open product; extended
    # Brief B EXT-B-02). Returns the brief's sentences for what was settled, '' when nothing was.
    if not multi(V):
        return ''
    cl = claims(V)
    pre = []
    for kind in ('dispute', 'paid'):
        ps = [p for p in pids(V) if cl.get(p) == kind and state(V, p) in ('open', 'agreed')]
        if ps:
            for p in ps:
                pset(V, p, 'state', kind)
            pre.append(T(kind, words=T('and').join([pg(V, p, 'words') for p in ps])))
    return join(pre)
def pay_claimed(V, pre):
    # after settle_claims: the products the same turn says will be paid go through the guard (amount: the one
    # named, by reference, else the full amount; day: the one named, else today). False when there is none.
    cl = claims(V)
    cw = claims(V, words=True)
    opn = [p for p in pids(V) if state(V, p) == 'open']
    pay = [p for p in opn if cl.get(p) == 'pay']
    if not pay:
        return False
    a = num(g(V, 'offer_amount'))
    if a is not None and a <= 0:
        a = None
    d, k = offer_date_of(V)
    t = today_of(V)
    d0 = d or (t if isbd(t) else next_bd(t))
    if len(pay) == 1:
        p = pay[0]
        V['stage'] = 'one'
        V['cur_pid'] = p
        a = ref_amount(V, p, a)
        if cw.get(p):
            d, k = resolve_when(V, cw[p])
            d0 = d or d0
        if k == 'vague':
            check_one(V, p, a, None, 'vague')
        else:
            check_one(V, p, full_of(V, p) if a is None else a, d0, 'exact')
    elif a is None:
        # several products, each with its own day words or the turn's day ('the card and the loan today, the car
        # loan on Monday the 26th'); a vague day for any of them -> not decided here
        days = {}
        named, moved = [], []
        for p in pay:
            dd, kk = resolve_when(V, cw.get(p, '')) if cw.get(p) else (None, 'none')
            if kk == 'vague':
                return False
            days[p] = fit_day(V, p, dd or d0)
            if days[p][1] == 'bd':
                named.append(dd or d0)
                moved.append(days[p][0])
        for p in pay:
            agree(V, p, full_of(V, p), days[p][0], days[p][1], move=False)
        V['offer_verdict'] = 'ok'
        advance(V, '')
        pre = join([pre, moved_note(V, named, moved)])
    else:
        return False
    spoken_prefix(V, pre)
    return True
def claims_first(V):
    # True when the turn's per-product claims decided the turn (settled products, then the paid ones or the next)
    if not (multi(V) and g(V, 'stage') == 'all'):
        return False
    pre = settle_claims(V)
    if pay_claimed(V, pre):
        return True
    if not pre:
        return False
    advance(V, pre)
    return True
def amount_targets(V):
    # the amounts the customer may be saying: floor, full amount and the amount on the table, of the open products
    out = []
    for p in [x for x in pids(V) if state(V, x) == 'open']:
        for x in (floor_of(V, p), full_of(V, p), prop_of(V, p)[0]):
            if x is not None:
                out.append(float(x))
    return out
def cut_cents(V, a):
    # a whole amount that is a target with its cents missing (637 for 637.50)
    if a is None or abs(a - round(a)) >= 0.005 or a < 1:
        return False
    return any(abs(x - round(x)) >= 0.005 and int(x) == int(round(a)) for x in amount_targets(V))
def join_amount(V, a):
    # the cents of last turn's whole amount ('and fifty cents' -> 0.5, 'and fifty' -> 50): joined to it
    ap = num(g(V, 'amount_prev'))
    if ap is None or a is None or a <= 0:
        return a
    if a < 1:
        return round(ap + a, 2)
    if abs(a - round(a)) < 0.005 and a < 100:
        j = round(ap + a / 100.0, 2)
        if any(abs(j - x) < 0.005 for x in amount_targets(V)):
            return j
    return a
def cutoff_turn(V, a, d):
    # a cut-off day ('Monday the twenty') or a day-sized amount with no day ('I accept the twenty' -> 20, below the
    # floor) is asked again, twice at most per call, before any rule uses it (Freya corrects PUB-07 offered the
    # deadline for a cut-off 26th, PUB-04 recorded the floor after 'the twenty' was taken as an amount)
    c = int(num(g(V, 'cutoff_count'), 0) or 0)
    if c >= 2:
        return False
    if g(V, 'when_cutoff') == 'yes' and (a is None or abs(a - 20) < 0.005 or abs(a - 30) < 0.005):
        V['cutoff_count'] = str(c + 1)
        V['offer_verdict'] = 'cutoff'
        say(V, T('cutoff_day'))
        return True
    if a is not None and d is None and cut_cents(V, a):
        # an amount whose cents did not come ('six hundred and thirty-seven' for 637.50): kept for the next turn's
        # cents and asked again, never checked as 637 (Freya pieces PUB-06 counted it below the floor and ended)
        V['pending_amount'] = str(int(round(a)))
        V['cutoff_count'] = str(c + 1)
        V['offer_verdict'] = 'cutoff_amount'
        say(V, join([T('cutoff_amount'), g(V, 'offer_question')]))
        return True
    if a is not None and d is None and abs(a - round(a)) < 0.005 and 1 <= a <= 31:
        ps = [p for p in pids(V) if state(V, p) == 'open']
        cur = g(V, 'cur_pid')
        fl_ = floor_of(V, cur) if cur in ps and not (multi(V) and g(V, 'stage') == 'all') else min([floor_of(V, p) for p in ps] or [0.0])
        if a < fl_ - 0.005 and g(V, 'small_amount_asked') != 'yes':
            V['small_amount_asked'] = 'yes'
            V['cutoff_count'] = str(c + 1)
            V['offer_verdict'] = 'cutoff_amount'
            say(V, join([T('cutoff_amount'), g(V, 'offer_question')]))
            return True
    return False
def ev_offer(V):
    if claims_first(V):
        return
    kind = g(V, 'offer_kind')
    a = num(g(V, 'offer_amount'))
    if a is not None and a <= 0:
        a = None
    a = join_amount(V, a)
    d, k2 = offer_date_of(V)
    if d is not None and k2 == 'exact' and cut_off(g(V, 'when_prev')) and a is not None and abs(a - round(a)) < 0.005 and 1 <= a <= 9:
        a = None   # the unit of a cut-off day ('Friday twenty' / 'three'), not an amount
    if cutoff_turn(V, a, d):
        return
    if d is None and a is None and k2 != 'vague' and kind != 'vague' and g(V, 'day_refused') == 'yes' and \
            g(V, 'stance') == 'refuse' and g(V, 'offer_ref') not in ('floor', 'full'):
        # 'I can't do Friday.' with no amount and no day of their own: the declined day is not an offer, the no is the
        # flat refusal it is (it reached the guard only because the extractor saw a day in it)
        ev_refuse(V)
        return
    if k2 in ('exact', 'vague'):
        kind = k2
    if kind == 'vague':
        d = None
    if not (multi(V) and g(V, 'stage') == 'all'):
        pid = g(V, 'cur_pid')
        a = ref_amount(V, pid, a)
        # 'the full amount is too much, but I can pay <date>': the too-much rule applies to the amount (the floor,
        # offered once, with the brief's sentence) and the named date still goes through the guard
        fl_ = floor_of(V, pid)
        # the floor asked for by name ('I can pay the minimum today'; on Freya the stance came out 'offer') gets the
        # same sentence: the brief's floor line says what happens to the rest
        tm = g(V, 'stance') == 'too_much'
        if (tm and (a is None or abs(a - fl_) < 0.005)) or (g(V, 'offer_ref') == 'floor' and a is not None and abs(a - fl_) < 0.005):
            if tm:
                pset(V, pid, 'too_much', 'yes')
            if g(V, 'mode') != 'hardship' and pg(V, pid, 'offered_floor') != 'yes' and fl_ < full_of(V, pid) - 0.005:
                pset(V, pid, 'offered_floor', 'yes')
                set_prop(V, pid, fl_, prop_of(V, pid)[1])   # a vague day keeps the floor as the amount
                check_one(V, pid, fl_, d, kind)
                spoken_prefix(V, T('too_much_floor', floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words')))
                return
    if multi(V) and g(V, 'stage') != 'all' and g(V, 'offer_for') == 'all' and d is not None and a is None and kind == 'exact':
        all_offer(V, d)
        return
    if multi(V) and g(V, 'stage') == 'all':
        tp = offer_target(V)
        if tp:
            V['stage'] = 'one'
            V['cur_pid'] = tp
            check_one(V, tp, a, d, kind)
            return
        if kind == 'vague' or (d is None and a is None):
            V['offer_verdict'] = 'vague'
            if g(V, 'vague_all') != 'yes':
                V['vague_all'] = 'yes'
                V['vague_pending'] = 'all'
                say(V, T('vague'))
                return
            p = pids(V)[0]
            pset(V, p, 'vague_asked', 'yes')
            V['stage'] = 'one'
            V['cur_pid'] = p
            check_one(V, p, None, None, 'vague')
            return
        if d is not None:
            all_offer(V, d)
            return
        p = pids(V)[0]
        V['stage'] = 'one'
        V['cur_pid'] = p
        check_one(V, p, a, None, 'exact')
        return
    check_one(V, g(V, 'cur_pid'), a, d, kind)
def ev_accept(V):
    if claims_first(V):
        return
    if multi(V) and g(V, 'stage') == 'all':
        t = today_of(V)
        for p in [x for x in pids(V) if state(V, x) == 'open']:
            agree(V, p, full_of(V, p), t if isbd(t) else next_bd(t), '', move=False)
        advance(V, '')
        return
    pid = g(V, 'cur_pid')
    if state(V, pid) == 'agreed':
        pset(V, pid, 'state', 'open')
    a, d = prop_of(V, pid)
    check_one(V, pid, a, d, 'exact')
def to_one_by_one(V):
    opn = [x for x in pids(V) if state(V, x) == 'open']
    p = opn[0] if opn else pids(V)[0]
    V['stage'] = 'one'
    V['cur_pid'] = p
    return p, join([T('one_by_one'), T('next_product', words=pg(V, p, 'words'), past_due=fmt(full_of(V, p)))])
def ev_refuse(V):
    # the answer to 'which exact day?' still gives no day, and the extractor called it a refusal ('I'm not sure, it
    # varies'): the brief's second-ask rule applies (propose the deadline), not a persuasion attempt (generated Brief B
    # GEN-P-06). A brief where no exact day after one ask is a non-answer keeps the refusal (vague_again='refuse').
    vp = g(V, 'vague_prev')
    if vp and P.get('vague_again') != 'refuse':
        if vp == 'all' and multi(V) and g(V, 'stage') == 'all':
            p = pids(V)[0]
            pset(V, p, 'vague_asked', 'yes')
            V['stage'] = 'one'
            V['cur_pid'] = p
            check_one(V, p, None, None, 'vague')
            return
        if vp == g(V, 'cur_pid') and state(V, vp) == 'open':
            check_one(V, vp, None, None, 'vague')
            return
    if multi(V) and g(V, 'stage') == 'all':
        pre0 = settle_claims(V)
        if pre0 and not [x for x in pids(V) if state(V, x) == 'open']:
            advance(V, pre0)
            return
        p, pre = to_one_by_one(V)
        refuse(V, p, join([pre0, pre]))
        return
    pid = g(V, 'cur_pid')
    if state(V, pid) == 'agreed':
        pset(V, pid, 'state', 'open')
    refuse(V, pid)
def ev_too_much(V):
    if multi(V) and g(V, 'stage') == 'all':
        pre0 = settle_claims(V)
        if pre0 and not [x for x in pids(V) if state(V, x) == 'open']:
            advance(V, pre0)
            return
        p, pre = to_one_by_one(V)
        too_much(V, p, join([pre0, pre]))
        return
    too_much(V, g(V, 'cur_pid'))
def live(V, p):
    return bool(p) and state(V, p) in ('open', 'agreed')
def targets_for_topic(V, kind=''):
    # a topic (paid / dispute) settles only products still open or agreed. The ordinal is the extractor's guess at a
    # position: one naming a product already settled while another one is on the table is not trusted (extended Brief B
    # EXT-B-12, talkative: a dispute of the product being asked about came back with the ordinal of a product already
    # settled; that one was settled again and the product on the table restarted, ~130 times). The same claim again on
    # that product is a repeat (nothing to settle); another claim is about the product on the table. With nothing on the
    # table the old rule stands: a different claim on a settled product is the customer changing it ('I don't recognise
    # it' ... 'sorry, I mean I already paid it'). kind '' (the hardship words, keep_said) keeps the old rule throughout.
    tp = offer_target(V)
    cur = g(V, 'cur_pid')
    if tp and (live(V, tp) or not kind):
        return [tp]
    if multi(V) and g(V, 'stage') == 'all':
        return [p for p in pids(V) if live(V, p)]
    if tp and state(V, tp) == kind:
        return []
    if tp and live(V, cur):
        return [cur]
    return [tp or cur]
def ev_settle(V, kind):
    if multi(V):
        pre = settle_claims(V)
        if pre:
            if not pay_claimed(V, pre):
                advance(V, pre)
            return
    ts = targets_for_topic(V, kind)
    if not ts:
        # a repeat of a claim already settled changes nothing: the call goes on where it was (the offer on the table,
        # unchanged: start_product never restarts it; the read-back; the notes). The same repeat in the very next turn
        # is about the product on the table (an ordinal that keeps naming the settled product is the extractor's, not
        # the customer's: no fixed point)
        key = kind + '@' + offer_target(V)
        cur = g(V, 'cur_pid')
        if g(V, 'claim_prev') == key and live(V, cur):
            ts = [cur]
        else:
            V['claim_repeat'] = key
            advance(V, '')
            return
    words = [pg(V, p, 'words') for p in ts]
    for p in ts:
        pset(V, p, 'state', kind)
    pre = T(kind, words=T('and').join(words)) if multi(V) else ''
    advance(V, pre)
def ev_human(V):
    c = int(num(g(V, 'human_count'), 0) or 0) + 1
    V['human_count'] = str(c)
    if c >= int(P['human_limit']):
        V['route'] = 'xfer_general'
        return
    say(V, T('human_first'))
def ev_notalk(V):
    c = int(num(g(V, 'notalk_count'), 0) or 0) + 1
    V['notalk_count'] = str(c)
    if c >= int(P['notalk_limit']):
        for p in pids(V):
            if state(V, p) in ('open', 'agreed'):
                pset(V, p, 'state', 'refused')
        advance(V, '')
        return
    say(V, join([T('notalk_first'), g(V, 'offer_question')]))
def ev_hardship(V):
    V['mode'] = 'hardship'
    hd, hk = offer_date_of(V)
    if g(V, 'offer_kind') == 'exact' or hk == 'exact' or g(V, 'offer_ref') in ('floor', 'full'):
        V['hs_offer'] = 'yes'
        V['hs_date'] = hd.isoformat() if hd is not None else ''
        ra = ref_amount(V, g(V, 'cur_pid'), num(g(V, 'offer_amount')) if (num(g(V, 'offer_amount')) or 0) > 0 else None)
        V['hs_amount'] = str(ra) if ra is not None else ''
    say(V, T('hardship'), 'hardship')
def ev_hs_decline(V):
    if g(V, 'hs_offer') == 'yes':
        V['hs_offer'] = 'no'
        V['offer_kind'] = 'exact'
        V['offer_date'] = g(V, 'hs_date')
        V['offer_amount'] = g(V, 'hs_amount')
        ev_offer(V)
        return
    for p in pids(V):
        if state(V, p) == 'open':
            pset(V, p, 'state', 'hardship')
    advance(V, '')
def ev_hs_offer(V):
    ev_offer(V)
def ev_confirm_no(V):
    V['same_change'] = '0'
    agreed = [p for p in pids(V) if state(V, p) == 'agreed']
    pid = g(V, 'cur_pid') if g(V, 'cur_pid') in agreed else (agreed[-1] if agreed else g(V, 'cur_pid'))
    if recorded_guard(V, pid):
        return
    V['cur_pid'] = pid
    V['stage'] = 'one'
    parts = pg(V, pid, 'agreed').split('|')
    a = num(parts[0]) if parts else None
    d = pdate(parts[1]) if len(parts) > 1 else None
    if a is not None and d is not None:
        set_prop(V, pid, a, d)
    pset(V, pid, 'state', 'open')
    refuse(V, pid)
def change_claims(V):
    # a change at the read-back that names each product's own day ('the card today and the loan on Monday the 26th')
    if not multi(V):
        return False
    cl = claims(V)
    cw = claims(V, words=True)
    ag = [p for p in pids(V) if state(V, p) == 'agreed' and cl.get(p) == 'pay' and cw.get(p)]
    if not ag:
        return False
    days = {}
    named, moved = [], []
    for p in ag:
        dd, kk = resolve_when(V, cw[p])
        if dd is None:
            return False
        days[p] = fit_day(V, p, dd)
        if days[p][1] == 'bd':
            named.append(dd)
            moved.append(days[p][0])
    for p in ag:
        parts = pg(V, p, 'agreed').split('|')
        a = num(parts[0]) if parts else None
        agree(V, p, full_of(V, p) if a is None else a, days[p][0], days[p][1], move=False)
    V['same_change'] = '0'
    V['offer_verdict'] = 'ok'
    advance(V, '')
    spoken_prefix(V, moved_note(V, named, moved))   # say why a day was moved (the read-back tag alone did not)
    return True
def recorded_guard(V, pid):
    # one promise per product: a recorded promise is never reopened or recorded again (the brief's change sentence)
    if pid and state(V, pid) == 'recorded':
        V['wrap_line'] = join([T('wrap_change'), T('anything_else')])
        V['route'] = 'wrapup'
        return True
    return False
def ev_change(V):
    if change_claims(V):
        return
    agreed = [p for p in pids(V) if state(V, p) == 'agreed']
    a = num(g(V, 'offer_amount'))
    if a is not None and a <= 0:
        a = None
    d, k2 = offer_date_of(V)
    tp = offer_target(V)
    if not tp and multi(V) and len(agreed) > 1 and d is not None and a is None:
        # the same date for everyone again is not a change either (Brief B PUB-12 looped 150 turns on 'the credit
        # card tomorrow, not the others' when the all-products read-back came back unchanged): once more, then a no
        same_all = all((pg(V, p, 'agreed').split('|') + [''])[1] == d.isoformat() for p in agreed)
        if same_all:
            n = int(num(g(V, 'same_change'), 0) or 0) + 1
            V['same_change'] = str(n)
            if n >= 2:
                V['same_change'] = '0'
                ev_confirm_no(V)
                return
        else:
            V['same_change'] = '0'
        for p in agreed:
            pset(V, p, 'state', 'open')
        all_offer(V, d)
        return
    pid = tp or (g(V, 'cur_pid') if g(V, 'cur_pid') in agreed else (agreed[-1] if agreed else g(V, 'cur_pid')))
    if recorded_guard(V, pid):
        return
    parts = pg(V, pid, 'agreed').split('|')
    pa = num(parts[0]) if parts else None
    pd = pdate(parts[1]) if len(parts) > 1 else None
    a = ref_amount(V, pid, a)
    # a 'change' that names nothing new (no value, or the values just read back) is not a change: reading the same
    # line back again looped 28 times on extended Brief A EXT-A-36. The second such answer in a row is a no to the
    # read-back offer (the ladder decides what comes next).
    same = (a is None or (pa is not None and abs(a - pa) < 0.005)) and (d is None or d == pd)
    if same:
        n = int(num(g(V, 'same_change'), 0) or 0) + 1
        V['same_change'] = str(n)
        if n >= 2:
            V['same_change'] = '0'
            ev_confirm_no(V)
            return
        if pa is not None and pd is not None:
            a, d = pa, pd    # read the same values back once more (never the vague-day question for a bare 'no, change')
    else:
        V['same_change'] = '0'
    if pa is not None and pd is not None:
        set_prop(V, pid, pa, pd)
    pset(V, pid, 'state', 'open')
    V['cur_pid'] = pid
    V['stage'] = 'one'
    # no reset of checks_<pid>: a customer who repeats the same correction at the read-back (an amount above the full
    # amount, read back as the full amount) looped confirm -> change_offer -> confirm ten times (Brief C v3 EXT-C-09);
    # max_checks is the loop exit for changes too
    check_one(V, pid, a, d, 'exact')
def rec_next(V):
    for p in pids(V):
        if state(V, p) == 'agreed':
            parts = pg(V, p, 'agreed').split('|')
            V['rec_pid'] = p
            V['rec_amount'] = str(num(parts[0], 0.0))
            V['rec_date'] = parts[1] if len(parts) > 1 else ''
            V['rec_ok'] = 'pending'
            V['route'] = 'record'
            return
    if P.get('defer_notes') and g(V, 'wrap_done') != 'yes' and [p for p in pids(V) if state(V, p) == 'recorded']:
        # notes wait until the wrap-up has decided the ending: a transfer from the wrap-up adds no notes at all
        enter_wrapup(V)
        return
    note_next(V)
def ev_confirm_yes(V):
    V['same_change'] = '0'
    rec_next(V)
def ev_rec_after(V):
    p = g(V, 'rec_pid')
    ok = g(V, 'rec_ok').lower() == 'true'
    if p:
        if ok:
            pset(V, p, 'state', 'recorded')
            rl = [x for x in g(V, 'recorded_pids').split(',') if x]
            if p not in rl:
                rl.append(p)
            V['recorded_pids'] = ','.join(rl)
        else:
            f = int(num(pg(V, p, 'fails'), 0) or 0) + 1
            pset(V, p, 'fails', f)
            if f < int(P['fail_max']):
                V['rec_ok'] = 'pending'
                V['route'] = 'record'
                return
            pset(V, p, 'state', 'service_error')
    rec_next(V)
def note_text(V, p, st):
    # the note's free text (when the API's note tool has one): what a reviewer needs per reason
    try:
        w = pg(V, p, 'words')
        said = str(pg(V, p, 'said_' + st) or '').strip()   # this product's own words only
        if said.lower() in ('none', 'null'):
            said = ''
        if st == 'refused':
            a, d = prop_of(V, p)
            n = int(num(pg(V, p, 'attempts_used'), 0) or 0)
            return ('%s: turned down. Attempts made: %d. Last offer: %s on %s.' % (w, max(n, 1), fmt(a), d.isoformat() if d else '')
                    + ((' Customer said: ' + said) if said else ''))
        if st == 'service_error':
            n = int(num(pg(V, p, 'fails'), 0) or 0)
            return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2))
        lab = {'paid': 'says already paid', 'dispute': 'disputes', 'hardship': 'hardship'}.get(st, st)
        return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)')
    except Exception:
        return str(st)
def note_next(V):
    if P['notes']:
        for p in pids(V):
            st = state(V, p)
            if st in P['note_reasons'] and pg(V, p, 'noted') == 'no':
                V['note_pid'] = p
                V['note_reason'] = P['note_reasons'][st]
                V['note_text'] = note_text(V, p, st)
                V['note_ok'] = 'pending'
                V['route'] = 'note'
                return
    if [p for p in pids(V) if state(V, p) == 'recorded'] and g(V, 'wrap_done') != 'yes':
        enter_wrapup(V)
        return
    finalize(V)
def ev_note_after(V):
    p = g(V, 'note_pid')
    if p:
        if g(V, 'note_ok').lower() == 'true':
            pset(V, p, 'noted', 'yes')
        else:
            f = int(num(pg(V, p, 'note_fails'), 0) or 0) + 1
            pset(V, p, 'note_fails', f)
            if f >= int(P['fail_max']):
                pset(V, p, 'noted', 'failed')
            else:
                V['note_ok'] = 'pending'
                V['route'] = 'note'
                return
    note_next(V)
def enter_wrapup(V):
    rec = [p for p in pids(V) if state(V, p) == 'recorded']
    bad = [p for p in pids(V) if state(V, p) == 'service_error']
    if multi(V) and (len(rec) > 1 or bad):
        line = T('recorded_many', list=T('and').join([pg(V, p, 'words') for p in rec]))
    else:
        line = T('recorded')
    parts = [line] + [T('rec_failed', words=pg(V, p, 'words')) for p in bad]
    if P['after_recorded']:
        parts.append(T('after_recorded'))
    parts.append(T('anything_else'))
    V['wrap_line'] = join(parts)
    V[P['outcome_var']] = P['promise_outcome']
    V['promise_reason'] = promise_reason(V)
    V[P['reason_var']] = V['promise_reason']
    V['route'] = 'wrapup'
def promise_reason(V):
    # the closing reason of a promise when the brief has one: 'full' when every recorded amount equals its full
    # amount, else 'partial' (P['promise_reasons'] maps both to the API's values); '' when the brief has none
    pr = P.get('promise_reasons') or {}
    if not pr:
        return ''
    rec = [p for p in pids(V) if state(V, p) == 'recorded']
    full = True
    for p in rec:
        a = num(pg(V, p, 'agreed').split('|')[0], 0.0) or 0.0
        if abs(a - full_of(V, p)) >= 0.005:
            full = False
    return str(pr.get('full' if full else 'partial') or '')
def finalize(V):
    ids = pids(V)
    sts = [state(V, p) for p in ids]
    fk = P['fin_keys']
    if 'recorded' in sts:
        key = fk['promise']
    elif sts and all(s == 'paid' for s in sts):
        key = fk['paid']
    else:
        key = fk['default']
        for s in sts:
            if s != 'paid':
                key = fk.get(s) or fk['default']
                break
    V['final_route'] = key
    V['route'] = 'fin'
def ev_wrap_human(V):
    c = int(num(g(V, 'wrap_human'), 0) or 0) + 1
    V['wrap_human'] = str(c)
    if c >= int(P['human_limit']):
        V['route'] = 'xfer_general'
        return
    V['wrap_line'] = T('human_first')
    V['route'] = 'wrapup'
def ev_wrap_change(V):
    c = int(num(g(V, 'wrap_count'), 0) or 0) + 1
    V['wrap_count'] = str(c)
    if c > int(P['wrap_turns']):
        ev_finalize(V)
        return
    V['wrap_line'] = join([T('wrap_change'), T('anything_else')])
    V['route'] = 'wrapup'
def ev_finalize(V):
    # the wrap-up is over without a transfer: the notes still owed are written now, then the ending
    V['wrap_done'] = 'yes'
    note_next(V)
def attempt_spoken(V, pid):
    # the current proposal is a counted persuasion attempt (a rung of the ladder, spoken by the system line on entering):
    # a dialogue turn that asks it again is another attempt (extended Brief B EXT-B-01, talkative: a 'No.' after small
    # talk was not extracted, the model re-asked attempt 1 word for word and the judge counted three attempts on a
    # two-attempt product)
    try:
        k = int(num(pg(V, pid, 'attempts_used'), 0) or 0)
        if k < 1 or k > len(ladder(V, pid)):
            return False
        a, d = rung(V, pid, k - 1)
        pa, pd = num(g(V, 'prop_amount')), pdate(g(V, 'prop_date'))
        return pa is not None and pd is not None and okey(a, d) == okey(pa, pd)
    except Exception:
        return False
def state_line(V):
    ids = pids(V)
    out = []
    cur = g(V, 'cur_pid')
    for i, p in enumerate(ids):
        st = state(V, p)
        L = ladder(V, p)
        head = ('Product ' + str(i + 1) + ' of ' + str(len(ids)) + ': ') if len(ids) > 1 else 'Product: '
        s = head + pg(V, p, 'words') + ' (id ' + p + '). Past due ' + fmt(full_of(V, p)) + ', lowest amount ' + fmt(floor_of(V, p)) + ', latest date ' + txt_short(deadline_of(V, p)) + '.'
        if st == 'open':
            rl = refused_list(V, p)
            if rl:
                s += ' Offers already refused: ' + ', '.join([x.replace('@', ' on ') for x in rl]) + ': never offer them again.'
            s += ' Persuasion attempts used: ' + pg(V, p, 'attempts_used', '0') + ' of ' + str(len(L)) + '.'
            if pg(V, p, 'offered_floor') == 'yes':
                s += ' The lowest amount was already offered once: do not offer it again yourself.'
        elif st == 'agreed':
            s += ' Agreed, not recorded yet: ' + pg(V, p, 'agreed').split('|')[0] + ' on ' + (pg(V, p, 'agreed').split('|') + ['', ''])[1] + '.'
        else:
            s += ' Settled: ' + st + '.'
        out.append(s)
    if g(V, 'mode') == 'hardship':
        out.append('The customer mentioned a hardship: make no persuasion attempt and propose nothing yourself. '
                   'The sympathy and the offer of help were already said once: never say them again.')
    elif g(V, 'offer_question'):
        cp = g(V, 'prop_pid')
        floor_said = pg(V, cp, 'offered_floor') == 'yes' and abs(num(g(V, 'prop_amount'), -1.0) - floor_of(V, cp)) < 0.005
        if cp and state(V, cp) == 'open' and (floor_said or attempt_spoken(V, cp)):
            # the floor is offered once (the brief's rule) and every ladder rung is one persuasion attempt: a dialogue
            # turn that re-asks it is another offer (Freya talkative PUB-06: 'How much can you let me pay?' got the
            # minimum again and the judge counted two; EXT-B-01: attempt 1 asked twice). A missed answer is asked for
            # again, never the offer: the repeated 'No.' then routes to the counter and the next offer is the real one.
            out.append('Current offer, already said once: "' + g(V, 'offer_question') + '" Never repeat its amount, its date or '
                       'the question yourself: a repeat counts as another persuasion attempt. If the customer asks what the amount '
                       'or the date was, give it once as the answer, without the question. To small talk or a side question, reply '
                       'in one short sentence and ask only whether they can do that. If their latest message already answered it '
                       '(a no, a yes, a day or an amount, also after small talk), say only: "Sorry, I did not catch that. Could you '
                       'say it again?"')
        else:
            out.append('Current offer, ask exactly this: "' + g(V, 'offer_question') + '"')
    rec = [p for p in ids if state(V, p) == 'recorded']
    out.append('Recorded: ' + (', '.join(rec) if rec else 'nothing yet') + '.')
    V['state_line'] = ' '.join(out)
def _clear_enums(V):
    for k, v in P['clear_enums'].items():
        V[k] = v
def _clear_values(V):
    for k, v in P['clear_values'].items():
        V[k] = v
def finish_turn(V):
    # an aside (a side question in the customer's turn: robot? scam?) is answered first, in the line the route speaks;
    # a turn that goes through code into a tts line never reaches the dialogue model, so the answer must be built here
    a = str(V.get('aside') or 'none')
    asides = P.get('asides') or {}
    if a != 'none' and a in asides:
        txt = str(asides[a].get('say') or '')
        key = {'confirm': 'readback_line', 'wrapup': 'wrap_line'}.get(str(V.get('route') or ''), 'say_next')
        line = str(V.get(key) or '')
        if txt and not line.startswith(txt):
            V[key] = (txt + ' ' + line).strip()
    _clear_enums(V)
    _clear_values(V)
    state_line(V)
def keep_said(V, ev):
    # the customer's words for a reason (customer_said, extracted on the turn) survive later turns that extract nothing:
    # one sticky copy per note kind, read by note_text
    s = str(g(V, 'customer_said') or '').strip()
    if s.lower() in ('', 'none', 'null'):
        return
    V['said_last'] = s
    kind = {'hardship': 'hardship', 'hs_decline': 'hardship', 'paid': 'paid', 'dispute': 'dispute', 'refuse': 'refused'}.get(ev)
    if not kind:
        return
    # per product: only the products this event is about get the words (another product's reason never reaches their
    # note); the first reason stays ('lost my job') and a later, different one is added ('no money')
    if kind == 'refused':
        ps = [g(V, 'cur_pid')]
    elif kind in ('paid', 'dispute') and multi(V) and [p for p, c in claims(V).items() if c == kind]:
        ps = [p for p, c in claims(V).items() if c == kind]
    else:
        ps = targets_for_topic(V, kind if kind in ('paid', 'dispute') else '')   # the products ev_settle will settle
        if not ps and kind in ('paid', 'dispute'):
            # a repeat of a settled claim (ev_settle, run after this with claim_prev = this claim_repeat): the second in a
            # row is about the product on the table; otherwise its new words still reach the settled product's note
            tp, cur = offer_target(V), g(V, 'cur_pid')
            if g(V, 'claim_repeat') == kind + '@' + tp and live(V, cur):
                ps = [cur]
            elif tp and state(V, tp) == kind:
                ps = [tp]
    for p in [x for x in ps if x]:
        old = str(pg(V, p, 'said_' + kind) or '').strip()
        if not old or old.lower() in ('none', 'null'):
            pset(V, p, 'said_' + kind, s)
        elif s.lower() not in old.lower():
            pset(V, p, 'said_' + kind, (old + '; ' + s)[:240])
def main(V, ev):
    try:
        keep_said(V, ev)
        V['policy_event'] = ev
        V['offer_verdict'] = ''
        V['when_prev'] = g(V, 'pending_when')   # unresolved day words of the last policy turn, joined once
        V['vague_prev'] = g(V, 'vague_pending')  # the last spoken line asked for the exact day (ev_refuse)
        V['vague_pending'] = ''
        V['pending_when'] = ''
        V['when_cutoff'] = ''
        V['amount_prev'] = g(V, 'pending_amount')   # a whole amount whose cents were cut off last turn, joined once
        V['pending_amount'] = ''
        V['claim_prev'] = g(V, 'claim_repeat')      # last turn's claim that repeated one already settled (ev_settle)
        V['claim_repeat'] = ''
        if ev == 'offer':
            ev_offer(V)
        elif ev == 'accept':
            ev_accept(V)
        elif ev == 'refuse':
            ev_refuse(V)
        elif ev == 'too_much':
            ev_too_much(V)
        elif ev in ('paid', 'dispute'):
            ev_settle(V, ev)
        elif ev == 'human':
            ev_human(V)
        elif ev == 'notalk':
            ev_notalk(V)
        elif ev == 'hardship':
            ev_hardship(V)
        elif ev == 'hs_decline':
            ev_hs_decline(V)
        elif ev == 'confirm_no':
            ev_confirm_no(V)
        elif ev == 'change':
            ev_change(V)
        elif ev == 'confirm_yes':
            ev_confirm_yes(V)
        elif ev == 'rec_after':
            ev_rec_after(V)
        elif ev == 'note_after':
            ev_note_after(V)
        elif ev == 'wrap_human':
            ev_wrap_human(V)
        elif ev == 'wrap_change':
            ev_wrap_change(V)
        elif ev == 'finalize':
            ev_finalize(V)
        V['policy_state'] = 'ok'
    except Exception as e:
        V['policy_state'] = 'error ' + ev + ': ' + str(e)
        if not g(V, 'route'):
            V['route'] = 'negotiate'
    try:
        finish_turn(V)
    except Exception as e:
        V['policy_state'] = 'error state_line: ' + str(e)
        V.setdefault('state_line', '')
'''

# Every variable the core writes (besides the per-product <name>_<pid> ones). Declared with vars.setdefault at the
# end of every policy node so that static checks (builder/lint.py) see who sets them; setdefault never overwrites.
WRITTEN = ("say_next", "state_line", "offer_question", "offer_text", "offer_verdict", "next_offer_text", "route",
           "final_route", "readback_line", "wrap_line", "prop_pid", "prop_amount", "prop_date", "ok_pid", "ok_amount",
           "ok_date", "rec_pid", "rec_amount", "rec_date", "rec_ok", "note_pid", "note_reason", "note_ok", "note_text",
           "said_last",
           "recorded_pids", "pids_csv", "cur_pid", "stage", "mode", "human_count", "notalk_count", "wrap_count",
           "wrap_human", "vague_all", "vague_pending", "vague_prev", "hs_offer", "hs_date", "hs_amount", "policy_state", "policy_event", "same_change", "wrap_done",
           "promise_reason", "pending_when", "when_prev", "when_cutoff", "cutoff_count", "small_amount_asked", "pending_amount", "amount_prev",
           "claim_repeat", "claim_prev")


def _declare():
    return "".join("vars.setdefault(%r, '')\n" % k for k in WRITTEN)


# Route values the core writes, and the default node each leads to.
ROUTES = ("negotiate", "hardship", "confirm", "record", "note", "wrapup", "xfer_general", "xfer_restructuring",
          "xfer_support")
DEFAULT_TARGETS = {"negotiate": "negotiate", "hardship": "hardship", "confirm": "confirm",
                   "record": "record_promise", "note": "record_note", "wrapup": "wrapup",
                   "xfer_general": "xfer_general", "xfer_restructuring": "xfer_restructuring",
                   "xfer_support": "xfer_support"}

# Policy nodes (name -> event); each runs CAL_HELPERS + core + main(vars, event).
EVENT_NODES = {
    "check_offer": "offer", "accept_offer": "accept", "count_refusal": "refuse", "too_much": "too_much",
    "pol_paid": "paid", "pol_dispute": "dispute", "pol_human": "human", "pol_notalk": "notalk",
    "pol_hardship": "hardship", "hs_decline": "hs_decline", "confirm_no": "confirm_no", "change_offer": "change",
    "rec_next": "confirm_yes", "rec_after": "rec_after", "note_after": "note_after",
    "wrap_human": "wrap_human", "wrap_change": "wrap_change", "finalize": "finalize",
}

ONCE_RULE = ("\n- Every persuasion offer (each attempt of the ladder, the lowest amount), the support team and a transfer are said "
             "once, by the system line you speak on entering: never repeat them yourself. To small talk, a cut-off line or a side "
             "question, reply in one short sentence (or 'Please go on.') and wait; the system asks again when it is due.")
# A generator line telling the model to ask the offer again after small talk or a question (every reference generator
# had 'then ask the current offer again') contradicts the 'already said once' state line: the model obeyed it and asked
# a refused attempt again word for word (extended Brief B EXT-B-01). negotiate_node / hardship_node rewrite it.
REASK_RX = re.compile(r"\b(?:then )?(?:ask|repeat|make|say) (?:the |that )?(?:current )?offer(?: (?:in|from) STATE)? again\b", re.I)
REASK_SUB = "then follow STATE for what to ask: an offer STATE marks already said once is never asked again"
# offer_for / per_product name products by position; 'in the order the agent listed them' was read off the agent's latest
# line, which after a settled product names only the product on the table (extended Brief B EXT-B-12: a dispute of the
# third product came back 'first' and settled the first product again)
POSITION_CLAUSE = (" Positions count in the order the agent's statement first listed every product (the bank's order, as in "
                   "STATE), never in the order of the agent's latest line: a line that names only one product does not make it "
                   "the first.")


def no_reask(task):
    """The task text with every 'then ask the current offer again' (and close variants) replaced by REASK_SUB."""
    return REASK_RX.sub(REASK_SUB, str(task or ""))


class Policy:
    """The negotiation, confirmation and recording part of a call, as code. One instance per generator.

    holidays, business_weekdays: the brief's calendar (CAL_HELPERS).
    texts: {key: template} overriding DEFAULT_TEXTS (see there; '[x]' or '{x}' placeholders).
    multi: the brief allows more than one product (stage 'all' first: one question for every product).
    notes: the brief records a note per product without a promise; note_reasons {state: API reason}.
    fin_keys: {'promise', 'paid', 'default', and per final state 'refused'/'hardship'/'dispute'/'service_error'}
        -> the generator's fin_<key> names (freyalib.end_pair keys).
    fail_max: tries in total of a write before it counts as failed (the brief's retry rule: 'try once more' = 2).
    max_checks: offer-guard loop exit per product (then the product is refused).
    human_limit / notalk_limit: on which request a human transfer / a 'does not want to talk' close happens.
    wrap_turns: how many change requests the wrap-up node answers before it closes.
    closed_day_move: 'after' (offer the next business day) or 'before'.
    ordinals: offer_for enum values naming products in get_account order.
    targets: route -> node name overrides (DEFAULT_TARGETS).
    notes_on_transfer: False when the brief adds no notes on a call that ends in a transfer: the notes are then written
        only once the wrap-up after a recorded promise has ended without one (a transfer from the wrap-up, e.g. a
        restructuring request after the promise, adds none). True (default): notes right after the promises.
    weekday_rule: the brief's reading of the weekday words: 'this_week' ('this X' = X of the current calendar week, 'next X' =
        X of the following week), 'first_after' ('this X' and 'next X' both = the first X after today) or 'first_after_plus7'
        (a bare 'X' or 'this X' = the first X after today, also when said on that weekday; 'next X' = that day + 7 days).
    vague_again: a second vague answer after the one ask for the exact day: 'deadline' (propose the deadline) or
        'refuse' (the brief counts it as a non-answer: one persuasion attempt).
    above_full: an amount above the full amount: 'ask' (propose the full amount and ask again) or 'agree' (the brief
        says record the full amount and say so: straight to the read-back with the brief's sentence first).
    promise_reasons: {'full': <reason>, 'partial': <reason>} when the brief's promise ending has a reason that depends
        on whether every recorded amount equals the full amount; written to reason_var and 'promise_reason' when the
        promise is recorded (so a hang-up in the wrap-up closes right). Use ending_code() for the fin nodes."""


    def __init__(self, holidays, texts=None, multi=False, notes=False, note_reasons=None, fin_keys=None,
                 fail_max=2, max_checks=8, human_limit=2, notalk_limit=2, wrap_turns=2, closed_day_move="after",
                 business_weekdays=fl.BUSINESS_WEEKDAYS, ordinals=("first", "second", "third"), targets=None,
                 outcome_var="outcome", reason_var="reason", promise_outcome="promise", now_var="now", asides=None,
                 weekday_rule="this_week", notes_on_transfer=True, vague_again="deadline", above_full="ask", promise_reasons=None):
        missing = [k for k in REQUIRED_TEXTS + (REQUIRED_TEXTS_MULTI if multi else ()) if k not in (texts or {})]
        if missing and not (texts or {}).get("_allow_defaults"):
            raise ValueError("Policy texts must come from the brief; missing: %s (pass texts={'_allow_defaults': True} only in tests)" % ", ".join(missing))
        t = dict(DEFAULT_TEXTS)
        for k, v in (texts or {}).items():
            t[k] = v
        t = {k: _tpl(v) for k, v in t.items()}
        t.setdefault("after_recorded", "")
        fk = {"promise": "promise", "paid": "paid", "default": "refused", "refused": "refused",
              "hardship": "hardship", "dispute": "dispute", "service_error": "service_error"}
        fk.update(fin_keys or {})
        for k, v in fk.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(v)):
                raise ValueError("fin key %r=%r must be an identifier" % (k, v))
        nr = dict(note_reasons or {})
        bad = set(nr) - set(STATES)
        if bad:
            raise ValueError("note_reasons keys must be states %s, got %s" % (STATES, sorted(bad)))
        if notes and not nr:
            raise ValueError("notes=True needs note_reasons {state: reason}")
        if closed_day_move not in ("after", "before"):
            raise ValueError("closed_day_move must be 'after' or 'before'")
        if vague_again not in ("deadline", "refuse"):
            raise ValueError("vague_again must be 'deadline' or 'refuse'")
        if above_full not in ("ask", "agree"):
            raise ValueError("above_full must be 'ask' or 'agree'")
        pr = dict(promise_reasons or {})
        if pr and set(pr) != {"full", "partial"}:
            raise ValueError("promise_reasons must map exactly 'full' and 'partial' to the API's reasons")
        self.holidays = list(holidays or [])
        self.bwd = list(business_weekdays)
        self.multi = bool(multi)
        self.notes = bool(notes)
        self.fin_keys = fk
        self.targets = dict(DEFAULT_TARGETS)
        self.targets.update(targets or {})
        self.asides = {str(k): {"when": str(v.get("when") or ""), "say": str(v.get("say") or "")} for k, v in (asides or {}).items()}
        self.P = {"texts": t, "multi": self.multi, "notes": self.notes, "note_reasons": nr, "fin_keys": fk, "asides": self.asides, "weekday_rule": str(weekday_rule),
                  "fail_max": int(fail_max), "defer_notes": bool(notes) and not notes_on_transfer, "max_checks": int(max_checks), "human_limit": int(human_limit),
                  "notalk_limit": int(notalk_limit), "wrap_turns": int(wrap_turns),
                  "closed_day_move": closed_day_move, "ordinals": list(ordinals),
                  "clear_enums": dict(CLEAR_ENUMS), "clear_values": dict(CLEAR_VALUES),
                  "outcome_var": outcome_var, "reason_var": reason_var, "promise_outcome": promise_outcome,
                  "now_var": now_var, "after_recorded": bool(t.get("after_recorded")),
                  "vague_again": vague_again, "above_full": above_full, "promise_reasons": pr}

    # ------------------------------------------------------------------ sources
    def core(self):
        """CAL_HELPERS + the policy core (functions only, nothing runs)."""
        src = fl.CAL_HELPERS(self.holidays, self.bwd, self.P.get("weekday_rule", "this_week")) + _CORE.replace("__P__", _pylit(self.P))
        if "{{" in src or "}}" in src:
            raise ValueError("policy core contains '{{' or '}}'")
        return src

    def event_code(self, event):
        """The source of a policy code node: core + main(vars, event), the whole body inside one try (a failing
        core still leaves a route and a state_line), every variable the core writes declared with setdefault."""
        body = self.core() + "\nmain(vars, %r)\n" % event + _declare()
        return ("try:\n%s\nexcept Exception as e:\n    vars['policy_state'] = 'error ' + str(e)\n"
                "    vars.setdefault('route', 'negotiate')\n    vars.setdefault('state_line', '')\n" % fl._indent(body, 4))

    def prepare_code(self, body, statement_expr, fallbacks=None, state_var="prepare_state"):
        """The prepare node: core + a guarded brief-specific `body` that reads the products (e.g. with
        freyalib.products_from_vars()), computes the brief's facts and calls, per product in get_account order,
        register_product(vars, pid, words, full, floor, floor_name, deadline_date, rungs)
        with rungs = [(amount_rule, date), ...] the brief's persuasion ladder (amount_rule in AMOUNT_RULES:
        'full_or_floor' = the floor once the customer said the full amount is too much; a rung date after the
        deadline is capped to it). Then init_negotiation(vars, <statement_expr>) with the statement of the debt
        (a Python expression over the body's names). `today` must be a datetime.date in the body."""
        fb = {"say_next": "", "state_line": "", "offer_question": "", "route": "negotiate"}
        fb.update(fallbacks or {})
        inner = self.core() + body.strip("\n") + "\ninit_negotiation(vars, %s)\n" % statement_expr + _declare()
        return fl.guarded(inner, state_var, fb)

    def ending_code(self, outcome, reason, promise_decides=True):
        """Code of a fin_<key> node: writes outcome/reason; with promise_decides, a promise recorded earlier in the
        call wins ("if a transfer takes place after a promise was recorded, the promise decides"): promise_outcome
        and the promise reason the core wrote (promise_reason). Use it for the promise ending itself too
        (ending_code(promise_outcome, <default reason>))."""
        ov, rv, po = self.P["outcome_var"], self.P["reason_var"], self.P["promise_outcome"]
        return ("try:\n    rec = str(vars.get('recorded_pids') or '').strip()\n"
                "    if %r and rec and rec.lower() not in ('none', 'null'):\n"
                "        vars[%r] = %r\n        vars[%r] = str(vars.get('promise_reason') or %r)\n"
                "        if vars[%r].lower() in ('none', 'null'):\n            vars[%r] = %r\n"
                "    else:\n        vars[%r] = %r\n        vars[%r] = %r\nexcept Exception:\n    pass\n"
                % (bool(promise_decides), ov, po, rv, reason if outcome == po else "", rv, rv,
                   reason if outcome == po else "", ov, outcome, rv, reason))

    def end_pair(self, key, outcome, reason, farewell, nodes, promise_decides=True):
        """freyalib.end_pair whose fin_<key> runs ending_code (a recorded promise decides the ending)."""
        fin, end = fl.end_pair(key, outcome, reason, farewell, nodes, self.P["outcome_var"], self.P["reason_var"])
        nodes[fin] = fl.code_node(fin, self.ending_code(outcome, reason, promise_decides), [fl.always(end)])
        return fin, end

    # ------------------------------------------------------------------ transitions
    def route_transitions(self):
        """The transitions every policy code node shares: endings first (route 'fin' + final_route), then every
        route value, then always -> negotiate."""
        trs = []
        seen = {self.fin_keys["default"]}
        for k in [self.fin_keys["promise"], self.fin_keys["paid"]] + [v for k, v in self.fin_keys.items() if k not in ("promise", "paid", "default")]:
            if k in seen:
                continue
            seen.add(k)
            trs.append(fl.tr("fin_" + k, "the call ends with %s" % k,
                             fl.and_group(fl.cond("route", "equals", "fin"), fl.cond("final_route", "equals", k))))
        # the default ending last and once: the engine merges transitions with the same target into one OR
        trs.append(fl.eq("route", "fin", "fin_" + self.fin_keys["default"], "the call ends"))
        for r in ROUTES:
            if r == "negotiate" or (r == "note" and not self.notes):
                continue
            trs.append(fl.eq("route", r, self.targets[r], "policy route %s" % r))
        trs.append(fl.always(self.targets["negotiate"]))
        return trs

    def add_event_nodes(self, nodes, names=None):
        """Adds the policy code nodes (EVENT_NODES, or the given subset) to `nodes` (note_after only with notes)."""
        for name, ev in EVENT_NODES.items():
            if (names is not None and name not in names) or (name == "note_after" and not self.notes):
                continue
            nodes[name] = fl.code_node(name, self.event_code(ev), self.route_transitions())
        return nodes

    # ------------------------------------------------------------------ helpers the task names
    def aside_extraction(self, conf=0.5):
        """The `aside` entry (only when the Policy has asides): a side question in the customer's LATEST message that
        must be answered before continuing, e.g. robot = asks whether they are talking to a robot. The generator
        supplies `when` (how to recognise it) and `say` (the brief's answer) per value; the core prefixes `say` to the
        line the route speaks (say_next / readback_line / wrap_line). Brief-agnostic."""
        if not self.asides:
            return []
        desc = ("A side question in the customer's LATEST message that must be answered before continuing: " +
                "; ".join("%s = %s" % (k, v["when"]) for k, v in self.asides.items()) +
                "; none = no such question. Pick it even when the message also contains an answer, an offer or a refusal.")
        return [fl.ext("aside", ["none"] + list(self.asides), desc, conf)]

    def said_extraction(self, conf=0.5):
        """`customer_said` (only when the brief keeps notes): the customer's own words for a hardship, a dispute, a
        payment already made or a refusal, kept by code per note kind and written into the note's free text."""
        return [{"name": "customer_said", "type": "string", "description": SAID_DESC, "min_confidence": conf}] if self.notes else []

    def claims_extraction(self, conf=0.5):
        """Multi-product only: `per_product`, what the customer's LATEST message says about each product when it says
        different things about different products, as 'first=dispute;second=paid;third=pay' (parsed in code:
        settle_claims / pay_claimed). Brief-agnostic; added to the negotiate node by negotiate_node()."""
        if not self.multi:
            return []
        o = self.P["ordinals"]
        desc = ("Only when the customer's LATEST message says DIFFERENT things about DIFFERENT products: one pair per product "
                "it mentions, '<position>=<claim>' separated by ';', where position is the product's place in the order the "
                "agent listed them (" + ", ".join(o) + ") and claim is one of: dispute (not theirs, never had it, closed or paid "
                "off in the past), paid (already paid it), pay (will pay it: accepts, or names a day or an amount for it; "
                "add '@' and the customer's OWN WORDS for that product's day when they name one), "
                "refuse (will not or cannot pay it). Example: '" + o[0] + "=dispute;" + o[min(1, len(o) - 1)] + "=pay@today;" +
                o[min(2, len(o) - 1)] + "=pay@monday the 26th'. Empty when the message is about all products together "
                "in one answer or about one product only. A pair only for a product the message NAMES (its type, its "
                "card digits or its position): words cut off before the product's name ('and I never had a') name no "
                "product, so leave that claim out, never guess which product it was." + POSITION_CLAUSE)
        return [{"name": "per_product", "type": "string", "description": desc, "min_confidence": conf}]

    @staticmethod
    def offer_extraction(date_desc, amount_desc, kind_desc, conf=0.5, ref_desc=None):
        """T1: offer_date (date), offer_amount (float), offer_kind (exact|vague|none), offer_when (the customer's
        words for the day, resolved in code), offer_ref (none|floor|full: an amount named by reference, resolved in
        code against the product; pass the brief's own names for its floor in ref_desc) and day_refused (none|yes: the
        proposed day was turned down, so an amount-only offer gets the exact-day question, never that day)."""
        kd = kind_desc if VAGUE_KIND_CLAUSE in str(kind_desc) else str(kind_desc) + VAGUE_KIND_CLAUSE
        return [fl.ext("offer_kind", ["none", "exact", "vague"], kd, conf),
                {"name": "offer_date", "type": "date", "description": date_desc, "min_confidence": conf},
                {"name": "offer_when", "type": "string", "description": WHEN_DESC, "min_confidence": conf},
                {"name": "offer_amount", "type": "float", "description": amount_desc, "min_confidence": conf},
                fl.ext("offer_ref", ["none", "floor", "full"], ref_desc or REF_DESC, conf),
                fl.ext("day_refused", ["none", "yes"], DAY_REFUSED_DESC, conf)]

    @staticmethod
    def offer_guard_transitions():
        """offer_kind exact|vague -> check_offer (the guard), stance accept -> accept_offer (the guard on the
        current offer). Put them after the topic transitions and before the stance counter."""
        return [fl.tr("check_offer", "the customer named a date, an amount or a vague period",
                      fl.cond("offer_kind", "equals", "exact"), fl.cond("offer_kind", "equals", "vague"),
                      fl.cond("offer_ref", "equals", "floor"), fl.cond("offer_ref", "equals", "full")),
                fl.eq("stance", "accept", "accept_offer", "the customer accepted the current offer")]

    @staticmethod
    def stance_extraction(desc, conf=0.5, values=("other", "accept", "refuse", "too_much", "offer")):
        """T2: stance in {refuse, too_much, offer, accept, other}, described with the brief's own definitions."""
        return fl.ext("stance", list(values), desc, conf)

    @staticmethod
    def stance_transitions():
        return [fl.eq("stance", "too_much", "too_much", "the customer says the amount is too much"),
                fl.eq("stance", "refuse", "count_refusal", "a flat refusal or a non-answer")]

    @staticmethod
    def topic_transitions(topic_var="topic", values=None):
        """topic value -> policy node (or transfer). `values` maps topic value -> event node / target, default:
        hardship, new_plan (restructuring transfer), human, no_talk, already_paid, dispute."""
        m = {"hardship": "pol_hardship", "new_plan": "xfer_restructuring", "human": "pol_human",
             "no_talk": "pol_notalk", "already_paid": "pol_paid", "dispute": "pol_dispute"}
        if values is not None:
            m = dict(values)
        return [fl.eq(topic_var, v, t, "topic %s" % v) for v, t in m.items()]

    @staticmethod
    def state_first(task, label="STATE (decided by the system; follow it, do not recompute it)"):
        """T3: {{state_line}} FIRST in a prompt."""
        return "%s: {{state_line}}\n\n%s" % (label, task)

    def negotiate_node(self, task, extraction, transitions, name=None):
        """The negotiation conversation node: on every entry it speaks the code-built {{say_next}} (tts),
        state_line first in its prompt, no tools (every write happens in the record nodes)."""
        name = name or self.targets["negotiate"]
        extraction = [dict(e, description=str(e.get("description") or "") + VAGUE_STANCE_CLAUSE)
                      if e.get("name") == "stance" and VAGUE_STANCE_CLAUSE not in str(e.get("description") or "") else
                      dict(e, description=str(e.get("description") or "") + VAGUE_KIND_CLAUSE)
                      if e.get("name") == "offer_kind" and VAGUE_KIND_CLAUSE not in str(e.get("description") or "") else
                      dict(e, description=str(e.get("description") or "") + POSITION_CLAUSE)
                      if e.get("name") == "offer_for" and POSITION_CLAUSE not in str(e.get("description") or "") else e
                      for e in extraction]
        return fl.conv(name, self.state_first(no_reask(task)) + ONCE_RULE, on_enter={"type": "tts", "text": "{{say_next}}"},
                       extraction=fl.with_cutoff(list(extraction) + self.claims_extraction() + self.aside_extraction() + self.said_extraction()),
                       transitions=transitions)

    def confirm_node(self, task, confirm_desc, date_desc, amount_desc, topic_entry=None, topic_trs=None,
                     name=None, conf=0.5, ref_desc=None):
        """T22: the read-back. on_enter tts {{readback_line}} (built in code from the agreed values, so what the
        customer hears is what gets written). Extraction confirm in {yes, no, change, other} (+ the new date or
        amount for a change, + the topic entry). yes -> rec_next (record loop), change -> change_offer (offer
        guard, read back again), no -> confirm_no (a flat refusal of the read-back offer). No tools."""
        name = name or self.targets["confirm"]
        ext = [fl.ext("confirm", ["other", "yes", "no", "change"], confirm_desc, conf),
               {"name": "offer_date", "type": "date", "description": date_desc, "min_confidence": conf},
               {"name": "offer_when", "type": "string", "description": WHEN_DESC, "min_confidence": conf},
               {"name": "offer_amount", "type": "float", "description": amount_desc, "min_confidence": conf},
               fl.ext("offer_ref", ["none", "floor", "full"], ref_desc or REF_DESC, conf)]
        if topic_entry:
            ext.append(topic_entry)
        # confirm routes FIRST: a read-back answer labelled both confirm=change and topic=new_plan is a change of the
        # offer, not a plan request (a different amount or date for this promise is never a restructuring transfer)
        trs = [
            fl.eq("confirm", "change", "change_offer", "the customer changes the date or the amount"),
            fl.eq("confirm", "yes", "rec_next", "the customer confirmed the read-back"),
            fl.eq("confirm", "no", "confirm_no", "the customer said no to the read-back"),
        ] + list(topic_trs or [])
        return fl.conv(name, self.state_first(task), on_enter={"type": "tts", "text": "{{readback_line}}"},
                       extraction=fl.with_cutoff(ext + self.claims_extraction(conf) + self.aside_extraction(conf)), transitions=trs)

    def promise_assert_pre(self, pid_field="product_id", amount_field="amount", date_field="date"):
        """Pre hook of the record node: the body MUST equal the approved values (rec_pid, rec_amount, rec_date,
        written by code from the read-back). A mismatch is replaced by the approved value and logged in
        vars['promise_guard'] (never a silent cap to some other value)."""
        return ("try:\n"
                "    b = config.get('body')\n"
                "    if isinstance(b, dict):\n"
                "        want = [(%r, str(vars.get('rec_pid') or '')), (%r, str(vars.get('rec_amount') or '')), (%r, str(vars.get('rec_date') or '')[:10])]\n"
                "        bad = []\n"
                "        for f, w in want:\n"
                "            if not w:\n"
                "                continue\n"
                "            have = b.get(f)\n"
                "            if f == %r:\n"
                "                try:\n"
                "                    same = abs(float(str(have).replace(',', '')) - float(w)) < 0.005\n"
                "                except Exception:\n"
                "                    same = False\n"
                "                if not same:\n"
                "                    bad.append(f)\n"
                "                b[f] = float(w)\n"
                "            else:\n"
                "                if str(have or '').strip()[:10] != w:\n"
                "                    bad.append(f)\n"
                "                b[f] = w\n"
                "        vars['promise_guard'] = ('corrected ' + ','.join(bad)) if bad else 'match'\n"
                "except Exception as e:\n"
                "    try:\n"
                "        vars['promise_guard'] = 'error ' + str(e)\n"
                "    except Exception:\n"
                "        pass\n" % (pid_field, amount_field, date_field, amount_field))

    def record_nodes(self, nodes, api, promise_tool="create_promise", note_tool="add_note", ok_field="ok",
                     pid_field="product_id", amount_field="amount", date_field="date", reason_field="reason"):
        """The write nodes: record_promise (api_request; body baked from rec_pid/rec_amount/rec_date, asserted by
        promise_assert_pre; data.<ok> -> rec_ok) -> rec_after; with notes, record_note (api_request; note_pid /
        note_reason; data.<ok> -> note_ok) -> note_after. The tools' field names are checked against the API."""
        spec = fl.tool_spec(api, promise_tool)
        for f in (pid_field, amount_field, date_field):
            if f not in spec["fields"]:
                raise KeyError("%s has no field %r in the API file" % (promise_tool, f))
        tool = fl.api_tool(api, promise_tool, baked={pid_field: "{{rec_pid}}", amount_field: "{{rec_amount}}",
                                                     date_field: "{{rec_date}}"},
                           description="Record the confirmed promise of one product.",
                           pre=self.promise_assert_pre(pid_field, amount_field, date_field))
        nodes[self.targets["record"]] = fl.api_node(self.targets["record"], tool, [fl.always("rec_after")],
                                                    mapping=[{"path": "data.%s" % ok_field, "variable": "rec_ok"}])
        if self.notes:
            nspec = fl.tool_spec(api, note_tool)
            enum = nspec["fields"].get(reason_field, {}).get("enum") or []
            for st, r in self.P["note_reasons"].items():
                if enum and r not in enum:
                    raise ValueError("note reason %r (state %s) is not in the API's %s.%s enum %s" % (r, st, note_tool, reason_field, enum))
            baked_n = {pid_field: "{{note_pid}}", reason_field: "{{note_reason}}"}
            if "text" in nspec["fields"]:
                baked_n["text"] = "{{note_text}}"
            omit = [f for f in nspec["fields"] if f not in baked_n and f != fl.CUSTOMER_ID and f not in nspec["required"]]
            ntool = fl.api_tool(api, note_tool, baked=baked_n,
                                description="Record why one product has no promise.", omit=omit)
            nodes[self.targets["note"]] = fl.api_node(self.targets["note"], ntool, [fl.always("note_after")],
                                                      mapping=[{"path": "data.%s" % ok_field, "variable": "note_ok"}])
        return nodes

    def hardship_node(self, task, answer_desc, kind_desc, date_desc, amount_desc, name=None, conf=0.5, ref_desc=None, human=False):
        """Hardship (sympathy + support offer spoken from {{say_next}}, no persuasion by routing): hs_answer in
        {support_yes, support_no, accept_offer, none}; a named date or amount still goes through the offer guard
        and the read-back; support_no without a named offer closes the open products as hardship.
        human=True adds hs_answer 'human' -> pol_human (the human-request counter) for a brief whose human-request rule
        also applies during hardship; describe the value in answer_desc."""
        name = name or self.targets["hardship"]
        vals = ["none", "support_yes", "support_no", "accept_offer"] + (["human"] if human else [])
        ext = [fl.ext("hs_answer", vals, answer_desc, conf)] + \
            self.offer_extraction(date_desc, amount_desc, kind_desc, conf, ref_desc)
        trs = ([fl.eq("hs_answer", "human", "pol_human", "the customer asks for a person")] if human else []) + [
               fl.eq("hs_answer", "support_yes", self.targets["xfer_support"], "the customer accepts the support team"),
               fl.tr("check_offer", "the customer names a date or an amount", fl.cond("offer_kind", "equals", "exact"),
                     fl.cond("offer_ref", "equals", "floor"), fl.cond("offer_ref", "equals", "full")),
               fl.eq("hs_answer", "accept_offer", "accept_offer", "the customer accepts the corrected offer"),
               fl.eq("hs_answer", "support_no", "hs_decline", "the customer declines the support team")]
        return fl.conv(name, self.state_first(no_reask(task)) + ONCE_RULE, on_enter={"type": "tts", "text": "{{say_next}}"},
                       extraction=fl.with_cutoff(ext + self.aside_extraction(conf) + self.said_extraction(conf)), transitions=trs)

    def wrapup_node(self, task, wrap_desc, name=None, conf=0.5, max_turns=3):
        """After a recorded promise (on_enter tts {{wrap_line}}: the recorded sentence, the brief's sentence after
        a promise, 'anything else?'). wrap in {done, human, new_plan, change, question, other}: done -> finalize
        (the promise ending), human -> wrap_human (ask once, then transfer), new_plan -> restructuring transfer,
        change -> wrap_change (the brief's sentence, promise unchanged), question -> stay (the model answers);
        max_turns turns at most, then finalize."""
        name = name or self.targets["wrapup"]
        ext = [fl.ext("wrap", ["other", "done", "human", "new_plan", "change", "question"], wrap_desc, conf)]
        trs = [fl.eq("wrap", "done", "finalize", "nothing else"),
               fl.eq("wrap", "human", "wrap_human", "asks for a human"),
               fl.eq("wrap", "new_plan", self.targets["xfer_restructuring"], "asks for a new plan"),
               fl.eq("wrap", "change", "wrap_change", "asks to change or cancel the promise")]
        n = fl.conv(name, self.state_first(task), on_enter={"type": "tts", "text": "{{wrap_line}}"},
                    extraction=fl.with_cutoff(ext + self.aside_extraction(conf)), transitions=trs, max_turns=max_turns)
        n["max_turn_transition"] = "finalize"
        return n
