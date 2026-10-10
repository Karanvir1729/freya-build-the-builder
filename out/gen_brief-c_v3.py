"""Brief C (Nordvik Savings Bank) generator, v3: policy as code (builder/policy.py). Writes out/brief-c_v3.workflow.json.

Transfer test of the v3 architecture: the STRUCTURE is that of out/gen_brief-a_v3.py (conversation-first opening,
one ask node per identity question, prepare -> negotiate -> check_offer -> confirm -> record -> wrapup on
policy.Policy); every value, rule and sentence comes from tests/synthetic/brief-c.md (`# Rn` = the brief's rule
number). Brief C specifics carried by Policy parameters: Monday-to-Saturday business days, 'this/next <weekday>' =
the first such weekday after today (weekday_rule='first_after'), the second vague answer is a non-answer
(vague_again='refuse'), an amount above the full amount is recorded as the full amount (above_full='agree'), the
promise reason full/partial (promise_reasons), the promise decides over a later transfer (POLICY.end_pair), a human
request transfers at once (human_limit=1), 'does not want to talk' ends at once (notalk_limit=1), two retries of a
failed write (fail_max=3)."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

API = fl.load_api(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools/openapi.json")
# section 7: business days Monday to Saturday, except the Nordvik holidays; Sundays and holidays never
HOLIDAYS = ["2026-10-16", "2026-11-02", "2026-11-21", "2026-12-08", "2026-12-24", "2026-12-25", "2026-12-26", "2026-12-31"]
BWD = [0, 1, 2, 3, 4, 5]
WEEKDAY_RULE = "first_after"   # R22
BYE = "Thank you for your time. Goodbye from Nordvik Savings Bank."                                   # R48
BYE_T = "Thank you for your time, {{title}} {{last_name}}. Goodbye from Nordvik Savings Bank."        # R17 + R48
ROBOT = "I am an automated assistant of Nordvik Savings Bank, and this conversation is recorded."     # R4 verbatim
SCAM = "You may hang up and call the number on the back of your card or on your latest statement to confirm this call."  # R44
REDUCTION = "I cannot offer any reduction, and the figures are those on the account."                # R34
OPENING_LINE = "Good day, this is the virtual assistant of Nordvik Savings Bank, and this call is recorded."  # R1 verbatim
ASK_NAME = "Am I speaking with {{first_name}} {{last_name}}?"                                          # R2

nodes = {}

# ---------------------------------------------------------------- payment policy (sections 7-10)
POLICY = pol.Policy(
    HOLIDAYS,
    texts={
        "question": "Can you pay [amount] [when]?",                                                   # R31 attempts (the assistant proposes every figure, R25)
        "weekend_or_holiday": "[named] is not a business day. The next business day is [date].",     # R21
        "after_deadline": "The latest date the bank can record is [deadline].",                       # R24
        "before_today": "[named] has already passed.",                                                # R20 (today or later)
        "below_floor": "The smallest amount the bank can record is [floor].",                         # R28
        "above_full": "The full overdue amount is [full], so [named] is more than is overdue. I will record [full], the full amount.",  # R28 above the full amount
        "vague": "Which exact day would that be?",                                                    # R23
        "vague_deadline": "The latest date the bank can record is [deadline].",                       # unused (vague_again='refuse')
        "too_much_floor": "I understand. I can propose [floor]. The remainder stays overdue, and the account stays in arrears until it is cleared.",  # R27
        "exhausted": "I understand.",                                                                 # R32
        "hardship": "I am sorry to hear that. I will not ask you for a payment today. The bank's care team can review your situation. May I connect you with them now?",  # R33
        "paid": "Thank you for letting me know. The bank will check for the payment within two business days and will not call you again before then.",  # R40
        "dispute": "I understand. A colleague will look into it.",                                    # R41
        "human_first": "I will connect you with a colleague now.",                                    # R43 (human_limit=1: never asked first)
        "notalk_first": "I understand.",                                                              # R46 (notalk_limit=1: never insists)
        "readback_head": "To confirm: ",                                                              # R35
        "readback_item": "[amount] [when] for your [words]",
        "readback_tail": ". Shall I record this?",
        "recorded": "I have noted your promise. A confirmation will be sent to your registered email address.",  # R39 verbatim (one sentence pair)
        "rec_failed": "The promise for your [words] could not be saved.",                             # R38
        "anything_else": "Is there anything else I can help you with?",
        "wrap_change": "A recorded promise is not changed or cancelled during this call. The payments line can change it.",  # R37
    },
    multi=False, notes=False,                     # R1 one product; R47 Brief C never calls add_note
    fin_keys={"promise": "promise", "paid": "paid", "default": "declined_offer", "refused": "declined_offer",
              "hardship": "financial_distress", "dispute": "contested_xfer", "service_error": "system_fault"},
    fail_max=3,                                   # R38: the first call and up to two more
    max_checks=6,                                 # loop exit: offers and read-back changes per product
    human_limit=1,                                # R43: transfer at once, never ask first
    notalk_limit=1,                               # R46: do not insist, end at once
    closed_day_move="after",                      # R21: the next business day
    business_weekdays=BWD,
    weekday_rule=WEEKDAY_RULE,                    # R22
    vague_again="refuse",                         # R23: no exact day after one ask = a non-answer (one attempt)
    above_full="agree",                           # R28: above the full amount, record the full amount and say so
    promise_reasons={"full": "full", "partial": "partial"},   # R47
    targets={"xfer_restructuring": "plan_offer"},             # R42: ask whether to connect first
    asides={   # R4, R44, R34: side questions answered before continuing, even on a turn that goes through code into a tts line
        "robot": {"when": "asks whether they are talking to a robot, an AI or a machine", "say": ROBOT},
        "scam": {"when": "asks whether this call is a scam or genuine", "say": SCAM},
        "reduction": {"when": "asks for a discount, a waiver, a fee reversal or a reduction of the amount", "say": REDUCTION},
    })

# ---------------------------------------------------------------- terminals (R47 table; R48 goodbye)
# Every fin node runs POLICY.ending_code: a promise recorded earlier in the call decides the ending (R47).
FINS = {
    "promise": ("promise", "full", BYE_T),                                                              # reason from the core (full/partial)
    "paid": ("paid", "self_reported", "Thank you for letting me know. The bank will check for the payment within two business days and will not call you again before then. " + BYE_T),  # R40
    "declined_offer": ("no_promise", "declined_offer", "I understand. " + BYE_T),                       # R32, R42, R46
    "financial_distress": ("no_promise", "financial_distress", "I understand. The care team will contact you within three business days. " + BYE_T),  # R33
    "system_fault": ("no_promise", "system_fault", "I am sorry, the promise could not be saved. " + BYE_T),  # R38
    "plan_review": ("transferred", "plan_review", "Thank you. A colleague from the plan review team will take over now. " + BYE_T),  # R42
    "agent_request": ("transferred", "agent_request", "A colleague will take over now. " + BYE),         # R43 (before or after the check)
    "care_team": ("transferred", "care_team", "Thank you. A colleague from the care team will take over now. " + BYE_T),  # R33
    "contested": ("transferred", "contested", "A colleague will take over now. " + BYE_T),              # R41
    "exhausted": ("not_verified", "exhausted", "I am sorry, the security check could not be completed. A colleague can complete the check if you call the number on the back of your card or on your latest statement. " + BYE),  # R15
    "withheld": ("not_verified", "withheld", "I understand. The bank cannot discuss anything until the security check is complete. " + BYE),  # R16, R46
    "scheduled": ("not_reached", "scheduled", "Thank you, we will call back then. " + BYE),              # R6
    "no_slot": ("not_reached", "no_slot", "I understand, I will not book a callback. " + BYE),           # R7
    "wrong_party": ("not_reached", "wrong_party", "I apologise for the disturbance. " + BYE),            # R8
    "estate": ("not_reached", "estate", "Please accept my condolences. " + BYE),                         # R9: ask nothing further
    "unconfirmed": ("not_reached", "unconfirmed", "I am sorry, I could not confirm who I am speaking with. " + BYE),  # R3
}
for key, (outcome, reason, farewell) in FINS.items():
    POLICY.end_pair(key, outcome, reason, farewell, nodes)

# transfers (api_request, engine-run): R42 restructuring, R33 support, R43 general, R41 general
for name, q, fin, line in [
        ("xfer_plan", "restructuring", "fin_plan_review", "I will connect you with the plan review team now."),
        ("xfer_support", "support", "fin_care_team", "I will connect you with the care team now."),
        ("xfer_general", "general", "fin_agent_request", "I will connect you with a colleague now."),
        ("fin_contested_xfer", "general", "fin_contested", "I understand. A colleague will look into it. I will connect you now.")]:
    nodes[name] = fl.api_node(name, fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1),
                              [fl.always(fin)], on_enter={"type": "tts", "text": line})

# ---------------------------------------------------------------- setup: dates, callback window
# R6: a callback slot today or on one of the next two business days, 09:00 to 18:00 inclusive, later than now
CALLBACK = {"open": "09:00", "close": "18:00", "same_day": True, "days_ahead": 2}
# R47/R46: every call ends with one close_call; a hang-up before any ending still needs a valid outcome and reason:
# before the check = the person did not stay for it (R46 withheld once the customer confirmed, else R3 unconfirmed);
# prepare moves it to no_promise / declined_offer (R46 after the check).
DEFAULT_OUTCOME = r'''
if str(vars.get('who1') or '') == 'customer':
    vars['outcome'] = 'not_verified'
    vars['reason'] = 'withheld'
else:
    vars['outcome'] = 'not_reached'
    vars['reason'] = 'unconfirmed'
'''
SETUP = fl.SETUP_CODE(HOLIDAYS, BWD, callback_rule=CALLBACK, weekday_rule=WEEKDAY_RULE, extra=DEFAULT_OUTCOME)

# ---------------------------------------------------------------- opening (R1-R4, R43, R46)
WHO_VALUES = ["customer", "someone_else", "wrong_number", "deceased", "refuses", "wants_agent", "unclear"]
WHO_DESC = ("Who answered, judged ONLY from the person's latest message. "
            "customer = ONLY 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} {{last_name}}). "
            "someone_else = another person answered (a relative, partner, colleague), or says the customer is not here / not available, or offers to take a message. "
            "wrong_number = says this number does not belong to that person / they do not know them. "
            "deceased = says the customer has died / passed away. "
            "refuses = says they do not want to talk or wants to end the call. "
            "wants_agent = asks to speak to a person, a human, an agent. "
            "unclear = anything else: 'hello', 'go ahead', 'who's calling?', 'what is this about?', 'is this a robot?', 'is this a scam?', any question, silence.")
ROUTES = [
    ("customer", "ask_phone", "the customer confirmed who they are"),
    ("deceased", "fin_estate", "the customer has died"),
    ("wrong_number", "fin_wrong_party", "wrong number"),
    ("someone_else", "third_party", "someone else answered"),
    ("refuses", "fin_withheld", "does not want to talk (R46, before the check)"),
    ("wants_agent", "xfer_general", "asks for a person (R43)"),
]
# the chat route answers the first customer line with the dialogue model instead of the tts: opening_conv repeats it
nodes["opening"] = fl.opening_conv(
    "opening", OPENING_LINE + " " + ASK_NAME,
    "you have just introduced yourself and asked whether you are speaking with {{first_name}} {{last_name}}. Do not call any tool in this turn. Do not say why you are calling.",
    [fl.ext("who1", WHO_VALUES, WHO_DESC)])
INITIAL = fl.conversation_first("opening", SETUP, "who1", ROUTES, "opening_retry", nodes)

nodes["opening_retry"] = fl.conv(
    "opening_retry",
    "You called {{first_name}} {{last_name}} and asked whether you are speaking with them, but the answer did not confirm it. "
    "No tool call is allowed in this turn. Do not say why you are calling. Do not use the words overdue, arrears, collections, payment or debt, and do not name any product.\n"
    "If the person asked a question, answer it briefly first: "
    "a robot, an AI or a machine -> say exactly \"" + ROBOT + "\"; "
    "a scam -> say exactly \"" + SCAM + "\"; "
    "who is calling -> the virtual assistant of Nordvik Savings Bank; what it is about -> you can discuss it only with {{first_name}} {{last_name}} personally.\n"
    "Then ask exactly: \"" + ASK_NAME + "\" This is the second and last time you ask.",
    extraction=[fl.ext("who2", WHO_VALUES, WHO_DESC)],
    transitions=[fl.eq("who2", v, t, d) for v, t, d in ROUTES] + [fl.always("fin_unconfirmed")])  # R3

# ---------------------------------------------------------------- third party (R5-R10)
cb_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book a callback for the customer. CALL it as soon as the person names a day and time inside the allowed window.",
    field_descriptions={"date": "Callback date as YYYY-MM-DD. Must be one of the allowed days listed.",
                        "time": "Callback time as HH:MM, 24 hour, from 09:00 to 18:00 inclusive, later than now."},
    pre=fl.normalise_pre({"time": "time"}),
    post=fl.ok_post("Callback booked.", "The booking failed. Try schedule_callback once more with the same values."))

nodes["third_party"] = fl.conv(
    "third_party",
    "You called for {{first_name}} {{last_name}} but someone else is on the line.\n"
    "STRICT: Say only that you are calling from Nordvik Savings Bank on a private matter that you can discuss with the customer personally. "
    "Never say what the matter is, not even in general terms. Never use the words overdue, arrears, collections, payment or debt, never name a product or an amount. "
    "If they ask what it is about, offer to pay, or offer to take a message, repeat that you can discuss it only with the customer. Never ask them a security question and arrange nothing with them except a callback.\n"
    "Your only job: ask when {{first_name}} {{last_name}} can be reached, then book a callback.\n"
    "Now: {{today_text}}, {{now_time}}.\n{{callback_text}}\n"
    "- If they give a day and time inside the window, call schedule_callback with date YYYY-MM-DD (from the list above) and time HH:MM. 'Tomorrow morning around eleven' means tomorrow at 11:00; 'four o'clock this afternoon' means today at 16:00. If they give only a day, ask for a time; if only a vague time like 'morning', propose a precise time such as 10:00 and ask if it suits.\n"
    "- If the day or time is outside the window, state the window (today later than now, or the next two business days, from 09:00 to 18:00) and ask once for another slot.\n"
    "- If the second slot is also outside the window, or they cannot say when, book nothing: call transition_to_fin_no_slot.\n"
    "- If they ask whether you are a robot: say exactly \"" + ROBOT + "\"\n"
    "After every tool result, speak or call the next tool.",
    tools=[cb_tool],
    extraction=[fl.ext("tp_status", ["none", "wrong_number", "deceased"],
                       "From the person's latest message: wrong_number if they say this number does not belong to the customer or they do not know the customer; deceased if they say the customer has died; otherwise none.")],
    transitions=[
        fl.ok_true("schedule_callback", "fin_scheduled", "callback booked"),
        fl.eq("tp_status", "deceased", "fin_estate", "customer died"),
        fl.eq("tp_status", "wrong_number", "fin_wrong_party", "wrong number"),
        fl.intent_tool("fin_no_slot",
                       "No callback can be booked: the person gave a second slot outside the allowed window, or cannot say when the customer is reachable.",
                       "No callback can be booked inside the allowed window"),
    ])

# ---------------------------------------------------------------- identity (R11-R16)
Q_PHONE = "What are the last four digits of the mobile number registered with the bank?"
Q_DOB = "What is your date of birth?"
SWAP = "Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month said as a word, for example 14 March 1988."  # R14
LIMIT = ("Two wrong answers: the check has ended. Do not ask again and reveal no amount, product or reason for the call. "
         "Tell the customer a colleague can complete the check if they call the number on the back of their card or on their latest statement.")  # R13, R15
SERVICE_LEFT_AT_LIMIT = "1"   # R13 two wrong answers; the service allows three (wrong_answers_left 3 -> 1 after two): fallback route
WRONG = "Wrong answer. Tell the customer it does not match our records and ask the same question again: {question}"


def verify_tool(field, question, desc, answer_desc, verified_text):
    return fl.api_tool(API, "verify_identity", baked={"field": field}, description=desc,
                       field_descriptions={"answer": answer_desc},
                       pre=fl.reset_pre(["question_count_" + ("phone" if field == "phone_last4" else "dob")]) +
                       fl.normalise_pre({"answer": "answer"}, date_order="none"),   # R12: no numbers-only order: ask for the month as a word
                       post=fl.verify_count_post(question, 2, {"day_month_swapped": SWAP}, LIMIT,
                                                 free_hints={"day_month_swapped": 1},  # R14: one free retry per call
                                                 all_verified_text="Both security questions passed. Identity is verified.",
                                                 verified_text=verified_text, wrong_text=WRONG))


ID_COMMON = ("Rules for this step:\n"
             "- Until both questions pass, do not use the words overdue, arrears, collections, payment or debt, and name no product or amount.\n"
             "- If the customer refuses to answer, or asks what the call is about instead of answering: say that the bank cannot discuss anything until the security check is complete, and ask the question again.\n"
             "- If the customer asks another question (who is calling, why you need it): answer it in one short sentence, then ask the question again. "
             "Robot, AI or machine -> say exactly \"" + ROBOT + "\". Scam -> say exactly \"" + SCAM + "\"\n"
             "- " + fl.latest_value_note(4) + "\n"
             "- After every tool result, speak to the customer or call the next tool. Follow what_to_do_next.")
# R16: refusing, or asking what the call is about instead of answering, is the brief's refusal/deflection (counted);
# any other question back is answered (R3/R4/R44) and is not counted. fl.QUESTION_ENUM_CLAUSE lists 'what this is about'
# as a non-counting question, which Brief C counts: the question value is described here instead.
REFUSAL_DESC = ("From the customer's LATEST message only. "
                "refused = they refuse to answer the security question, OR they ask what the call is about (or how much they owe) instead of answering it. "
                "end_call = they say they do not want to talk or want to end the call. "
                "human = they ask to speak to a person, a human, an agent. "
                "question = they ask something else back instead of answering (who is calling, why you need it, is this a robot, is this a scam) without refusing. "
                "none = they give an answer or say anything else." + fl.REFUSAL_NONE_CLAUSE)
REFUSAL_VALUES = ["none", "refused", "end_call", "human", "question"]

nodes["ask_phone"] = fl.conv(
    "ask_phone",
    "The person confirmed they are {{first_name}} {{last_name}}. Check identity with two security questions, one at a time. Ask the first now: \"" + Q_PHONE + "\"\n"
    "When they give four digits, call verify_identity with answer = the four digits only. Do not ask the date of birth before this question has passed.\n" + ID_COMMON,
    tools=[verify_tool("phone_last4", Q_PHONE, "Check the last four digits of the registered mobile number. CALL it every time the customer gives four digits.",
                       "Exactly four digits.", "Correct. Now ask the second security question: " + Q_DOB)],
    extraction=[fl.ext("refusal_phone", REFUSAL_VALUES, REFUSAL_DESC)],
    transitions=[
        fl.eq("id_route", "exhausted", "fin_exhausted", "two wrong answers"),
        fl.tr("fin_exhausted", "two wrong answers (service counter, no swapped hint so far)",
              fl.and_group(fl.cond("verify_identity_response.data.wrong_answers_left", "equals", SERVICE_LEFT_AT_LIMIT),
                           fl.cond("hint_day_month_swapped", "is_not_set"))),
        fl.is_true("verify_identity_response.data.verified", "ask_dob", "phone digits correct"),
        fl.eq("refusal_phone", "human", "xfer_general", "asks for a person (R43)"),
        fl.eq("refusal_phone", "end_call", "fin_withheld", "wants to end the call (R46)"),
        fl.eq("refusal_phone", "refused", "count_decline_phone", "refuses or deflects (R16)"),
        fl.eq("refusal_phone", "question", "qb_phone", "asks another question back"),
    ])

nodes["ask_dob"] = fl.conv(
    "ask_dob",
    "The mobile digits were correct. Ask the second security question now: \"" + Q_DOB + "\"\n"
    "Call verify_identity with the date as YYYY-MM-DD. If the customer gives the date ONLY in numbers (for example 3/7/85), do not call the tool: ask them to say the month as a word, then call it. "
    "If they give only part of the date, ask for the rest before calling the tool.\n" + ID_COMMON,
    tools=[verify_tool("date_of_birth", Q_DOB, "Check the date of birth. CALL it every time the customer gives a full date of birth with the month as a word.",
                       "The date of birth as YYYY-MM-DD.", "Both security questions passed. Identity is verified.")],
    extraction=[fl.ext("refusal_dob", REFUSAL_VALUES, REFUSAL_DESC)],
    transitions=[
        fl.is_true("verify_identity_response.data.all_verified", "load_account", "identity verified"),
        fl.eq("id_route", "exhausted", "fin_exhausted", "two wrong answers"),
        fl.tr("fin_exhausted", "two wrong answers (service counter, no swapped hint so far)",
              fl.and_group(fl.cond("verify_identity_response.data.wrong_answers_left", "equals", SERVICE_LEFT_AT_LIMIT),
                           fl.cond("hint_day_month_swapped", "is_not_set"))),
        fl.eq("refusal_dob", "human", "xfer_general", "asks for a person (R43)"),
        fl.eq("refusal_dob", "end_call", "fin_withheld", "wants to end the call (R46)"),
        fl.eq("refusal_dob", "refused", "count_decline_dob", "refuses or deflects (R16)"),
        fl.eq("refusal_dob", "question", "qb_dob", "asks another question back"),
    ])

for stage in ["phone", "dob"]:
    # R16: the second refusal or deflection closes withheld (counted across both questions)
    code = fl.counter_code("decline_count", 2, "decline_route", reset={"refusal_dob": "none", "refusal_phone": "none"})
    nodes[f"count_decline_{stage}"] = fl.code_node(f"count_decline_{stage}", code, [
        fl.eq("decline_route", "close", "fin_withheld", "second refusal"), fl.always(f"ask_{stage}")])
    # R3/R4/R44: other questions are answered, never counted as refusals; three in a row without an answer = withheld
    nodes[f"qb_{stage}"] = fl.question_back_node(stage, f"ask_{stage}", "fin_withheld", limit=3)

# ---------------------------------------------------------------- account and statement (R17, R18, R26, R19, R31)
PREPARE_BODY = fl.products_from_vars() + r'''
import math
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
p = prods[0] if prods else {}
if not isinstance(p, dict):
    p = {}
ptype = str(p.get('type') or '')
pid = str(p.get('product_id') or 'p1')
past_due = float(p.get('past_due') or 0)
if ptype == 'credit_card':
    words = 'credit card ending in ' + str(p.get('card_last4') or '')
    floor = float(math.ceil(round(past_due * 0.4, 2) - 1e-9))   # R26: 40%, rounded up to the next whole unit
elif ptype == 'car_loan':
    words = 'car loan'
    floor = float(math.ceil(float(p.get('instalment_amount') or past_due) - 1e-9))   # R26: the instalment, stated in whole units
else:
    words = 'personal loan' if ptype == 'personal_loan' else (ptype.replace('_', ' ') or 'loan')
    floor = float(math.ceil(float(p.get('instalment_amount') or past_due) - 1e-9))
if floor > past_due:
    floor = past_due
days_late = int(float(p.get('days_late') or 0))
a1 = addbd(today, 1)                       # R31 attempt 1: the next business day after today
if days_late <= 10:                        # R19 green: the 9th business day after today, 2 attempts
    deadline = addbd(today, 9)
    rungs = [('full_or_floor', a1), ('floor', deadline)]   # R31 attempt 2 (green only): the floor on the deadline
else:                                      # R19 amber: the 4th business day after today, 1 attempt
    deadline = addbd(today, 4)
    rungs = [('full_or_floor', a1)]
register_product(vars, pid, words, past_due, floor, 'floor', deadline, rungs)
vars['outcome'] = 'no_promise'             # R46: a hang-up after the check closes no_promise / declined_offer
vars['reason'] = 'declined_offer'
vars['product_id'] = pid
vars['product_words'] = words
vars['past_due_fmt'] = fmt(past_due)
vars['days_late_txt'] = str(days_late)
vars['deadline_text'] = txt_short(deadline)
statement = ('Thank you, ' + str(vars.get('title') or '') + ' ' + str(vars.get('last_name') or '') + '. I am calling from the payments team of Nordvik Savings Bank about an overdue amount on your '
             + words + '. The overdue amount is ' + fmt(past_due) + ', and it is ' + str(days_late) + ' days overdue. Are you able to settle the full overdue amount today?')   # R18, R29
'''
PREPARE = POLICY.prepare_code(PREPARE_BODY, "statement", fallbacks={
    "say_next": "Thank you. I am calling from the payments team of Nordvik Savings Bank about an overdue amount. Are you able to settle the full overdue amount today?",
    "product_words": "account", "past_due_fmt": "the overdue amount", "days_late_txt": "", "deadline_text": ""})

nodes["load_account"] = fl.api_node(
    "load_account", fl.api_tool(API, "get_account", description="Get the overdue product.", retries=2),
    [fl.always("prepare")], mapping=[{"path": "data.products", "variable": "products"}])
nodes["prepare"] = fl.code_node("prepare", PREPARE, [fl.always("negotiate")])

# ---- extraction, in the brief's own terms
TOPIC_DESC = ("What the customer's LATEST message says, if it is one of these. "
              "hardship = mentions illness, a bereavement, job loss or a similar hardship (this wins over every other value, even when they also name a date or an amount). "
              "already_paid = says they have ALREADY paid this overdue amount (not 'I will pay'). "
              "dispute = says 'this is not my debt', they never had this product, or the product was closed or settled in the past. "
              "new_plan = asks for a new payment plan, lower instalments, or spreading the amount over several months. Saying the amount is too much is NOT new_plan; a different amount or date for this payment is NOT new_plan." + fl.PLAN_REQUEST_CLAUSE + " "
              "human = asks to speak to a person, a human, an agent or a colleague. "
              "no_talk = says they do not want to talk or want to end the call (not a refusal to pay). "
              "none = anything else: offers, yes or no answers, refusals to pay, questions.")
STANCE_DESC = ("The customer's answer to the agent's LATEST payment proposal, from the customer's latest message only. "
               "accept = agrees to exactly what the agent proposed ('yes', 'okay', 'fine', 'that works', 'I can do that'). "
               "refuse = a flat refusal: a no to paying with no date and no amount ('no', 'I can't', 'not today', 'I won't'), declining the proposal, or a non-answer that avoids the question ('I don't know', 'maybe', 'you tell me'). "
               "too_much = says the full amount is too much, too high, or that they cannot pay all of it, without naming an amount. "
               "offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. "
               "other = anything else: a question, small talk, a request.")
KIND_DESC = ("From the customer's LATEST message only. exact = they name a specific payment day (a date, a weekday, 'tomorrow', 'the 26th', 'Monday the 26th') or a specific amount of money, or both. "
             "vague = only a vague period without a day ('next week', 'the week after next', 'after payday', 'end of the month', 'when my salary comes'), or they say they cannot say which day. "
             "none = no date, amount or period in the latest message (also 'yes', 'no', questions).")
DATE_DESC = ("The payment date the customer names in their LATEST message. 'this <weekday>' and 'next <weekday>' both mean the FIRST such weekday after today. "
             "Leave it empty when the latest message names no specific day.")
AMOUNT_DESC = ("The amount of money the customer offers to pay in their LATEST message, as a number ('three hundred and twenty' = 320, 'a hundred' = 100). "
               "Leave it empty when the latest message names no amount. A day of the month is not an amount.")
CONFIRM_DESC = ("The customer's answer to the read-back question 'Shall I record this?', from their latest message only. "
                "yes = a clear yes ('yes', 'correct', 'please do', 'go ahead', 'that's right'). "
                "change = they give a different amount or a different date for this promise ('make it 200 instead', 'actually Monday'). "
                "no = a plain no without a new amount or date. "
                "other = anything else, for example a question.")

topic = fl.ext("topic", ["none", "hardship", "already_paid", "dispute", "new_plan", "human", "no_talk"], TOPIC_DESC)
TOPIC_TRS = POLICY.topic_transitions(values={"hardship": "pol_hardship", "new_plan": "plan_offer", "human": "pol_human",
                                             "no_talk": "pol_notalk", "already_paid": "pol_paid", "dispute": "pol_dispute"})

FACTS = ("FACTS\n- Product: {{product_words}}. Overdue amount: {{past_due_fmt}}. Days overdue: {{days_late_txt}}.\n"
         "- Today: {{today_text}}. The latest date the bank can record: {{deadline_text}}.\n")
COMMON = ("- If asked whether you are a robot, an AI or a machine: say exactly \"" + ROBOT + "\" Never claim to be a person. If asked whether this is a scam: say \"" + SCAM + "\"\n"
          "- Never offer or agree to a discount, a waiver, a fee reversal, an instalment plan or any date later than the latest date. If asked for one, say \"" + REDUCTION + "\"\n"
          "- A question these facts do not answer: say you do not have that information and that the payments team can answer it. Never invent a figure, a date or a reason.\n"
          "- No tool call is allowed here. Never say that a promise is noted or recorded.\n")

NEGOTIATE = ("You are talking with {{title}} {{last_name}}, who is verified, about the overdue amount. The line you just said and the offer in STATE were decided by the system from the bank's rules.\n"
             "- Never propose, compute or change an amount or a date yourself, and never ask what they can pay or how much they can afford. The only offer you may make is the current offer in STATE, word for word.\n"
             "- If the customer asks a question or says something else, answer it in one short sentence, then ask the current offer again.\n"
             + COMMON + FACTS)
neg_ext = [topic, POLICY.stance_extraction(STANCE_DESC)] + POLICY.offer_extraction(DATE_DESC, AMOUNT_DESC, KIND_DESC)
neg_trs = TOPIC_TRS + POLICY.offer_guard_transitions() + POLICY.stance_transitions()
nodes["negotiate"] = POLICY.negotiate_node(NEGOTIATE, neg_ext, neg_trs)

CONFIRM = ("You read back the promise and asked \"Shall I record this?\". The promise is recorded only after a clear yes.\n"
           "- If the customer asks something, answer it in one short sentence, then ask again: \"Shall I record this?\".\n"
           + COMMON + FACTS)
nodes["confirm"] = POLICY.confirm_node(CONFIRM, CONFIRM_DESC, DATE_DESC, AMOUNT_DESC, topic_entry=topic, topic_trs=TOPIC_TRS)

HS_ANSWER_DESC = ("From the customer's LATEST message. support_yes = they want to be connected with the care team. "
                  "support_no = they do not want to be connected, say no to that offer, or say they cannot pay and want nothing more. "
                  "accept_offer = they agree to the date and amount the agent just proposed. "
                  "human = they ask to speak to a person, a human or an agent (not the care team). "
                  "none = anything else, for example a question or a request for a discount.")
HARDSHIP = ("The customer mentioned a hardship (illness, a bereavement, job loss or similar). You said \"I am sorry to hear that. I will not ask you for a payment today.\" and asked whether you may connect them with the bank's care team now.\n"
            "- Make NO persuasion attempt. Never propose an amount or a date yourself.\n"
            "- If they ask a question or for a discount, answer in one short sentence, then ask whether you may connect them with the care team now.\n"
            + COMMON + FACTS)
nodes["hardship"] = POLICY.hardship_node(HARDSHIP, HS_ANSWER_DESC, KIND_DESC, DATE_DESC, AMOUNT_DESC, human=True)   # R43 applies during hardship too

WRAP_DESC = ("From the customer's LATEST message, after the agent said the promise is noted and asked whether there is anything else. "
             "done = nothing else ('no', 'that's all', 'thanks', 'goodbye'). "
             "human = asks to speak to a person, a human or an agent. "
             "new_plan = asks for a new payment plan or lower instalments. "
             "change = asks to change, move or cancel the promise just recorded (another date or amount). "
             "question = asks a question. other = anything else.")
WRAPUP = ("The promise is noted (STATE). You said so and asked whether there is anything else.\n"
          "- If the customer asks a question, answer it in one or two sentences from these facts or say you do not have that information and that the payments team can answer it, then ask whether there is anything else.\n"
          "- A recorded promise is not changed or cancelled during this call; the payments line can change it.\n"
          + COMMON + FACTS)
nodes["wrapup"] = POLICY.wrapup_node(WRAPUP, WRAP_DESC)

POLICY.add_event_nodes(nodes)
POLICY.record_nodes(nodes, API)

# R42: a plan request: describe no plan, ask whether to connect; yes -> restructuring, no -> declined_offer
nodes["plan_offer"] = fl.conv(
    "plan_offer",
    "The customer asked for a new payment plan, lower instalments or spreading the amount. You said the plan review team handles these requests and asked whether you may connect them now. "
    "Do not describe or invent any plan, and propose no amount or date. If they did not answer the question, answer in one short sentence and ask it again. No tool call is allowed here.",
    on_enter={"type": "tts", "text": "The plan review team handles these requests. May I connect you with them now?"},
    extraction=[fl.ext("plan_choice", ["none", "accept", "decline"],
                       "Answer to the offer to connect with the plan review team, from the customer's LATEST message: accept if they want to be connected, decline if they say no or do not want to be transferred, none otherwise."),
                fl.ext("plan_human", ["no", "yes"], "yes if the customer's LATEST message asks to speak to a person, a human or an agent; otherwise no.")],
    transitions=[
        fl.eq("plan_choice", "accept", "xfer_plan", "accepts the plan review team"),
        fl.eq("plan_human", "yes", "xfer_general", "asks for a person (R43)"),
        fl.eq("plan_choice", "decline", "fin_declined_offer", "declines the transfer"),
    ])

# ---------------------------------------------------------------- close_call lifecycle (R47)
close_call = fl.close_call_tool(
    API,
    outcome_desc="promise: a promise was recorded. paid: says already paid. transferred: handed to a person. no_promise: verified, no promise. not_verified: identity not passed. not_reached: the customer was not reached.",
    reason_desc="promise: full|partial. paid: self_reported. transferred: plan_review|agent_request|care_team|contested. no_promise: declined_offer|financial_distress|system_fault. "
                "not_verified: exhausted|withheld. not_reached: scheduled|no_slot|wrong_party|estate|unconfirmed.")

SYSTEM = ("You are the virtual assistant of Nordvik Savings Bank on an outbound phone call to {{first_name}} {{last_name}}. Speak English. Keep every turn to one or two short sentences. "
          "After the security check, address the customer as {{title}} {{last_name}}.\n"
          "Always:\n"
          "- Until the security check is complete, never use the words overdue, arrears, collections, payment or debt, and never name a product, to anyone. The word collections is never used.\n"
          "- If asked whether you are a robot, an AI or a machine: say exactly \"" + ROBOT + "\" and carry on. Never claim to be a person.\n"
          "- If asked whether this is a scam: say \"" + SCAM + "\", then continue.\n"
          "- Never invent a figure, a date or a reason. If you do not have the information, say so and that the payments team can answer it.\n"
          "- Never offer a discount, waiver, fee reversal, instalment plan or any term you were not given.\n"
          "- Do not say goodbye or end the call yourself: the call is closed for you.\n"
          "- Call at most one tool per message. When a rule says to call a tool, call it: saying it is not enough.\n"
          "- After every tool result, speak to the customer or call the next tool. Never end a turn with nothing. Follow what_to_do_next in a tool result.\n"
          "- Say amounts as plain numbers, for example 420.50, and dates as weekday, day and month, for example Thursday 15 October.")

wf = fl.assemble(INITIAL, nodes, SYSTEM, [close_call], conduct=True)   # no test_variables (CLAUDE.md); conduct = how customers talk

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out/brief-c_v3.workflow.json"
    fl.write_workflow(wf, out)
    print("nodes:", len(nodes), "->", out)
