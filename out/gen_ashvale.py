"""Ashvale Bank generator (brief: ashvale.md, a mailbox export): policy as code on builder/policy.py.
Structure: out/gen_brief-b_v3.py (one to three products, notes); every value and sentence from the brief, `# Rn` = rule
number in out/ashvale.rules.md. Rules in force = the latest dated decision: late band latest date = 5th business day
(message 2.4, from 12 Oct), card floor = half the overdue balance or the minimum payment if higher (message 2.3),
callbacks today or the next two business days 08:30-17:00 (message 4.2), create_promise one try (message 4.2),
second wrong answer in total ends the check (message 5.1), hardship stays with the assistant: letter sentence, hardship
notes, VUL (message 5.1). Outcome codes from the dialler list v5."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

API = fl.load_api(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools/openapi.json")
SPEC = json.load(open(ROOT / "out/ashvale.spec.json"))["spec"]
HOLIDAYS = [h["date"] for h in SPEC["calendar"]["holidays"]]            # R01 thread 1
BWD = [0, 1, 2, 3, 4]                                                     # R33 Monday to Friday
WEEKDAY_RULE = "first_after_plus7"                                        # R39: 'Friday'/'this Friday' = first after today; 'next Friday' = +7
MAX_WRONG = SPEC["max_wrong_answers"]                                     # R80: 2 in total
CB = SPEC["callback"]                                                     # R76: 08:30-17:00, today or next two business days

BANK = "Ashvale Bank"
OPENING_LINE = "Hello, this is the automated assistant from Ashvale Bank. This call is recorded for quality and security."   # R07 verbatim
ASK_NAME = "May I speak with {{title}} {{last_name}}, please?"           # R07 verbatim
ROBOT = "Yes, I'm Ashvale Bank's automated assistant."                   # R11 verbatim
SCAM = "You can hang up and ring the number on the back of your card or on your statement."   # R12
PRIVATE = "I'm calling about a private matter for {{title}} {{last_name}}."   # R14 verbatim
NO_INFO = "I'm afraid I don't have that information."                    # R59 verbatim
BYE = "Thank you for your time. Goodbye."                                 # R65: thank them and say goodbye
BYE_T = "Thank you for your time, {{title}} {{last_name}}. Goodbye."

nodes = {}
NOTE_ENUM = fl.tool_spec(API, "add_note")["fields"]["reason"]["enum"]

# ---------------------------------------------------------------- payment policy (R29-R64, R68-R70, R78, R81)
POLICY = pol.Policy(
    HOLIDAYS,
    texts={
        "question": "Would you be able to pay [amount] [when]?",                                  # R30: the assistant proposes every amount
        "today_when": "today, [date]",
        "tomorrow_when": "tomorrow, [date]",
        "question_product": "For your [words], would you be able to pay [amount] [when]?",      # R60 one by one
        "question_all": "Would you be able to pay all of these in full today?",                 # R29 verbatim
        "weekend_or_holiday": "[named] is not a business day, so I can't log it. The next business day after it is [date].",   # R35
        "after_deadline": "[deadline] is the last day we can log for your [words].",            # R36
        "before_today": "[named] has already passed, so I need a day from today onwards.",      # R37
        "below_floor": "I can't log [named]. The smallest amount I can log is [floor].",         # R41
        "above_full": "The full overdue amount is [full], so I will log [full].",                # R40 more than the full amount: log the full amount
        "above_full_again": "The full overdue amount is [full], so I will log [full].",
        "vague": "Which exact day would that be?",                                               # R38 ask once for the exact day
        "vague_deadline": "The latest date we can log for your [words] is [deadline].",         # R38 then propose the latest date
        "too_much_floor": "I understand. I can log [floor]. The rest of the balance stays overdue.",   # R42 verbatim sentence
        "exhausted": "I understand.",                                                            # R45
        "one_by_one": "Let's go through them one at a time.",                                   # R60
        "next_product": "Next, your [words].",
        "paid": "Thank you for letting me know. Payments can take up to two business days to show on your account with us.",   # R54 verbatim
        "dispute": "Thank you for telling me. I won't log anything for your [words].",          # R55 don't argue
        "hardship": "I'm sorry you're going through that. Our Financial Support team will write to you within five working days.",   # R81 verbatim (both)
        "human_first": "Is there anything I can help you with myself first?",                   # R57 ask once whether the assistant can help
        "notalk_first": "I understand. This will only take a moment.",                          # R58 twice
        "readback_head": "To confirm: your ",                                                    # R49, R62 one read-back for everything
        "readback_item": "[words], [amount], [when]",
        "readback_sep": "; your ",
        "own_deadline": ", which is the latest date we can log for it",                         # R61
        "moved_bd": ", the next business day",
        "readback_tail": ". Shall I go ahead and log that?",                                    # R49 verbatim
        "recorded": "That's logged.",                                                            # R52 only after ok true
        "recorded_many": "Those are logged for your [list].",
        "after_recorded": "You'll receive a text message confirming this arrangement today.",   # R53 verbatim, once per call
        "rec_failed": "I'm sorry, I couldn't confirm that arrangement on this call. Our team will be in touch with you about it.",   # R78 verbatim
        "anything_else": "Is there anything else I can help you with?",
        "wrap_change": "Once it's logged it can't be changed or cancelled on this call, but you can change it in the Ashvale mobile app.",   # R51
    },
    multi=True,                                                 # R04: one to three products
    notes=True,                                                 # R63: a note per product without a promise
    note_reasons={s: s for s in ("refused", "hardship", "dispute", "paid", "service_error") if s in NOTE_ENUM},   # R96
    notes_on_transfer=False,                                    # R64: no notes at all on a transferred call
    fin_keys={"promise": "promise", "paid": "paid", "default": "refused", "refused": "refused",
              "hardship": "hardship", "dispute": "dispute", "service_error": "service_error"},   # R66 closing precedence
    fail_max=1,                                                 # R78: create_promise gets one try
    human_limit=2,                                              # R57: ask once, then transfer
    notalk_limit=2,                                             # R58: says twice
    closed_day_move="after",                                    # R35: the next business day after it
    business_weekdays=BWD,
    weekday_rule=WEEKDAY_RULE,                                  # R39
    vague_again="deadline",                                     # R38: propose the latest date
    above_full="agree",                                         # R40: log the full amount
    targets={"xfer_support": "hs_decline"},                     # R81: no support transfer; hardship stays with the assistant
    asides={
        "robot": {"when": "asks whether they are talking to a robot, a machine or an AI", "say": ROBOT},          # R11
        "scam": {"when": "asks whether this call is a scam or genuine", "say": SCAM},                              # R12
        "reduction": {"when": "asks for a discount, a waiver, a payment holiday, interest frozen or any reduction", "say": "I'm afraid nothing like that is on offer; I can only log a payment."},   # R48
    })

# ---------------------------------------------------------------- terminals (dialler list v5; R65 goodbye)
FINS = {
    "promise": ("promise", "", BYE_T),
    "paid": ("paid", "CLP", "Thank you for letting me know. Payments can take up to two business days to show on your account with us. " + BYE_T),   # R54 verbatim (single product too)
    "transferred_restructuring": ("transferred", "XRS", "I'll put you through to our restructuring team now. " + BYE_T),
    "transferred_human": ("transferred", "XHM", "I'll put you through to a colleague now. " + BYE),
    "refused": ("no_promise", "RTP", "I understand. " + BYE_T),
    "hardship": ("no_promise", "VUL", "Take care. " + BYE_T),
    "dispute": ("no_promise", "DIS", BYE_T),
    "service_error": ("no_promise", "SYS", "I'm sorry, I couldn't confirm that arrangement on this call. Our team will be in touch with you about it. " + BYE_T),   # R78 verbatim
    "failed": ("not_verified", "NVF", "I'm sorry, I couldn't verify your identity on this call. You can use the Ashvale mobile app or come into a branch. " + BYE),   # R25
    "declined": ("not_verified", "NVD", "I understand. I can't continue without the security questions. " + BYE),   # R26, R58
    "callback": ("not_reached", "CBB", "Thank you, we'll call back then. " + BYE),
    "no_callback": ("not_reached", "CBX", "I understand, I won't book anything. " + BYE),
    "wrong_number": ("not_reached", "WRN", "I'm sorry for the disturbance. " + BYE),
    "deceased": ("not_reached", "DCD", "I'm very sorry for your loss."),                        # R20 verbatim, nothing else
    "unclear": ("not_reached", "UNK", "I'm sorry, I couldn't tell who I'm speaking with. " + BYE),   # R09
}
for key, (outcome, reason, farewell) in FINS.items():
    POLICY.end_pair(key, outcome, reason, farewell, nodes, promise_decides=False)   # R66: a transfer after a logged promise closes as the transfer

for q, fin, line in [("restructuring", "fin_transferred_restructuring", "I'll put you through to the team that handles that."),   # R56 describe nothing
                     ("general", "fin_transferred_human", "I'll put you through to a colleague now.")]:             # R57
    nodes[f"xfer_{q}"] = fl.api_node(
        f"xfer_{q}", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1),
        [fl.always(fin)], on_enter={"type": "tts", "text": line})

# ---------------------------------------------------------------- setup
DEFAULT_OUTCOME = r'''
if str(vars.get('who1') or '') == 'customer':
    vars['outcome'] = 'not_verified'
    vars['reason'] = 'NVD'
else:
    vars['outcome'] = 'not_reached'
    vars['reason'] = 'UNK'
'''
SETUP = fl.SETUP_CODE(HOLIDAYS, BWD, callback_rule={"open": CB["open"], "close": CB["close"], "same_day": bool(CB["same_day"]), "days_ahead": int(CB["days_ahead_business"])},
                      weekday_rule=WEEKDAY_RULE, extra=DEFAULT_OUTCOME)

# ---------------------------------------------------------------- opening (R07-R12)
WHO_VALUES = ["customer", "someone_else", "wrong_number", "deceased", "refuses", "unclear"]
WHO_DESC = ("Who answered, judged ONLY from the person's latest message. "
            "customer = ONLY 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} {{last_name}}). "
            "someone_else = another person answered (a relative, partner, colleague), or says the customer is not here / not available, or offers to take a message. "
            "wrong_number = says this number does not belong to that person / they do not know them. "
            "deceased = says the customer has died / passed away. "
            "refuses = says they do not want to talk or wants to end the call. "
            "unclear = anything else: 'hello', 'go ahead', 'who's calling?', 'what's it about?', 'is this a robot?', 'is this a scam?', any question, silence.")
ROUTES = [
    ("customer", "ask_dob", "the customer confirmed who they are"),
    ("deceased", "fin_deceased", "the customer has died"),
    ("wrong_number", "fin_wrong_number", "wrong number"),
    ("someone_else", "third_party", "someone else answered"),
]
nodes["opening"] = fl.opening_conv(
    "opening", OPENING_LINE + " " + ASK_NAME,
    "you have just introduced yourself and asked whether you may speak with {{title}} {{last_name}}. Do not call any tool in this turn. Do not say why you are calling.",
    [fl.ext("who1", WHO_VALUES, WHO_DESC)])
INITIAL = fl.conversation_first("opening", SETUP, "who1", ROUTES, "opening_retry", nodes)

nodes["opening_retry"] = fl.conv(
    "opening_retry",
    "You called {{title}} {{last_name}} and asked whether you may speak with them, but the answer did not confirm it. "
    "No tool call is allowed in this turn. Do not say why you are calling. Never use the words arrears, overdue, owe, debt, payment or collections, and name no product.\n"
    "If the person asked a question, answer it briefly first: "
    "a robot, an AI or a machine -> say exactly \"" + ROBOT + "\"; "
    "a scam -> say \"" + SCAM + "\"; "
    "who is calling -> the automated assistant from Ashvale Bank; what it is about -> a private matter you can discuss only with {{title}} {{last_name}}; "
    "if they said they do not want to talk -> say it will only take a moment.\n"
    "Then ask exactly: \"" + ASK_NAME + "\" This is the second and last time you ask.",   # R09, R10
    extraction=[fl.ext("who2", WHO_VALUES, WHO_DESC)],
    transitions=[fl.eq("who2", v, t, d) for v, t, d in ROUTES] + [
        fl.eq("who2", "refuses", "fin_declined", "does not want to talk, said twice (R58, before security)"),
        fl.always("fin_unclear")])   # R09 UNK

# ---------------------------------------------------------------- third party (R14-R20, R76, R77)
cb_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book a callback for the customer. CALL it as soon as the person names a day and time inside the allowed window.",
    field_descriptions={"date": "Callback date as YYYY-MM-DD. Must be one of the allowed days listed.",
                        "time": "Callback time as HH:MM, 24 hour, from " + CB["open"] + " to " + CB["close"] + " inclusive, later than now."},
    pre=fl.normalise_pre({"time": "time"}),
    post=fl.ok_post("Callback booked.", "The booking failed. Say you could not book it."))

nodes["third_party"] = fl.conv(
    "third_party",
    "You called for {{title}} {{last_name}} but someone else is on the line. You said: \"" + PRIVATE + "\"\n"
    "STRICT: Never say what the matter is. Never use the words arrears, overdue, owe, debt, payment or collections, never name a product or an amount. "
    "If they ask what it is about, say it is a private matter for {{title}} {{last_name}}. If they offer to pay or to help with it, thank them, say no, that it can only be dealt with by {{title}} {{last_name}}, and ask again when they can be reached. Never ask them a security question and arrange nothing with them except a callback.\n"
    "Your only job: ask when {{title}} {{last_name}} can be reached, then book a callback.\n"
    "Now: {{today_text}}, {{now_time}}.\n{{callback_text}}\n"
    "- If they give a day and time inside the window, call schedule_callback with date YYYY-MM-DD (from the list above) and time HH:MM. 'Tomorrow morning around eleven' means tomorrow at 11:00; 'four o'clock this afternoon' means today at 16:00. If they give only a day, ask for a time; if only a vague time like 'morning', propose a precise time such as 10:00 and ask if it suits.\n"
    "- If the day or time is outside the window (after " + CB["close"] + ", before " + CB["open"] + ", a weekend, a bank holiday, too far ahead, or earlier than now today), say the hours are " + CB["open"] + " to " + CB["close"] + " today or on the next two business days, and ask ONCE for another time.\n"
    "- If the second time is also outside the window, or they cannot say when, book nothing: call transition_to_fin_no_callback.\n"
    "- If they ask whether you are a robot: say exactly \"" + ROBOT + "\"\n"
    "After every tool result, speak or call the next tool.",
    on_enter={"type": "tts", "text": PRIVATE + " When would be a good time to reach them?"},
    tools=[cb_tool],
    extraction=[fl.ext("tp_status", ["none", "wrong_number", "deceased"],
                       "From the person's latest message: wrong_number if they say this number does not belong to the customer or they do not know the customer; deceased if they say the customer has died; otherwise none.")],
    transitions=[
        fl.ok_true("schedule_callback", "fin_callback", "callback booked"),
        fl.eq("tp_status", "deceased", "fin_deceased", "customer died"),
        fl.eq("tp_status", "wrong_number", "fin_wrong_number", "wrong number"),
        fl.intent_tool("fin_no_callback",
                       "No callback can be booked: the person gave a second time outside the allowed window, or cannot say when the customer is reachable.",
                       "No callback can be booked inside the allowed window"),
    ])

# ---------------------------------------------------------------- identity (R21-R26, R80, R97)
Q_DOB = "Could you tell me your date of birth, please?"
Q_PHONE = "And the last four digits of the phone number we hold for you?"
SWAP = "Day and month look swapped. This is NOT a wrong answer. Ask the customer to say the date of birth again with the month as a word, for example 14 March 1988."   # R23
LIMIT = ("Second wrong answer in total: the check has ended. Do not ask again and do not say what the call was about. "
         "Tell the customer they can use the Ashvale mobile app or come into a branch.")   # R80, R25
WRONG = "Wrong answer. Tell the customer it does not match our records and ask the same question again: {question}"   # a wrong answer can be asked again


def verify_tool(field, question, desc, answer_desc, verified_text):
    return fl.api_tool(API, "verify_identity", baked={"field": field}, description=desc,
                       field_descriptions={"answer": answer_desc},
                       pre=fl.reset_pre(["question_count_" + ("phone" if field == "phone_last4" else "dob")]) +
                       fl.normalise_pre({"answer": "answer"}, date_order="dmy"),   # R22: numbers only = day, month, year
                       post=fl.verify_count_post(question, MAX_WRONG, {"day_month_swapped": SWAP}, LIMIT,
                                                 free_hints={"day_month_swapped": 1},
                                                 all_verified_text="Both security questions passed. Identity is verified.",
                                                 verified_text=verified_text, wrong_text=WRONG))


ID_COMMON = ("Rules for this step:\n"
             "- Until both questions pass, never use the words arrears, overdue, owe, debt, payment or collections, and name no product or amount.\n"
             "- If the customer refuses to answer or asks what the call is about instead of answering: explain that these questions are there to protect their account and that you can explain the reason for the call right after them, then ask the question again.\n"
             "- If the customer asks another question (who is calling, why you need it): answer it in one short sentence, then ask the question again. "
             "Robot, AI or machine -> say exactly \"" + ROBOT + "\". Scam -> say \"" + SCAM + "\"\n"
             "- If the customer asks for a person: the first time, ask whether you can help them yourself; if they insist, the call is transferred.\n"
             "- " + fl.latest_value_note(4) + "\n"
             "- After every tool result, speak to the customer or call the next tool. Follow what_to_do_next.")
REFUSAL_DESC = ("From the customer's LATEST message only. "
                "refused = they refuse to answer the security question, OR they ask what the call is about (or what they owe) instead of answering it. "
                "end_call = they say they do not want to talk or want to end the call. "
                "human = they ask to speak to a person, a human, an agent. "
                "question = they ask something else back instead of answering (who is calling, why you need it, is this a robot, is this a scam) without refusing. "
                "none = they give an answer or say anything else." + fl.REFUSAL_NONE_CLAUSE)
REFUSAL_VALUES = ["none", "refused", "end_call", "human", "question"]

nodes["ask_dob"] = fl.conv(
    "ask_dob",
    "The person confirmed they are {{title}} {{last_name}}. Check identity with two security questions, one at a time. Ask the first now: \"" + Q_DOB + "\"\n"
    "When they give it, call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 1990-03-05). "
    "If they give only part of the date, ask for the rest before calling the tool. Do not ask the phone digits before this question has passed.\n" + ID_COMMON,
    tools=[verify_tool("date_of_birth", Q_DOB, "Check the date of birth. CALL it every time the customer gives a full date of birth.",
                       "The date of birth as YYYY-MM-DD.", "Correct. Now ask the second security question: " + Q_PHONE)],
    extraction=[fl.ext("refusal_dob", REFUSAL_VALUES, REFUSAL_DESC)],
    transitions=[
        fl.eq("id_route", "exhausted", "fin_failed", "second wrong answer in total (R80)"),
        fl.is_true("verify_identity_response.data.verified", "ask_phone", "date of birth correct"),
        fl.eq("refusal_dob", "human", "human_dob", "asks for a person (R57)"),
        fl.eq("refusal_dob", "end_call", "count_decline_dob", "does not want to talk (R58)"),
        fl.eq("refusal_dob", "refused", "count_decline_dob", "refuses or deflects (R26)"),
        fl.eq("refusal_dob", "question", "qb_dob", "asks another question back"),
    ])

nodes["ask_phone"] = fl.conv(
    "ask_phone",
    "The date of birth was correct. Ask the second security question now: \"" + Q_PHONE + "\"\n"
    "When they give four digits, call verify_identity with answer = the four digits only.\n" + ID_COMMON,
    tools=[verify_tool("phone_last4", Q_PHONE, "Check the last four digits of the phone number we hold. CALL it every time the customer gives four digits.",
                       "Exactly four digits.", "Both security questions passed. Identity is verified.")],
    extraction=[fl.ext("refusal_phone", REFUSAL_VALUES, REFUSAL_DESC)],
    transitions=[
        fl.is_true("verify_identity_response.data.all_verified", "load_account", "identity verified"),
        fl.eq("id_route", "exhausted", "fin_failed", "second wrong answer in total (R80)"),
        fl.eq("refusal_phone", "human", "human_phone", "asks for a person (R57)"),
        fl.eq("refusal_phone", "end_call", "count_decline_phone", "does not want to talk (R58)"),
        fl.eq("refusal_phone", "refused", "count_decline_phone", "refuses or deflects (R26)"),
        fl.eq("refusal_phone", "question", "qb_phone", "asks another question back"),
    ])

for stage in ["dob", "phone"]:
    # R26: explain once; the second refusal or deflection closes declined (counted across both questions); R58 'no talk' twice
    code = fl.counter_code("decline_count", 2, "decline_route", reset={"refusal_dob": "none", "refusal_phone": "none"})
    nodes[f"count_decline_{stage}"] = fl.code_node(f"count_decline_{stage}", code, [
        fl.eq("decline_route", "close", "fin_declined", "second refusal"), fl.always(f"ask_{stage}")])
    nodes[f"qb_{stage}"] = fl.question_back_node(stage, f"ask_{stage}", "fin_declined")
    # R57: ask once whether the assistant can help; the second request transfers to general
    hcode = fl.counter_code("human_count", 2, "human_route", reset={"refusal_dob": "none", "refusal_phone": "none"})
    nodes[f"human_{stage}"] = fl.code_node(f"human_{stage}", hcode, [
        fl.eq("human_route", "close", "xfer_general", "insists on a person"), fl.always(f"ask_{stage}")])

# ---------------------------------------------------------------- account, bands, floors, ladder (R27, R32-R36, R68-R70)
PREPARE_BODY = fl.products_from_vars() + r'''
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
a1 = addbd(today, 2)                                    # R70 proposal 1: the 2nd business day after the call date
items = []
for i, p in enumerate(prods):
    if not isinstance(p, dict):
        continue
    ptype = str(p.get('type') or '')
    pid = str(p.get('product_id') or ('p' + str(i + 1)))
    past_due = float(p.get('past_due') or 0)
    if ptype == 'credit_card':
        words = 'credit card ending ' + str(p.get('card_last4') or '')
        try:
            mp = float(p.get('minimum_payment') or 0)
        except Exception:
            mp = 0.0
        floor = max(round(past_due / 2.0, 2), mp)      # R68: half the overdue balance, or the minimum payment where higher
        floor_name = 'smallest amount we can log'
    else:
        words = ptype.replace('_', ' ') if ptype else 'loan'
        try:
            floor = float(p.get('instalment_amount'))   # R68: the instalment amount
        except Exception:
            floor = past_due
        floor_name = 'instalment amount'
    if floor > past_due:
        floor = past_due
    days_late = int(float(p.get('days_late') or 0))
    if days_late <= 9:                                  # R69 early band: 18 calendar days, next business day if closed; 1 proposal
        deadline = today + datetime.timedelta(days=18)
        while not isbd(deadline):
            deadline = deadline + datetime.timedelta(days=1)
        rungs = [('full_or_floor', a1)]
    else:                                               # R69 late band (10 and over): the 5th business day; 2 proposals, the 2nd = the floor on the latest date
        deadline = addbd(today, 5)
        rungs = [('full_or_floor', a1), ('floor', deadline)]
    register_product(vars, pid, words, past_due, floor, floor_name, deadline, rungs)
    items.append((words, past_due, days_late, deadline))
name = str(vars.get('title') or '') + ' ' + str(vars.get('last_name') or '')
statement = 'Thank you, ' + name + ". I'm calling from Ashvale's Customer Payments team about an overdue balance. "   # R27
for w, pd, dl_, dd in items:
    statement += 'Your ' + w + ' has ' + fmt(pd) + ' overdue, ' + str(dl_) + ' days overdue. '
if len(items) == 1:
    statement += 'Would you be able to pay the full overdue balance today?'   # R29 verbatim
else:
    statement += 'Would you be able to pay all of these in full today?'     # R29 verbatim
lines = []
for w, pd, dl_, dd in items:
    lines.append(w + ': overdue ' + fmt(pd) + ', ' + str(dl_) + ' days overdue, latest date ' + txt_short(dd))
vars['products_facts'] = '; '.join(lines)
vars['outcome'] = 'no_promise'                          # R58: a hang-up after security = will not talk, refused
vars['reason'] = 'RTP'
'''
PREPARE = POLICY.prepare_code(PREPARE_BODY, "statement", fallbacks={
    "say_next": "Thank you. I'm calling from Ashvale's Customer Payments team about an overdue balance. Would you be able to pay the full overdue balance today?",
    "products_facts": ""})

nodes["load_account"] = fl.api_node(
    "load_account", fl.api_tool(API, "get_account", description="Get the overdue products.", retries=2),
    [fl.always("prepare")], mapping=[{"path": "data.products", "variable": "products"}])
nodes["prepare"] = fl.code_node("prepare", PREPARE, [fl.always("negotiate")])

# ---- extraction, in the brief's own terms
TOPIC_DESC = ("What the customer's LATEST message says, if it is one of these. "
              "hardship = mentions illness, a bereavement, losing their job or a similar hardship (this wins over every other value, even when they also name a date or an amount). "
              "already_paid = says they have ALREADY paid this overdue amount (not 'I will pay'). "
              "dispute = says 'it's not mine', 'I never had that', the product or balance is not theirs. "
              "new_plan = asks for a payment plan, lower instalments, or more time in general. Saying the amount is too much is NOT new_plan; a different amount or date for this payment is NOT new_plan." + fl.PLAN_REQUEST_CLAUSE + " "
              "human = asks to speak to a person, a human, an agent or a colleague. "
              "no_talk = says they do not want to talk or want to end the call (not a refusal to pay). "
              "none = anything else: offers, yes or no answers, refusals to pay, questions.")
STANCE_DESC = ("The customer's answer to the agent's LATEST payment proposal, from the customer's latest message only. "
               "accept = agrees to exactly what the agent proposed ('yes', 'okay', 'fine', 'that works', 'I can do that'). "
               "refuse = a flat no with no date and no amount ('no', 'I can't', 'not today', 'I won't'), declining the proposal, or a non-answer that avoids the question ('I don't know', 'maybe'). "
               "too_much = says the full amount is too much, too high, or that they cannot pay all of it, without naming an amount. "
               "offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. "
               "other = anything else: a question, small talk, a request.")
KIND_DESC = ("From the customer's LATEST message only. exact = they name a specific payment day (a date, a weekday, 'tomorrow', 'the 26th') or a specific amount of money, or both. "
             "vague = only a vague period without a day ('next week', 'end of the month', 'payday', 'when I get paid'), or they say they cannot say which day. "
             "none = no date, amount or period in the latest message (also 'yes', 'no', questions).")
FOR_DESC = ("Which product the customer's LATEST message is about, in the order the agent listed the products: first, second or third "
            "(match the product they name, e.g. 'the credit card', 'the car loan'); pick that one even when they mention the other products only to "
            "refuse or exclude them. all = all of them, everything, both, or one date or amount for everything. none = no product named.")
DATE_DESC = ("The payment date the customer names in their LATEST message. 'Friday' or 'this Friday' is the first Friday after today; 'next Friday' is the Friday after that, seven days later; the same for other weekdays. "
             "Leave it empty when the latest message names no specific day.")
AMOUNT_DESC = ("The amount of money the customer offers to pay in their LATEST message, as a number ('three hundred and twenty' = 320). "
               "Leave it empty when the latest message names no amount. A day of the month is not an amount.")
REF_DESC = ("Whether the customer's LATEST message names the payment amount BY REFERENCE instead of as a number. "
            "floor = the smallest amount the agent can log: 'the minimum', 'the minimum payment', 'the instalment', 'half', 'the lowest amount'. "
            "full = the whole overdue amount ('all of it', 'the full amount', 'everything') ONLY when they offer to pay it. none = no such reference (also when they say a number).")
CONFIRM_DESC = ("The customer's answer to the read-back question 'Shall I go ahead and log that?', from their latest message only. "
                "yes = a clear yes ('yes', 'go ahead', 'please do', 'that's right'). "
                "change = they give a different amount or a different date for a promise ('make it 200 instead', 'actually Monday'). "
                "no = a plain no without a new amount or date. other = anything else, for example a question.")

topic = fl.ext("topic", ["none", "hardship", "already_paid", "dispute", "new_plan", "human", "no_talk"], TOPIC_DESC)
offer_for = fl.ext("offer_for", ["none", "all", "first", "second", "third"], FOR_DESC)
TOPIC_TRS = POLICY.topic_transitions()

FACTS = ("FACTS\n- Products: {{products_facts}}.\n- Today: {{today_text}}.\n")
COMMON = ("- If asked whether you are a robot, an AI or a machine: say exactly \"" + ROBOT + "\" If asked whether this is a scam: say \"" + SCAM + "\"\n"
          "- Nothing else is on offer: no discount, no waiver, no payment holiday, no plan, no freezing interest. If asked, say so.\n"
          "- A question these facts do not answer: say exactly \"" + NO_INFO + "\"\n"
          "- No tool call is allowed here. Never say that a promise is logged.\n")

NEGOTIATE = ("You are talking with {{title}} {{last_name}}, who is verified, about the overdue balance. The line you just said and the offer in STATE were decided by the system from the bank's rules.\n"
             "- Never propose, compute or change an amount or a date yourself, and never ask how much they can pay, in any wording. The only offer you may make is the current offer in STATE, word for word.\n"
             "- If the customer asks a question or says something else, answer it in one short sentence, then ask the current offer again.\n"
             + COMMON + FACTS)
neg_ext = [topic, POLICY.stance_extraction(STANCE_DESC), offer_for] + POLICY.offer_extraction(DATE_DESC, AMOUNT_DESC, KIND_DESC, ref_desc=REF_DESC)
neg_trs = TOPIC_TRS + POLICY.offer_guard_transitions() + POLICY.stance_transitions()
nodes["negotiate"] = POLICY.negotiate_node(NEGOTIATE, neg_ext, neg_trs)

CONFIRM = ("You read back the arrangement and asked \"Shall I go ahead and log that?\". It is logged only after a clear yes.\n"
           "- If the customer asks something, answer it in one short sentence, then ask again: \"Shall I go ahead and log that?\".\n"
           + COMMON + FACTS)
nodes["confirm"] = POLICY.confirm_node(CONFIRM, CONFIRM_DESC, DATE_DESC, AMOUNT_DESC, topic_entry=topic, topic_trs=TOPIC_TRS, ref_desc=REF_DESC)

# R81: hardship stays with the assistant: sympathy + Financial Support letter (spoken on entry), no proposal; a date or
# amount they name is logged as normal (offer guard); anything else closes every open product as hardship (VUL).
HS_ANSWER_DESC = ("From the customer's LATEST message. support_no = they acknowledge, say thanks, say no, say they cannot pay, or want nothing more. "
                  "support_yes = they ask for the letter or the Financial Support team (treated the same: the letter is already on its way). "
                  "accept_offer = they agree to a date and amount they themselves named. "
                  "human = they ask to speak to a person, a human or an agent. "
                  "none = anything else, for example a question.")
HARDSHIP = ("The customer mentioned a hardship (illness, a bereavement, job loss or similar). You said \"I'm sorry you're going through that.\" and that the Financial Support team will write to them within five working days.\n"
            "- Make NO proposal. Never propose an amount or a date yourself and never ask what they can pay. Do not offer a transfer.\n"
            "- If they ask a question, answer in one short sentence; otherwise wait for them.\n"
            + COMMON + FACTS)
nodes["hardship"] = POLICY.hardship_node(HARDSHIP, HS_ANSWER_DESC, KIND_DESC, DATE_DESC, AMOUNT_DESC, ref_desc=REF_DESC, human=True)   # R83

WRAP_DESC = ("From the customer's LATEST message, after the agent said the arrangement is logged and asked whether there is anything else. "
             "done = nothing else ('no', 'that's all', 'thanks', 'goodbye'). "
             "human = asks to speak to a person, a human or an agent, or insists on one. "
             "new_plan = asks for a payment plan or lower instalments. "
             "change = asks to change, move or cancel the arrangement just logged (another date or amount). "
             "question = asks a question. other = anything else.")
WRAPUP = ("The arrangements in STATE are logged. You said so and asked whether there is anything else.\n"
          "- If the customer asks a question, answer it in one or two sentences from these facts or say exactly \"" + NO_INFO + "\", then ask whether there is anything else you can help with.\n"
          "- Once it's logged it can't be changed or cancelled on this call; they can change it in the Ashvale mobile app.\n"
          + COMMON + FACTS)
nodes["wrapup"] = POLICY.wrapup_node(WRAPUP, WRAP_DESC)

POLICY.add_event_nodes(nodes)
POLICY.record_nodes(nodes, API)

# ---------------------------------------------------------------- close_call lifecycle (dialler list v5)
close_call = fl.close_call_tool(
    API,
    outcome_desc="promise: a promise was logged. paid: every product noted paid. transferred: handed to a person. no_promise: verified, no promise. not_verified: identity not passed. not_reached: the customer was not reached.",
    reason_desc="paid: CLP. transferred: XRS|XHM. no_promise: RTP|VUL|DIS|SYS. not_verified: NVF|NVD. not_reached: CBB|CBX|WRN|DCD|UNK. Empty for promise.",
    no_reason_outcomes=("promise",))

SYSTEM = ("You are the automated assistant from Ashvale Bank on an outbound phone call to {{title}} {{last_name}}. Speak English. Keep every turn to one or two short sentences. Address the customer as {{title}} {{last_name}}.\n"
          "Always:\n"
          "- Until both security questions are passed, never use the words arrears, overdue, owe, debt, payment or collections, and never name a product, to anyone.\n"
          "- If asked whether you are a robot, an AI or a machine: say exactly \"" + ROBOT + "\" and carry on.\n"
          "- If asked whether this is a scam: say \"" + SCAM + "\" and carry on.\n"
          "- Anything you cannot answer from the facts you were given: say exactly \"" + NO_INFO + "\" Never invent a figure, a date or a reason.\n"
          "- Nothing else is on offer: no discount, no waiver, no payment holiday, no plan, no freezing interest.\n"
          "- Never ask the customer how much they can pay, in any wording: you propose every amount.\n"
          "- Do not say goodbye or end the call yourself: the call is closed for you.\n"
          "- Call at most one tool per message. When a rule says to call a tool, call it: saying it is not enough.\n"
          "- After every tool result, speak to the customer or call the next tool. Never end a turn with nothing. Follow what_to_do_next in a tool result.\n"
          "- Say amounts as plain numbers, for example 420.50, and dates as weekday, day and month, for example Friday 16 October.")

wf = fl.assemble(INITIAL, nodes, SYSTEM, [close_call], conduct=True)   # no test_variables

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out/ashvale.workflow.json"
    fl.write_workflow(wf, out)
    print("nodes:", len(nodes), "->", out)
