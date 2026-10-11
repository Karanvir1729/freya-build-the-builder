"""Generator for slot 'tamsin' (Corran Bay Bank pack: mail + AHS-5 s.5 + 9 Oct minutes + code card v2).
Structure from out/gen_brief-b_v3.py (policy as code, one to three products); every value from the brief.
Rules in force: minutes of 9 Oct (card floor = half past_due rounded up to 5, capped; middle band = 4th business
day; cut-over closure moved to 6 Nov, 13 Nov a working day)."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

API = fl.load_api(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools/openapi.json")
# R51 superseded by R83: 13 Nov is a working day, 6 Nov is closed (minutes item 4)
HOLIDAYS = ["2026-10-22", "2026-11-06", "2026-11-24", "2026-12-25", "2026-12-28"]
BANK = "Corran Bay Bank"

nodes = {}

# ---------------------------------------------------------------- terminals (code card v2)
TPL_END = "Thank you for your time, {{title}} {{last_name}}. Goodbye."
FINS = {
    "promise_full": ("promise", "FULLPTP", "Thank you, {{title}} {{last_name}}. Your arrangement is in place. Goodbye."),
    "promise_part": ("promise", "PARTPTP", "Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."),
    "paid": ("paid", "CLMPD", "Thank you. A payment can take up to two business days to reach us. Thank you for letting us know. Goodbye."),
    "transferred_restructuring": ("transferred", "XRST", "Please stay on the line."),
    "transferred_human": ("transferred", "XGEN", "Please stay on the line."),
    "transferred_support": ("transferred", "XCARE", "Please stay on the line."),
    "tdn": ("no_promise", "TDN", TPL_END),
    "tdn2l": ("no_promise", "TDN2L", "Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye."),
    "hardship": ("no_promise", "HDNX", "Thank you for telling me. Take care, {{title}} {{last_name}}. Goodbye."),
    "dispute": ("no_promise", "DSPT", "We will look into this and write to you. Goodbye."),
    "service_error": ("no_promise", "SYSF", "I'm sorry, our system is not responding. We will call you again. Goodbye."),
    "failed": ("not_verified", "IDNO", "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye."),
    "declined": ("not_verified", "IDREF", "I understand. You can use the Corran Bay app or visit any branch. Goodbye."),
    "callback": ("not_reached", "TPCB", "Thank you, we will call back then. Goodbye."),
    "no_callback": ("not_reached", "NOCON", "Thank you. Goodbye."),
    "deceased": ("not_reached", "NOCON", "I am very sorry to hear that. Thank you. Goodbye."),
}
for key, (outcome, reason, farewell) in FINS.items():
    fl.end_pair(key, outcome, reason, farewell, nodes)
# aliases used by the shared routes
for alias, target in [("wrong_number", "no_callback"), ("unclear", "no_callback")]:
    nodes[f"fin_{alias}"] = fl.code_node(f"fin_{alias}", "try:\n    vars['alias_route'] = 'end'\nexcept Exception:\n    pass\n", [fl.always(f"fin_{target}")])

# ---------------------------------------------------------------- setup: dates (AHS-5 5.1, 5.3, 5.4, 5.6a, 5.7)
DATES = r'''
vars['early_deadline'] = nextbd_on_or_after(today + datetime.timedelta(days=14)).isoformat()
vars['middle_deadline'] = addbd(today, 4).isoformat()
vars['late_deadline'] = addbd(today, 3).isoformat()
vars['late_a1'] = addbd(today, 1).isoformat()
vars['part_deadline'] = addbd(today, 2).isoformat()
sl = addbd(today, 3)
vars['secondlook_iso'] = sl.isoformat()
vars['secondlook_text'] = txt(sl)
'''
EXTRA_HELP = r'''
def nextbd_on_or_after(d):
    while not isbd(d):
        d = d + datetime.timedelta(days=1)
    return d
'''
SETUP = fl.SETUP_CODE(HOLIDAYS, callback_rule={"open": "10:00", "close": "16:00", "same_day": False, "days_ahead": 2},
                      extra=EXTRA_HELP + DATES, fallbacks={"secondlook_text": "the third business day from today", "secondlook_iso": ""})

# ---------------------------------------------------------------- opening
WHO_VALUES = ["customer", "someone_else", "wrong_number", "deceased", "refuses", "unclear"]
WHO_DESC = ("Who answered, judged ONLY from the person's latest message. "
            "customer = 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} {{last_name}}). "
            "someone_else = another person answered (relative, partner, flatmate), or says the customer is not here / not available. "
            "wrong_number = this number does not belong to that person / they do not know them. "
            "deceased = says the customer has died. "
            "refuses = says they do not want to talk. "
            "unclear = anything else: 'hello?', 'who wants to know?', 'what's this about?', a question, silence.")
OPENING_ROUTES = [
    ("customer", "ask_dob", "the customer confirmed who they are"),
    ("deceased", "fin_deceased", "the customer has died"),
    ("wrong_number", "fin_wrong_number", "wrong number"),
    ("someone_else", "third_party", "someone else answered"),
]
OPEN_LINE = f"Hello, this is the automated assistant of {BANK}. This call may be recorded. Could I speak to {{{{first_name}}}} {{{{last_name}}}}, please?"
nodes["opening"] = fl.conv(
    "opening",
    "If you have not spoken yet, say exactly: \"" + OPEN_LINE + "\" Do not call any tool in this turn. Do not say why you are calling.",
    on_enter={"type": "tts", "text": OPEN_LINE},
    extraction=[fl.ext("who1", WHO_VALUES, WHO_DESC)], first_only=True)
INITIAL = fl.conversation_first("opening", SETUP, "who1", OPENING_ROUTES, "opening_retry", nodes)

SIDE = ("If asked whether this is a robot: say \"Yes, I am an automated assistant.\" If asked whether this is a scam: say they are free to hang up and call us on the number on the Corran Bay website. ")
nodes["opening_retry"] = fl.conv(
    "opening_retry",
    "You asked for {{first_name}} {{last_name}} but the answer did not confirm it. No tool call. Never say why you are calling; never say overdue, arrears, missed, owe, debt, balance, payment, account, card or loan.\n"
    "If the person asked a question, answer it briefly first. " + SIDE +
    "What it is about / who wants to know: you have a personal message for {{first_name}} {{last_name}}. If they said they do not want to talk, say \"This will only take a moment.\"\n"
    "Then ask exactly: \"Could I speak to {{first_name}} {{last_name}}, please?\"",
    extraction=[fl.ext("who2", WHO_VALUES, WHO_DESC)],
    transitions=[
        fl.eq("who2", "customer", "ask_dob", "the customer confirmed who they are"),
        fl.eq("who2", "deceased", "fin_deceased", "the customer has died"),
        fl.eq("who2", "wrong_number", "fin_wrong_number", "wrong number"),
        fl.eq("who2", "someone_else", "third_party", "someone else answered"),
        fl.eq("who2", "refuses", "fin_declined", "refuses again"),
        fl.always("fin_unclear"),
    ])

# ---------------------------------------------------------------- third party (R19, 5.6a)
cb_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book a callback for the customer. CALL it as soon as the person agrees a day and time inside the allowed window.",
    field_descriptions={"date": "Callback date as YYYY-MM-DD: one of the allowed days.",
                        "time": "Callback time as HH:MM, 24 hour, from 10:00 to 16:00."},
    post=fl.ok_post("Callback booked.", "The booking failed. Try schedule_callback once more with the same values."))
nodes["third_party"] = fl.conv(
    "third_party",
    "You called for {{title}} {{last_name}} but someone else is on the line.\n"
    "STRICT: say only that you are calling with a personal message for {{title}} {{last_name}}. Never say what it is about, nor the bank's department. Never say overdue, arrears, missed, owe, debt, balance, payment, account, card or loan. "
    "If they offer to answer questions or arrange anything for the customer, thank them, decline, and go back to when the customer can be reached.\n"
    "Ask when {{title}} {{last_name}} will be available.\n"
    "Now: {{today_text}}, {{now_time}}.\nAllowed callback window: the next business day after today or the business day after that (never today), from 10:00 to 16:00 both included.\n{{callback_text}}\n"
    "- If what they say fits the window, call schedule_callback (date YYYY-MM-DD, time HH:MM).\n"
    "- If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed business day (if the time is outside 10:00-16:00, the nearest end of the hours on that day). If they accept, book it.\n"
    "- If they turn that down, or cannot say, book nothing: call transition_to_fin_no_callback.\n"
    "- " + SIDE + "\nAfter every tool result, speak or call the next tool.",
    tools=[cb_tool],
    extraction=[fl.ext("tp_status", ["none", "wrong_number", "deceased"],
                       "From the person's latest message: wrong_number if this number is not the customer's; deceased if the customer has died; otherwise none.")],
    transitions=[
        fl.ok_true("schedule_callback", "fin_callback", "callback booked"),
        fl.eq("tp_status", "deceased", "fin_deceased", "customer died"),
        fl.eq("tp_status", "wrong_number", "fin_wrong_number", "wrong number"),
        fl.intent_tool("fin_no_callback",
                       "No callback: the person turned down the one proposed slot, or cannot say when the customer is reachable.",
                       "No callback can be booked"),
    ])

# ---------------------------------------------------------------- identity (R23, R85: one retry PER question)
HINTS = {"day_month_swapped": "Day and month look swapped. This is NOT a wrong answer. Ask for the date of birth again with the month as a word, for example 14 March 1988."}
MAX_WRONG = "The check has ended. Say nothing about why you called."
transfer_general = fl.api_tool(API, "transfer_to_agent", baked={"queue": "general"},
                               description="Transfer to a person. CALL it only when the customer asks for a person again after you asked once whether they are happy to continue with you.")
ID_COMMON = ("Rules for this step:\n"
             "- Never say overdue, arrears, missed, owe, debt, balance, payment, account, or any product name (card, credit card, loan, car loan), also not as the reason for the questions.\n"
             "- If they will not answer or ask why: say the questions are there to protect their personal details, and ask the same question again.\n"
             "- " + SIDE + "\n"
             "- If they ask for a person: ask once \"I can help you with this now. Are you happy to continue with me?\" If they say no or ask again, call transfer_to_agent.\n"
             "- After every tool result, speak or call the next tool. Follow what_to_do_next.")
REFUSAL_DESC = ("From the customer's LATEST message only: refused = refuses to answer the security question, says they do not want to talk, "
                "or asks what the call is about instead of answering. question = any other question back (why do you need it, who is calling, is this a robot). "
                "none = they give an answer or say anything else." + fl.REFUSAL_NONE_CLAUSE)


def id_tool(field, stops, question, desc, fdesc):
    return fl.api_tool(API, "verify_identity", baked={"field": field}, pre=fl.reset_pre(["question_count_" + ("dob" if field == "date_of_birth" else "phone")]),
                       description=desc, field_descriptions={"answer": fdesc},
                       post=fl.verify_post(question, HINTS, MAX_WRONG, stop_left=stops,
                                           all_verified_text="Both answers are correct. Identity verified.",
                                           verified_text="Correct. Now ask the second security question: the last four digits of the phone number we hold."))


DOB_Q = "What is your date of birth?"
PH_Q = "What are the last four digits of the phone number we hold for you?"
nodes["ask_dob"] = fl.conv(
    "ask_dob",
    "The person confirmed they are {{title}} {{last_name}}. Say you need to ask two security questions to protect their personal details, one at a time. Ask the first: their date of birth.\n"
    "When they give it, call verify_identity with answer = YYYY-MM-DD. A date given only in numbers is day, month, year (05/03/1990 = 1990-03-05). "
    "If only part of the date is given, ask for the rest first. " + fl.latest_value_note(what="the date") + "\n" + ID_COMMON,
    tools=[id_tool("date_of_birth", ("1", "0"), DOB_Q, "Check the date of birth. CALL it every time the customer gives a full date of birth.", "The date of birth as YYYY-MM-DD."), transfer_general],
    extraction=[fl.ext("refusal_dob", ["none", "refused", "question"], REFUSAL_DESC)],
    transitions=[
        fl.eq("verify_identity_response.data.wrong_answers_left", "1", "fin_failed", "second wrong answer to the date of birth"),
        fl.eq("verify_identity_response.data.wrong_answers_left", "0", "fin_failed", "check ended"),
        fl.is_true("verify_identity_response.data.verified", "after_dob", "date of birth correct"),
        fl.transferred("fin_transferred_human", "transferred"),
        fl.eq("refusal_dob", "refused", "count_decline_dob", "customer refused"),
        fl.eq("refusal_dob", "question", "qb_dob", "asks a question back"),
    ])
# after_dob: remember how many wrong answers are left, so the phone question allows exactly one wrong answer of its own
nodes["after_dob"] = fl.code_node("after_dob", r'''
try:
    left = str(vars.get('verify_identity_response.data.wrong_answers_left') or '3')
    vars['phone_variant'] = 'b' if left == '2' else 'a'
except Exception:
    vars['phone_variant'] = 'a'
''', [fl.eq("phone_variant", "b", "ask_phone_b", "one wrong answer used on the date of birth"), fl.always("ask_phone_a")])

for v, stops in [("a", ("1", "0")), ("b", ("0",))]:
    trs = [fl.is_true("verify_identity_response.data.all_verified", "load_account", "identity verified")]
    for s in stops:
        trs.append(fl.eq("verify_identity_response.data.wrong_answers_left", s, "fin_failed", "second wrong answer to the phone question"))
    trs += [fl.transferred("fin_transferred_human", "transferred"),
            fl.eq("refusal_phone", "refused", f"count_decline_phone_{v}", "customer refused"),
            fl.eq("refusal_phone", "question", f"qb_phone_{v}", "asks a question back")]
    nodes[f"ask_phone_{v}"] = fl.conv(
        f"ask_phone_{v}",
        "The date of birth was correct. Ask the second security question: \"" + PH_Q + "\"\n"
        "When they give four digits, call verify_identity with answer = the four digits only. " + fl.latest_value_note(4) + "\n" + ID_COMMON,
        tools=[id_tool("phone_last4", stops, PH_Q, "Check the last four digits of the phone number. CALL it every time the customer gives four digits.", "Exactly four digits."), transfer_general],
        extraction=[fl.ext("refusal_phone", ["none", "refused", "question"], REFUSAL_DESC)],
        transitions=trs)

for stage, ask in [("dob", "ask_dob"), ("phone_a", "ask_phone_a"), ("phone_b", "ask_phone_b")]:
    qstage = "dob" if stage == "dob" else "phone"
    qcode = fl.counter_code("question_count_%s" % qstage, 2, "qb_route", reset={"refusal_%s" % qstage: "none"})
    nodes[f"qb_{stage}"] = fl.code_node(f"qb_{stage}", qcode, [fl.eq("qb_route", "close", "fin_declined", "a second question back instead of an answer"), fl.always(ask)])
    code = fl.counter_code("decline_count", 2, "decline_route", reset={"refusal_dob": "none", "refusal_phone": "none"})
    nodes[f"count_decline_{stage}"] = fl.code_node(f"count_decline_{stage}", code, [
        fl.eq("decline_route", "close", "fin_declined", "second refusal"), fl.always(ask)])


# ---------------------------------------------------------------- payment: policy as code, one to three products
NOTE_ENUM = fl.tool_spec(API, "add_note")["fields"]["reason"]["enum"]
POLICY = pol.Policy(
    HOLIDAYS,
    texts={
        "question": "Can you pay [amount] [when]?",
        "today_when": "today, [date]",
        "tomorrow_when": "tomorrow, [date]",
        "question_product": "For your [words], can you pay [amount] [when]?",
        "question_all": "Can you pay all of these in full today?",
        "weekend_or_holiday": "[named] is not a business day, so I cannot record it. The nearest day I can record is [date].",
        "after_deadline": "The last date I can record for your [words] is [deadline]; that is the latest day that can be recorded.",
        "before_today": "[named] has already passed, so it cannot be recorded. Please choose a day from today on.",
        "below_floor": "I cannot record [named]. The smallest amount I can record is [floor].",
        "above_full": "The overdue amount is [full], so I will record [full].",
        "vague": "Which exact day would that be?",
        "vague_deadline": "The last date I can record is [deadline].",
        "too_much_floor": "I understand. I can record [floor] instead; the rest stays overdue and we will contact you about it.",
        "exhausted": "I understand.",
        "one_by_one": "Let us go through them one by one.",
        "next_product": "Next, your [words].",
        "paid": "Thank you. A payment can take up to two business days to reach us.",
        "dispute": "Thank you for telling me. I will not make an arrangement for your [words].",
        "hardship": "I'm sorry to hear that. I will put you through to our Customer Care team, who can help.",
        "human_first": "I can help you with this now. Are you happy to continue with me?",
        "notalk_first": "This will only take a moment.",
        "readback_head": "So that is ",
        "readback_item": "[amount] for your [words] [when]",
        "readback_sep": "; and ",
        "own_deadline": "",
        "moved_bd": "",
        "readback_tail": ". Is that right?",
        "recorded": "Your payment arrangement is recorded.",
        "recorded_many": "Your payment arrangement is recorded.",
        "after_recorded": "",
        "rec_failed": "I'm sorry, I could not record that.",
        "anything_else": "Is there anything else I can help you with?",
        "wrap_change": "An arrangement already recorded cannot be changed on this call.",
    },
    multi=True, notes=True,
    note_reasons={s: s for s in ("refused", "hardship", "dispute", "paid", "service_error") if s in NOTE_ENUM},
    notes_on_transfer=False,
    fin_keys={"promise": "promise", "paid": "paid", "default": "refused", "refused": "refused",
              "hardship": "hardship", "dispute": "dispute", "service_error": "service_error"},
    fail_max=2, human_limit=2, notalk_limit=2, closed_day_move="after", weekday_rule="this_week",
    vague_again="deadline", above_full="agree", promise_reasons={"full": "FULLPTP", "partial": "PARTPTP"},
    asides={
        "robot": {"when": "asks whether they are talking to a robot, a machine or an AI", "say": "Yes, I am an automated assistant."},
        "scam": {"when": "asks whether this call is a scam or genuine", "say": "You are free to hang up and call us on the number on the Corran Bay website."},
    })

# AHS-5 5.3/5.4/5.5 + minutes 2/3; 5.9 order: most days late first, ties keep get_account order
PREPARE_BODY = fl.products_from_vars() + r'''
import math
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
part_dl = datetime.date.fromisoformat(str(vars.get('part_deadline')))
idx = [(i, p) for i, p in enumerate(prods) if isinstance(p, dict)]
idx.sort(key=lambda t: (-int(float(t[1].get('days_late') or 0)), t[0]))
items = []
for i, p in idx:
    ptype = str(p.get('type') or '')
    pid = str(p.get('product_id') or ('p' + str(i + 1)))
    past_due = float(p.get('past_due') or 0)
    if ptype == 'credit_card':
        words = 'credit card ending ' + str(p.get('card_last4') or '')
        floor = min(past_due, math.ceil(past_due / 2.0 / 5.0 - 1e-9) * 5.0)
        floor_name = 'smallest amount'
    else:
        words = ptype.replace('_', ' ') if ptype else 'loan'
        try:
            floor = float(p.get('instalment_amount'))
        except Exception:
            floor = past_due
        floor_name = 'instalment amount'
    days_late = int(float(p.get('days_late') or 0))
    if days_late <= 7:
        deadline = datetime.date.fromisoformat(str(vars.get('early_deadline')))
        rungs = [('full_or_floor', deadline)]
    elif days_late <= 20:
        deadline = datetime.date.fromisoformat(str(vars.get('middle_deadline')))
        rungs = [('full_or_floor', deadline), ('floor', min(part_dl, deadline))]
    else:
        deadline = datetime.date.fromisoformat(str(vars.get('late_deadline')))
        a1 = datetime.date.fromisoformat(str(vars.get('late_a1')))
        rungs = [('full_or_floor', a1), ('floor', min(part_dl, deadline))]
    register_product(vars, pid, words, past_due, floor, floor_name, deadline, rungs)
    items.append((words, past_due, days_late, deadline))
statement = "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. "
for w, pd, dl_, dd in items:
    statement += 'Your ' + w + ' has ' + fmt(pd) + ' overdue, ' + str(dl_) + ' days overdue. '
if len(items) == 1:
    statement += 'Can you pay the overdue amount in full today?'
else:
    statement += 'Can you pay all of these in full today?'
lines = []
for w, pd, dl_, dd in items:
    lines.append(w + ': overdue ' + fmt(pd) + ', ' + str(dl_) + ' days overdue, last date for full payment ' + txt_short(dd))
vars['products_facts'] = '; '.join(lines)
vars['outcome'] = 'no_promise'
vars['reason'] = 'TDN'
'''
PREPARE = POLICY.prepare_code(PREPARE_BODY, "statement", fallbacks={
    "say_next": "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. Can you pay all of these in full today?",
    "products_facts": ""})

nodes["load_account"] = fl.api_node(
    "load_account", fl.api_tool(API, "get_account", description="Get the overdue products.", retries=1),
    [fl.is_true("get_account_failed", "fin_service_error", "get_account failed"), fl.always("prepare")],
    mapping=[{"path": "data.products", "variable": "products"}])
nodes["load_account"]["transitions"] = [fl.always("prepare")]
nodes["prepare"] = fl.code_node("prepare", PREPARE, [fl.always("negotiate")])

TOPIC_DESC = ("What the customer's LATEST message says, if it is one of these. "
              "hardship = illness, bereavement, job loss or anything like it (wins over every other value). "
              "already_paid = says they have ALREADY paid (not 'I will pay'). "
              "dispute = says a product or debt is not theirs / they never had it. "
              "new_plan = asks for a plan, lower monthly amounts or a payment holiday. Saying an amount is too much is NOT new_plan." + fl.PLAN_REQUEST_CLAUSE + " "
              "human = asks for a person, a human or an agent. "
              "no_talk = says they do not want to talk (not a refusal to pay). "
              "none = anything else.")
STANCE_DESC = ("The customer's answer to the agent's LATEST proposal, from their latest message only. "
               "accept = agrees ('yes', 'okay', 'fine'). "
               "refuse = a no with no date and no amount ('no', 'I can't'), or no answer ('I don't know'). "
               "too_much = says the amount is too much / they cannot pay that much, without naming an amount. "
               "offer = names their own date, amount or period: never a refusal. "
               "other = a question, small talk, a request.")
KIND_DESC = ("From the LATEST message only. exact = a specific day (date, weekday, 'tomorrow') or a specific amount, or both. "
             "vague = only a vague period ('next week', 'end of the month', 'payday') or 'I don't know the exact day' after being asked for the exact day. "
             "none = no date, amount or period.")
FOR_DESC = ("Which product the LATEST message is about, in the order the agent listed them: first, second or third "
            "(match the product they name). all = all of them / one date or amount for everything. none = no product named.")
DATE_DESC = ("The payment day the customer names in their LATEST message, in their own words. Leave empty when none.")
AMOUNT_DESC = ("The amount of money the customer offers in their LATEST message, as a number ('ninety five' = 95). Empty when none. A day of the month is not an amount.")
REF_DESC = ("Whether the LATEST message names the amount BY REFERENCE. floor = 'the minimum', 'the smallest amount', 'the instalment'. "
            "full = 'all of it', 'the full amount' ONLY when they offer to pay it. none = otherwise.")
CONFIRM_DESC = ("The answer to the read-back question 'Is that right?', latest message only. yes = a clear yes. "
                "change = a different amount or date. no = a plain no. other = anything else.")

topic = fl.ext("topic", ["none", "hardship", "already_paid", "dispute", "new_plan", "human", "no_talk"], TOPIC_DESC)
offer_for = fl.ext("offer_for", ["none", "all", "first", "second", "third"], FOR_DESC)
TOPIC_TRS = POLICY.topic_transitions()
FACTS = "FACTS\n- Products: {{products_facts}}.\n- Today: {{today_text}}.\n"
COMMON = ("- If asked whether you are a robot: \"Yes, I am an automated assistant.\" If asked whether this is a scam: they are free to hang up and call us on the number on the Corran Bay website.\n"
          "- Never mention consequences: no fees, credit file, recovery agents or court. Never describe plans.\n"
          "- A question the facts do not answer: \"I don't have that information.\"\n"
          "- No tool call here. Never say that anything is recorded.\n")
NEGOTIATE = ("You are talking with {{title}} {{last_name}}, who is verified, about missed payments. The line you just said and the offer in STATE were decided by the system.\n"
             "- Never propose, compute or change an amount or a date yourself, and NEVER ask how much they can pay. The only offer is the current offer in STATE, word for word.\n"
             "- If the customer asks a question or says something else, answer in one short sentence, then ask the current offer again.\n"
             + COMMON + FACTS)
neg_ext = [topic, POLICY.stance_extraction(STANCE_DESC), offer_for] + POLICY.offer_extraction(DATE_DESC, AMOUNT_DESC, KIND_DESC, ref_desc=REF_DESC)
nodes["negotiate"] = POLICY.negotiate_node(NEGOTIATE, neg_ext, TOPIC_TRS + POLICY.offer_guard_transitions() + POLICY.stance_transitions())
CONFIRM = ("You read back the arrangement and asked \"Is that right?\". It is recorded only after a clear yes.\n"
           "- If the customer asks something, answer in one short sentence, then ask again: \"Is that right?\".\n" + COMMON + FACTS)
nodes["confirm"] = POLICY.confirm_node(CONFIRM, CONFIRM_DESC, DATE_DESC, AMOUNT_DESC, topic_entry=topic, topic_trs=TOPIC_TRS, ref_desc=REF_DESC)
HS_ANSWER_DESC = ("From the LATEST message. support_yes = fine to be put through to Customer Care. "
                  "support_no = they do not want to be put through. accept_offer = agrees to a date and amount just proposed. none = anything else.")
HARDSHIP = ("The customer mentioned a hardship. You said \"I'm sorry to hear that.\" and that you will put them through to Customer Care.\n"
            "- Make NO attempt of any kind. Never propose an amount or a date.\n- If they ask a question, answer in one short sentence.\n" + COMMON + FACTS)
nodes["hardship"] = POLICY.hardship_node(HARDSHIP, HS_ANSWER_DESC, KIND_DESC, DATE_DESC, AMOUNT_DESC, ref_desc=REF_DESC)
WRAP_DESC = ("From the LATEST message, after the agent said the arrangement is recorded and asked whether there is anything else. "
             "done = nothing else. human = asks for a person. new_plan = asks for a plan or lower amounts. "
             "change = asks to change a recorded arrangement. question = asks a question. other = anything else.")
WRAPUP = ("The arrangements in STATE are recorded. You said so and asked whether there is anything else.\n"
          "- Answer a question in one sentence from these facts or say \"I don't have that information.\"\n"
          "- An arrangement already recorded cannot be changed on this call.\n" + COMMON + FACTS)
nodes["wrapup"] = POLICY.wrapup_node(WRAPUP, WRAP_DESC)
POLICY.add_event_nodes(nodes)
POLICY.record_nodes(nodes, API)

# promise ending: FULLPTP / PARTPTP by the reason the policy core wrote
nodes["fin_promise"] = fl.code_node("fin_promise", "try:\n    vars['promise_split'] = 'part' if str(vars.get('promise_reason') or '') == 'PARTPTP' else 'full'\nexcept Exception:\n    vars['promise_split'] = 'full'\n",
                                    [fl.eq("promise_split", "part", "fin_promise_part", "part payment"), fl.always("fin_promise_full")])

# second look (Document 1 'Second look', AHS-5 5.7): turned-down products, once per call, before the goodbye
sl_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book the second-look call. CALL it as soon as the customer names a time from 12:00 to 18:00.",
    baked={"date": "{{secondlook_iso}}"},
    field_descriptions={"time": "The time the customer chose, HH:MM, 24 hour, from 12:00 to 18:00."},
    post=fl.ok_post("Second-look call booked.", "The booking failed. Try schedule_callback once more with the same values."))
nodes["fin_refused"] = fl.conv(
    "fin_refused",
    "No arrangement was made. Offer once a second-look call: a colleague rings them back on {{secondlook_text}} to go through it again; they choose a time from 12:00 to 18:00.\n"
    "- If they agree and name a time inside 12:00-18:00, call schedule_callback with that time as HH:MM.\n"
    "- If the time is outside the hours, say the hours (12:00 to 18:00) once and ask again. If the second time does not fit either, or they decline, call transition_to_fin_tdn.\n"
    "- After the tool result, say exactly: \"Your second-look call is booked for {{secondlook_text}} at <HH:MM>.\"\n" + COMMON,
    on_enter={"type": "tts", "text": "Would you like a second-look call? A colleague can ring you back on {{secondlook_text}} to go through it again, at a time you choose between 12:00 and 18:00."},
    tools=[sl_tool],
    transitions=[fl.ok_true("schedule_callback", "fin_tdn2l", "second-look call booked"),
                 fl.intent_tool("fin_tdn", "The customer declines the second-look call, or the second time named does not fit 12:00-18:00.", "No second-look call")])

for q, fin, line in [("restructuring", "fin_transferred_restructuring", "I am putting you through now. Please stay on the line."),
                     ("support", "fin_transferred_support", "I am putting you through to Customer Care now. Please stay on the line."),
                     ("general", "fin_transferred_human", "I am putting you through now. Please stay on the line.")]:
    # the closing sentence is said BEFORE transfer_to_agent (code card): a code node speaks it, the next node transfers
    _api = fl.api_node(f"xfer_call_{q}", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1),
                       [fl.always(fin)], on_enter={"type": "tts", "text": line})
    _say = {k: v for k, v in _api.items() if k not in ("name", "pre_actions", "transitions", "type", "id")}
    nodes[f"xfer_call_{q}"] = fl.api_node(f"xfer_call_{q}", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1), [fl.always(fin)])
    nodes[f"xfer_{q}"] = fl.code_node(f"xfer_{q}", "try:\n    vars['xfer_queue'] = %r\nexcept Exception:\n    pass\n" % q, [fl.always(f"xfer_call_{q}")])
    _plain = fl.api_node("x", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1), [fl.always(fin)])
    for k, v in _api.items():
        if k not in _plain or _plain[k] != v:
            if k not in ("name", "id", "pre_actions"):
                nodes[f"xfer_{q}"][k] = v

close_call = fl.close_call_tool(
    API,
    outcome_desc="promise / paid / transferred / no_promise / not_verified / not_reached, from the dialler code card.",
    reason_desc="The code from the dialler code card: FULLPTP, PARTPTP, CLMPD, XRST, XGEN, XCARE, TDN, TDN2L, HDNX, DSPT, SYSF, IDNO, IDREF, TPCB, NOCON.",
    no_reason_outcomes=())

SYSTEM = ("You are the automated assistant of Corran Bay Bank on an outbound phone call to {{first_name}} {{last_name}}. Speak English. Keep every turn to one or two short sentences. Once the right person is on the line, address them as {{title}} {{last_name}}.\n"
          "Always:\n"
          "- If asked whether you are a robot: say \"Yes, I am an automated assistant.\", then continue.\n"
          "- If asked whether this is a scam: say they are free to hang up and call us on the number on the Corran Bay website, then continue.\n"
          "- Before both security questions are passed never say overdue, arrears, missed, owe, debt, balance, payment, account, card or loan.\n"
          "- Never invent figures, dates or reasons; if you cannot answer from the tools: \"I don't have that information.\"\n"
          "- Never mention fees, credit file, recovery agents or court.\n"
          "- Do not say goodbye or end the call yourself: the call is closed for you.\n"
          "- Call at most one tool per message. After every tool result, speak or call the next tool. Follow what_to_do_next.\n"
          "- Say amounts as plain numbers and dates as weekday, day and month, for example Friday 16 October.")

wf = fl.assemble(INITIAL, nodes, SYSTEM, [close_call], conduct=True)

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out/tamsin.workflow.json"
    fl.write_workflow(wf, out)
    print("nodes:", len(nodes), "->", out)
