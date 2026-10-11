"""Generator for slot `harrow` (Corran Bay Bank pack: mail + AHS-5 s.5 + 9 Oct minutes + dialler code card).
Structure of out/gen_brief-b_v3.py (policy as code, 1-3 products, notes); every value and sentence from the brief,
with the 9 Oct minutes in force (Middle band = 4th business day, card floor = half past_due rounded up to 5,
cut-over closure 6 Nov instead of 13 Nov). Usage: python3 out/gen_harrow.py <api.json> [out.json]"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

API = fl.load_api(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools/openapi.json")
SPEC = json.load(open(ROOT / "out/harrow.spec.json"))["spec"]
HOLIDAYS = [h["date"] for h in SPEC["calendar"]["holidays"]]   # R44/R71: 2026-11-06 replaces 2026-11-13
assert "2026-11-06" in HOLIDAYS and "2026-11-13" not in HOLIDAYS

nodes = {}
BANK = "Corran Bay Bank"

# ---------------------------------------------------------------- terminals: the dialler code card (R75, R95)
NAME = "{{title}} {{last_name}}"
XFER = "I am putting you through now. Please stay on the line."
FINS = {
    "promise": ("promise", "FULLPTP", "Thank you, " + NAME + ". Your arrangement is in place. Goodbye."),
    "paid": ("paid", "CLMPD", "Thank you. A payment can take up to two business days to reach us. Thank you for letting us know. Goodbye."),
    "transferred_restructuring": ("transferred", "XRST", "Goodbye."),
    "transferred_human": ("transferred", "XGEN", "Goodbye."),
    "transferred_support": ("transferred", "XCARE", "Goodbye."),
    "tdn": ("no_promise", "TDN", "Thank you for your time, " + NAME + ". Goodbye."),
    "tdn2l": ("no_promise", "TDN2L", "Your second-look call is booked for {{second_look_text}} at {{sl_time}}. Thank you for your time, " + NAME + ". Speak to you then. Goodbye."),
    "hardship": ("no_promise", "HDNX", "Thank you for telling me. Take care, " + NAME + ". Goodbye."),
    "dispute": ("no_promise", "DSPT", "We will look into this and write to you. Goodbye."),
    "sysf": ("no_promise", "SYSF", "I'm sorry, our system is not responding. We will call you again. Goodbye."),
    "failed": ("not_verified", "IDNO", "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye."),
    "declined": ("not_verified", "IDREF", "I understand. You can use the Corran Bay app or visit any branch. Goodbye."),
    "callback": ("not_reached", "TPCB", "Thank you, we will call back then. Goodbye."),
    "nocon": ("not_reached", "NOCON", "Thank you. Goodbye."),
    "deceased": ("not_reached", "NOCON", "I am very sorry to hear that. Thank you. Goodbye."),
}
POLICY_FINS = {"promise", "paid", "transferred_restructuring", "transferred_human", "transferred_support", "tdn", "tdn2l", "hardship", "dispute", "sysf"}

# ---------------------------------------------------------------- setup: dates (R44-R62, R69)
EXTRA = r'''
def nth_bd(d, n):
    return addbd(d, n)
e = today + datetime.timedelta(days=14)
while not isbd(e):
    e = e + datetime.timedelta(days=1)
vars['early_deadline'] = e.isoformat()
vars['middle_deadline'] = addbd(today, 4).isoformat()
vars['late_deadline'] = addbd(today, 3).isoformat()
vars['late_a1'] = addbd(today, 1).isoformat()
vars['part_deadline'] = addbd(today, 2).isoformat()
sl = addbd(today, 3)
vars['second_look_date'] = sl.isoformat()
vars['second_look_text'] = sl.strftime('%A') + ' ' + str(sl.day) + ' ' + sl.strftime('%B')
'''
SETUP = fl.SETUP_CODE(HOLIDAYS, callback_rule={"open": "10:00", "close": "16:00", "same_day": False, "days_ahead": 2},
                      extra=EXTRA, fallbacks={"second_look_text": "the third business day from today", "second_look_date": "2026-10-19"})

# ---------------------------------------------------------------- opening (R07-R12)
WHO_VALUES = ["customer", "someone_else", "wrong_number", "deceased", "refuses", "unclear"]
WHO_DESC = ("Who answered, judged ONLY from the person's latest message. "
            "customer = 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} / {{last_name}}). "
            "someone_else = another person answered (relative, partner, flatmate), or says the customer is not here / not available. "
            "wrong_number = this number does not belong to that person / they do not know them. "
            "deceased = says the customer has died. "
            "refuses = says they do not want to talk. "
            "unclear = anything else: 'hello?', 'who wants to know?', 'what's this about?', any question, silence.")
OPENING_ROUTES = [
    ("customer", "ask_dob", "the customer confirmed who they are"),
    ("deceased", "fin_deceased", "the customer has died"),
    ("wrong_number", "fin_nocon", "wrong number"),
    ("someone_else", "third_party", "someone else answered"),
]
OPEN_LINE = "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded. Could I speak to {{first_name}} {{last_name}}, please?"
nodes["opening"] = fl.conv(
    "opening",
    "If you have not spoken yet, say exactly: \"" + OPEN_LINE + "\" Do not call any tool in this turn. Do not say why you are calling.",
    on_enter={"type": "tts", "text": OPEN_LINE},
    extraction=[fl.ext("who1", WHO_VALUES, WHO_DESC)], first_only=True)
INITIAL = fl.conversation_first("opening", SETUP, "who1", OPENING_ROUTES, "opening_retry", nodes)

ASIDES_TXT = ("If the person asked whether this is a robot: say \"Yes, I am an automated assistant.\" "
              "If they asked whether this is a scam: say they are free to hang up and call us on the number on the Corran Bay website. ")
FORBID = ("Never say any of these words: overdue, arrears, missed, owe, debt, balance, payment, account, card, credit card, loan, car loan. "
          "Never say why you are calling or which department. ")
nodes["opening_retry"] = fl.conv(
    "opening_retry",
    "You asked to speak to {{first_name}} {{last_name}}, but it is not clear who answered. No tool call in this turn. " + FORBID +
    ASIDES_TXT + "If they asked what this is about or who wants to know: say you are the automated assistant of Corran Bay Bank with a personal message for {{first_name}} {{last_name}}. "
    "If they said they do not want to talk: say \"This will only take a moment.\" "
    "Then ask exactly once more: \"Could I speak to {{first_name}} {{last_name}}, please?\"",
    extraction=[fl.ext("who2", WHO_VALUES, WHO_DESC)],
    transitions=[
        fl.eq("who2", "customer", "ask_dob", "the customer confirmed who they are"),
        fl.eq("who2", "deceased", "fin_deceased", "the customer has died"),
        fl.eq("who2", "wrong_number", "fin_nocon", "wrong number"),
        fl.eq("who2", "someone_else", "third_party", "someone else answered"),
        fl.eq("who2", "refuses", "fin_declined", "refuses again"),
        fl.always("fin_nocon"),
    ])

# ---------------------------------------------------------------- third party (R13-R17, R61)
cb_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book a callback for the customer. CALL it as soon as the person agrees a day and time inside the allowed window.",
    field_descriptions={"date": "Callback date as YYYY-MM-DD, one of the allowed days.",
                        "time": "Callback time as HH:MM, 24 hour, from 10:00 to 16:00."},
    pre=fl.normalise_pre({"time": "time"}, date_order="dmy"),
    post=fl.ok_post("Callback booked.", "The booking failed. Try schedule_callback once more with the same values."))
nodes["third_party"] = fl.conv(
    "third_party",
    "You called for {{title}} {{last_name}} but someone else is on the line.\n" + FORBID +
    "Say that you are calling with a personal message for {{title}} {{last_name}}, and ask when they will be available. Nothing else.\n"
    "If they offer to answer questions, pay or arrange anything for the customer: thank them, decline, and ask again when {{title}} {{last_name}} can be reached.\n"
    + ASIDES_TXT + "\nNow: {{today_text}}, {{now_time}}. We never call back today.\n{{callback_text}}\n"
    "- If they name a day and time inside the window, call schedule_callback (date YYYY-MM-DD, time HH:MM).\n"
    "- If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed day, or if the time is outside 10:00-16:00 the nearest end of those hours (10:00 or 16:00). If they accept, book it.\n"
    "- If they turn down your proposal or cannot say when, book nothing: call transition_to_fin_nocon.\n"
    "After every tool result, speak or call the next tool.",
    tools=[cb_tool],
    extraction=[fl.ext("tp_status", ["none", "wrong_number", "deceased"],
                       "From the person's latest message: wrong_number if this number is not the customer's; deceased if the customer has died; otherwise none.")],
    transitions=[
        fl.ok_true("schedule_callback", "fin_callback", "callback booked"),
        fl.eq("tp_status", "deceased", "fin_deceased", "customer died"),
        fl.eq("tp_status", "wrong_number", "fin_nocon", "wrong number"),
        fl.intent_tool("fin_nocon", "No callback will be booked: the person turned down the one proposed slot, or cannot say when.",
                       "No callback booked"),
    ])

# ---------------------------------------------------------------- identity (R18-R22)
HINTS = {"day_month_swapped": "Day and month look swapped. NOT a wrong answer. Ask for the date of birth again with the month as a word, for example 14 March 1988."}
LIMIT_TXT = "The check has ended. Say nothing about why you called."
transfer_general = fl.api_tool(API, "transfer_to_agent", baked={"queue": "general"},
                               description="Transfer to a person. CALL it only when the customer asks for a person AGAIN after you asked once whether they are happy to continue with you.")
ID_COMMON = ("Rules for this step:\n- " + FORBID + "\n"
             "- The questions are there to protect their personal details: say that ONCE in the call (if they ask why, or will not answer), never a second time; then ask the same question again.\n"
             "- If they ask what the call is about: say you can tell them once the security questions are done, that the questions protect their personal details, and ask again (asking again what it is about instead of answering ends the call).\n"
             "- " + ASIDES_TXT + "\n"
             "- If they ask for a person: the first time say \"I can help you with this now. Are you happy to continue with me?\" If they ask again or say no, call transfer_to_agent.\n"
             "- After every tool result, speak or call the next tool. Follow what_to_do_next.")
REFUSAL_DESC = ("From the customer's LATEST message only: refused if they refuse to answer the security question, say they do not want to talk, "
                "or ask AGAIN what the call is about instead of answering. none if they give an answer or say anything else." + fl.QUESTION_ENUM_CLAUSE + fl.REFUSAL_NONE_CLAUSE)

for stage, field, q, nxt, desc, fdesc in [
        ("dob", "date_of_birth", "What is your date of birth?", "ask_phone",
         "Ask the first security question: their date of birth. When they give a full date call verify_identity with answer = YYYY-MM-DD. A date in numbers only is day, month, year (05/03/1990 = 1990-03-05). If only part of the date, ask for the rest first.",
         "The date of birth as YYYY-MM-DD."),
        ("phone", "phone_last4", "What are the last four digits of the phone number we hold for you?", "load_account",
         "The date of birth was correct. Ask the second security question: the last four digits of the phone number we hold for them. When they give four digits call verify_identity with answer = the four digits.",
         "Exactly four digits.")]:
    post = fl.verify_count_post(q, 2, HINTS, LIMIT_TXT, route_var="id_route_" + stage, counter="id_wrong_" + stage,
                                all_verified_text="Both answers are correct. Identity verified.",
                                verified_text="Correct. Now ask the second security question.",
                                wrong_text="Wrong answer. Say it does not match our records and ask once more: {question}")
    pre = fl.reset_pre(["question_count_" + stage])
    nodes["ask_" + stage] = fl.conv(
        "ask_" + stage, desc + "\n" + fl.latest_value_note(4 if stage == "phone" else None) + "\n" + ID_COMMON,
        tools=[fl.api_tool(API, "verify_identity", baked={"field": field}, pre=pre,
                           description="Check the answer to the security question. CALL it every time the customer gives an answer.",
                           field_descriptions={"answer": fdesc}, post=post), transfer_general],
        extraction=[fl.ext("refusal_" + stage, ["none", "refused", "question"], REFUSAL_DESC)],
        transitions=[
            fl.eq("id_route_" + stage, "exhausted", "fin_failed", "second wrong answer to this question"),
            (fl.is_true("verify_identity_response.data.all_verified", "load_account", "identity verified") if stage == "phone"
             else fl.is_true("verify_identity_response.data.verified", "ask_phone", "date of birth correct")),
            fl.transferred("fin_transferred_human", "transferred"),
            fl.eq("refusal_" + stage, "refused", "count_decline_" + stage, "customer refused"),
            fl.eq("refusal_" + stage, "question", "qb_" + stage, "asks a question back"),
        ])
    # R21: after a refusal was answered with the protection line, a question instead of an answer closes (declined)
    qb_code = ("try:\n    n = int(float(vars.get('question_count_%s') or 0)) + 1\n    vars['question_count_%s'] = n\n"
               "    vars['refusal_%s'] = 'none'\n    dc = int(float(vars.get('decline_count') or 0))\n"
               "    vars['qb_route'] = 'close' if (n >= 2 or dc >= 1) else 'retry'\nexcept Exception:\n    vars['qb_route'] = 'retry'\n") % (stage, stage, stage)
    nodes["qb_" + stage] = fl.code_node("qb_" + stage, qb_code, [fl.eq("qb_route", "close", "fin_declined", "a question instead of an answer after the explanation"),
                                                                 fl.always("ask_" + stage)])
    code = fl.counter_code("decline_count", 2, "decline_route", reset={"refusal_dob": "none", "refusal_phone": "none"})
    nodes["count_decline_" + stage] = fl.code_node("count_decline_" + stage, code, [
        fl.eq("decline_route", "close", "fin_declined", "second refusal"), fl.always("ask_" + stage)])

# ---------------------------------------------------------------- payment: policy as code
NOTE_ENUM = fl.tool_spec(API, "add_note")["fields"]["reason"]["enum"]
POLICY = pol.Policy(
    HOLIDAYS,
    texts={
        "question": "Can you pay [amount] [when]?",
        "tomorrow_when": "tomorrow, [date]",
        "question_product": "For your [words], can you pay [amount] [when]?",
        "question_all": "Can you pay all of these in full today?",                                   # R26
        "weekend_or_holiday": "I cannot record [named], it is not a business day. The first business day after it is [date].",
        "after_deadline": "The latest day I can record for your [words] is [deadline].",            # 5.6
        "before_today": "I cannot record a day that has passed. Please choose a day from today on.",
        "below_floor": "I cannot record [named]. The smallest amount I can record is [floor].",      # 5.4
        "above_full": "The overdue amount is [full], so that is what I can record.",
        "vague": "Which exact day would that be?",                                                    # 5.6
        "vague_deadline": "The latest day I can record is [deadline].",
        "too_much_floor": "I understand. The smallest amount I can record is [floor]. The rest stays overdue and we will contact you about it.",
        "exhausted": "I understand.",
        "one_by_one": "Let us take them one at a time.",
        "next_product": "Now your [words].",
        "paid": "Thank you. A payment can take up to two business days to reach us.",                # R34
        "dispute": "I understand. I will not take an arrangement for your [words].",                   # R35
        "hardship": "I'm sorry to hear that. I will put you through to our Customer Care team, who can help. Is that all right?",  # R37
        "human_first": "I can help you with this now. Are you happy to continue with me?",          # R36
        "notalk_first": "This will only take a moment.",                                              # R38
        "readback_head": "So that is ",
        "readback_item": "[amount] for your [words] on [date]",
        "readback_sep": "; and ",
        "own_deadline": "",
        "moved_bd": "",
        "readback_tail": ". Is that right?",                                                          # R29
        "recorded": "Your payment arrangement is recorded.",                                          # R30
        "recorded_many": "Your payment arrangement is recorded.",
        "after_recorded": "",
        "rec_failed": "I'm sorry, I could not record that.",                                         # R31
        "anything_else": "Is there anything else I can help you with?",
        "wrap_change": "An arrangement already recorded cannot be changed on this call.",           # 5.8
    },
    multi=True, notes=True,
    note_reasons={s: s for s in ("refused", "hardship", "dispute", "paid", "service_error") if s in NOTE_ENUM},
    notes_on_transfer=False,                                    # transfer freezes everything
    fin_keys={"promise": "promise", "paid": "paid", "default": "secondlook", "refused": "secondlook",
              "hardship": "hardship", "dispute": "dispute", "service_error": "sysf"},
    promise_reasons={"full": "FULLPTP", "partial": "PARTPTP"},
    fail_max=2, human_limit=2, notalk_limit=2, closed_day_move="after", weekday_rule="this_week",
    vague_again="deadline", above_full="agree",
    asides={
        "robot": {"when": "asks whether they are talking to a robot, a machine or an AI", "say": "Yes, I am an automated assistant."},
        "scam": {"when": "asks whether this call is a scam or genuine", "say": "You are free to hang up and call us on the number on the Corran Bay website."},
    })
ENDS = {}
for key, (outcome, reason, farewell) in FINS.items():
    if key in POLICY_FINS:
        ENDS[key] = POLICY.end_pair(key, outcome, reason, farewell, nodes)
    else:
        ENDS[key] = fl.end_pair(key, outcome, reason, farewell, nodes)
# PARTPTP has its own closing sentence (code card): fin_promise writes promise_reason, route the part case to its end.
_pf, _pe = fl.end_pair("promise_part", "promise", "PARTPTP",
                       "Thank you, " + NAME + ". The rest of the overdue amount is still due and we will be in touch about it. Goodbye.", nodes)
nodes["fin_promise"]["transitions"] = [fl.eq("reason", "PARTPTP", _pe, "part arrangement")] + nodes["fin_promise"]["transitions"]

PREPARE_BODY = fl.products_from_vars() + r'''
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
D = lambda k: datetime.date.fromisoformat(str(vars.get(k)))
part_raw = D('part_deadline')
prods = [p for p in prods if isinstance(p, dict)]
order = sorted(range(len(prods)), key=lambda i: (-int(float(prods[i].get('days_late') or 0)), i))
items = []
for i in order:
    p = prods[i]
    ptype = str(p.get('type') or '')
    pid = str(p.get('product_id') or ('p' + str(i + 1)))
    past_due = float(p.get('past_due') or 0)
    if ptype == 'credit_card':
        words = 'credit card ending ' + str(p.get('card_last4') or '')
        if str(vars.get('today_iso')) >= '2026-10-14':
            floor = float(int(math.ceil(past_due / 2.0 / 5.0 - 1e-9)) * 5)
        else:
            floor = float(p.get('minimum_payment') or past_due)
        floor = min(floor, past_due)
    else:
        words = ptype.replace('_', ' ') if ptype else 'loan'
        try:
            floor = float(p.get('instalment_amount'))
        except Exception:
            floor = past_due
    days_late = int(float(p.get('days_late') or 0))
    if days_late <= 7:
        dl = D('early_deadline'); part = min(part_raw, dl)
        rungs = [('full_or_floor', dl)]
    elif days_late <= 20:
        dl = D('middle_deadline'); part = min(part_raw, dl)
        rungs = [('full_or_floor', dl), ('floor', part)]
    else:
        dl = D('late_deadline'); part = min(part_raw, dl)
        rungs = [('full_or_floor', D('late_a1')), ('floor', part)]
    register_product(vars, pid, words, past_due, floor, 'smallest amount', dl, rungs)
    pset(vars, pid, 'part_deadline', part.isoformat())   # 5.4 part-payment last date
    items.append((words, past_due, days_late, dl, part, floor))
head = "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. "
statement = head
for w, pd, dl_, dd, pt, fl_ in items:
    statement += 'Your ' + w + ' has ' + fmt(pd) + ' overdue, ' + str(dl_) + ' days overdue. '
statement += 'Can you pay the overdue amount in full today?' if len(items) == 1 else 'Can you pay all of these in full today?'
lines = []
for w, pd, dl_, dd, pt, fl_ in items:
    lines.append(w + ': overdue ' + fmt(pd) + ', ' + str(dl_) + ' days, last date full payment ' + txt_short(dd) + ', smallest amount ' + fmt(fl_) + ', part payments only up to ' + txt_short(pt))
vars['products_facts'] = '; '.join(lines)
vars['outcome'] = 'no_promise'
vars['reason'] = 'TDN'
'''
PREPARE = POLICY.prepare_code("import math\n" + PREPARE_BODY, "statement", fallbacks={
    "say_next": "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. Can you pay the overdue amount in full today?",
    "products_facts": ""})

nodes["load_account"] = fl.api_node(
    "load_account", fl.api_tool(API, "get_account", description="Get the products.", retries=1),
    [fl.eq("get_account_response.ok", "false", "fin_sysf", "get_account failed"),
     fl.eq("get_account_response.ok", "False", "fin_sysf", "get_account failed"),
     fl.always("prepare")], mapping=[{"path": "data.products", "variable": "products"}])
nodes["prepare"] = fl.code_node("prepare", PREPARE, [fl.always("negotiate")])

TOPIC_DESC = ("What the customer's LATEST message says, if it is one of these. "
              "hardship = illness, bereavement, job loss or anything like it (wins over every other value). "
              "already_paid = says they have ALREADY paid (not 'I will pay'). "
              "dispute = says the product is not theirs or they never had it. "
              "new_plan = asks for a plan, lower monthly amounts or a payment holiday. Saying an amount is too much is NOT new_plan; a different amount or date is NOT new_plan." + fl.PLAN_REQUEST_CLAUSE + " "
              "human = asks to speak to a person. "
              "no_talk = says they do not want to talk (not a refusal to pay). "
              "none = anything else.")
STANCE_DESC = ("The customer's answer to the agent's LATEST proposal, latest message only. "
               "accept = agrees to exactly what was proposed. "
               "refuse = a no with no date and no amount, a flat refusal, or no answer ('I don't know'). "
               "too_much = says the amount is too much or they cannot pay that much, without naming an amount. "
               "offer = names their own date, amount or period (a date or amount is NEVER a refusal); 'I don't know the exact day' after being asked for the exact day is an offer with a vague period. "
               "other = anything else: a question, small talk.")
KIND_DESC = ("From the customer's LATEST message only. exact = a specific day or a specific amount, or both. "
             "vague = only a vague time ('next week', 'end of the month', 'payday', 'I don't know the exact day'). none = no date, amount or period.")
FOR_DESC = ("Which product the customer's LATEST message is about, in the order the agent listed them: first, second or third "
            "(match the product they name). all = all of them, or one date or amount for everything. none = no product named.")
DATE_DESC = ("The payment day the customer names in their LATEST message, in their own words. Leave empty when no specific day.")
AMOUNT_DESC = ("The amount the customer offers in their LATEST message, as a number ('two hundred' = 200). Empty when none. A day of the month is not an amount.")
REF_DESC = ("Whether the LATEST message names the amount BY REFERENCE: floor = 'the minimum', 'the smallest amount', 'the instalment', 'half'. "
            "full = 'all of it', 'the full amount' ONLY when they offer to pay it. none = otherwise.")
CONFIRM_DESC = ("The customer's answer to the read-back 'Is that right?', latest message only. yes = a clear yes. "
                "change = a different amount or date. no = a plain no without a new value. other = anything else.")

said = {"name": "customer_said", "type": "string", "description": "The customer's latest message, word for word (their own words: how and when they paid, what they dispute, their circumstances).", "min_confidence": 0.3}
topic = fl.ext("topic", ["none", "hardship", "already_paid", "dispute", "new_plan", "human", "no_talk"], TOPIC_DESC)
offer_for = fl.ext("offer_for", ["none", "all", "first", "second", "third"], FOR_DESC)
TOPIC_TRS = POLICY.topic_transitions()

FACTS = "FACTS\n- Products: {{products_facts}}.\n- Today: {{today_text}}.\n"
COMMON = ("- If asked whether you are a robot: \"Yes, I am an automated assistant.\" If asked whether this is a scam: they are free to hang up and call us on the number on the Corran Bay website.\n"
          "- Never mention fees, credit file, recovery agents or court. Never describe a plan.\n"
          "- A question the facts do not answer: \"I don't have that information.\"\n"
          "- No tool call is allowed here. Never say that something is recorded.\n")
NEGOTIATE = ("You are talking with {{title}} {{last_name}}, who is verified. The line you just said and the offer in STATE were decided by the system from the bank's rules.\n"
             "- Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. The only offer you may make is the current offer in STATE, word for word.\n"
             "- If the customer asks a question or says something else, answer it in one short sentence, then ask the current offer again.\n"
             + COMMON + FACTS)
neg_ext = [topic, said, POLICY.stance_extraction(STANCE_DESC), offer_for] + POLICY.offer_extraction(DATE_DESC, AMOUNT_DESC, KIND_DESC, ref_desc=REF_DESC)
nodes["negotiate"] = POLICY.negotiate_node(NEGOTIATE, neg_ext, TOPIC_TRS + POLICY.offer_guard_transitions() + POLICY.stance_transitions())
CONFIRM = ("You read back the arrangement and asked \"Is that right?\". It is recorded only after a clear yes.\n"
           "- If the customer asks something, answer in one short sentence, then ask again: \"Is that right?\".\n" + COMMON + FACTS)
nodes["confirm"] = POLICY.confirm_node(CONFIRM, CONFIRM_DESC, DATE_DESC, AMOUNT_DESC, topic_entry=topic, topic_trs=TOPIC_TRS, ref_desc=REF_DESC)
HS_ANSWER_DESC = ("From the customer's LATEST message. support_yes = they agree to be put through to Customer Care ('yes', 'okay', 'please'). "
                  "support_no = they do not want to be put through. accept_offer = they agree to a date and amount just proposed. none = anything else.")
HARDSHIP = ("The customer mentioned a hardship. You said \"I'm sorry to hear that.\" and that you will put them through to Customer Care.\n"
            "- Make NO attempt. Never propose an amount or a date. If they ask something, answer in one short sentence.\n" + COMMON + FACTS)
nodes["hardship"] = POLICY.hardship_node(HARDSHIP, HS_ANSWER_DESC, KIND_DESC, DATE_DESC, AMOUNT_DESC, ref_desc=REF_DESC)
WRAP_DESC = ("From the customer's LATEST message, after the agent said the arrangement is recorded and asked whether there is anything else. "
             "done = nothing else. human = asks for a person. new_plan = asks for a plan or lower monthly amounts. "
             "change = asks to change a recorded arrangement. question = asks a question. other = anything else.")
WRAPUP = ("The arrangements in STATE are recorded. You said so and asked whether there is anything else.\n"
          "- Answer a question in one sentence from the facts or say \"I don't have that information.\", then ask whether there is anything else.\n"
          "- A recorded arrangement cannot be changed on this call.\n" + COMMON + FACTS)
nodes["wrapup"] = POLICY.wrapup_node(WRAPUP, WRAP_DESC)
POLICY.add_event_nodes(nodes)
POLICY.record_nodes(nodes, API)

for q, fin, line in [("restructuring", "fin_transferred_restructuring", XFER),
                     ("support", "fin_transferred_support", "I am putting you through to Customer Care now. Please stay on the line."),
                     ("general", "fin_transferred_human", XFER)]:
    # Known gap: the code card wants the line BEFORE transfer_to_agent; an api node runs its tool before its tts.
    # A tts code node in front of it re-runs the transfer on the customer's next turn (chat route), so it is not used.
    nodes[f"xfer_{q}"] = fl.api_node(
        f"xfer_{q}", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1),
        [fl.always(fin)], on_enter={"type": "tts", "text": line})

# ---------------------------------------------------------------- second look (R50-R53, 5.7): products turned down
# fin_secondlook: a 'does not want to talk' ending gets no second look; otherwise offer it once.
# code card precedence (several products, nothing recorded): SYSF, HDNX, DSPT, TDN2L, TDN -> 'worse' beats the second look
SL_GATE = ("try:\n    ids = [x for x in str(vars.get('pids_csv') or '').split(',') if x]\n"
           "    st = [str(vars.get('state_' + p) or '') for p in ids]\n"
           "    w = 'none'\n    for k, f in (('service_error', 'sysf'), ('hardship', 'hardship'), ('dispute', 'dispute')):\n"
           "        if k in st:\n            w = f\n            break\n    vars['sl_worse'] = w\n"
           "    n = int(float(vars.get('notalk_count') or 0))\n    vars['sl_route'] = 'skip' if n >= 2 else 'offer'\n"
           "except Exception:\n    vars['sl_route'] = 'offer'\n    vars['sl_worse'] = 'none'\n")
WORSE = [fl.eq("sl_worse", k, "fin_" + k, "a more serious situation decides the code") for k in ("sysf", "hardship", "dispute")]
nodes["fin_secondlook"] = fl.code_node("fin_secondlook", SL_GATE, [fl.and_tr("fin_tdn", "did not want to talk", ("sl_route", "skip"), ("sl_worse", "none"))] if hasattr(fl, "and_tr") else
                                       [fl.tr("fin_tdn", "did not want to talk", fl.and_group(fl.cond("sl_route", "equals", "skip"), fl.cond("sl_worse", "equals", "none")))]
                                       + [fl.tr("fin_" + k, "did not want to talk; " + k, fl.and_group(fl.cond("sl_route", "equals", "skip"), fl.cond("sl_worse", "equals", k))) for k in ("sysf", "hardship", "dispute")]
                                       + [fl.always("offer_second_look")])
nodes["sl_done"] = fl.code_node("sl_done", "try:\n    vars['sl_x'] = '1'\nexcept Exception:\n    pass\n", WORSE + [fl.always("fin_tdn2l")])
nodes["sl_none"] = fl.code_node("sl_none", "try:\n    vars['sl_x'] = '0'\nexcept Exception:\n    pass\n", WORSE + [fl.always("fin_tdn")])
sl_tool = fl.api_tool(
    API, "schedule_callback", baked={"date": "{{second_look_date}}"},
    description="Book the second-look call. CALL it when the customer agrees and names a time from 12:00 to 18:00.",
    field_descriptions={"time": "The time the customer chose, HH:MM 24 hour, from 12:00 to 18:00."},
    pre=fl.normalise_pre({"time": "time"}, date_order="dmy"),
    post=fl.ok_post("Second-look call booked.", "The booking failed. Try once more with the same values."))
nodes["offer_second_look"] = fl.conv(
    "offer_second_look",
    "No arrangement was made for a product the customer turned down. Offer ONCE a second-look call: a colleague rings them back to go through it again, on {{second_look_text}}, at a time they choose from 12:00 to 18:00.\n"
    "- If they agree and name a time from 12:00 to 18:00, call schedule_callback with that time.\n"
    "- If the time is outside 12:00-18:00: say the hours are 12:00 to 18:00 once and ask again. If the second time does not fit either, or they decline, call transition_to_fin_tdn.\n"
    "- After every tool result, speak or call the next tool.\n" + COMMON.replace("- No tool call is allowed here. Never say that something is recorded.\n", ""),
    on_enter={"type": "tts", "text": "Before you go, would you like a colleague to call you back for a second look, on {{second_look_text}}, at a time you choose between 12:00 and 18:00?"},
    tools=[sl_tool],
    extraction=[{"name": "sl_time", "type": "string", "description": "The callback time the customer chose, as HH:MM 24 hour ('three pm' = 15:00). Empty if none.", "min_confidence": 0.5}],
    transitions=[
        fl.ok_true("schedule_callback", "sl_done", "second look booked"),
        fl.intent_tool("sl_none", "No second-look call: the customer declined, or the second time named was outside 12:00-18:00.", "No second look"),
    ])

close_call = fl.close_call_tool(
    API,
    outcome_desc="From the dialler code card: promise, paid, transferred, no_promise, not_verified, not_reached.",
    reason_desc="FULLPTP/PARTPTP (promise), CLMPD (paid), XRST/XGEN/XCARE (transferred), TDN/TDN2L/HDNX/DSPT/SYSF (no_promise), IDNO/IDREF (not_verified), TPCB/NOCON (not_reached).",
    no_reason_outcomes=())

SYSTEM = ("You are the automated assistant of Corran Bay Bank on an outbound call to {{title}} {{last_name}}. Speak English. One or two short sentences per turn. "
          "Once the right person is on the line, call them {{title}} {{last_name}}.\n"
          "Always:\n"
          "- Robot question: say \"Yes, I am an automated assistant.\", then continue. Scam question: they are free to hang up and call us on the number on the Corran Bay website, then continue.\n"
          "- Before both security questions are passed never say: overdue, arrears, missed, owe, debt, balance, payment, account, card, credit card, loan, car loan.\n"
          "- Never invent figures, dates or reasons. A question you cannot answer from the tools: \"I don't have that information.\"\n"
          "- Never ask how much the customer can pay. Never mention fees, credit file, recovery agents or court.\n"
          "- Do not say goodbye or end the call yourself: the call is closed for you.\n"
          "- Call at most one tool per message. After every tool result, speak or call the next tool. Follow what_to_do_next.\n"
          "- Say amounts as plain numbers and dates as weekday, day and month.")

wf = fl.assemble(INITIAL, nodes, SYSTEM, [close_call], conduct=True)

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out/harrow.workflow.json"
    fl.write_workflow(wf, out)
    print("nodes:", len(nodes), "->", out)
