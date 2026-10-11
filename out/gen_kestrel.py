"""Kestrel Bank autumn arrears campaign (brief kestrel.md: email of 6 Oct + CP-7 s.4 + memo of 12 Oct in force from
14 Oct + code list v3). Policy as code on builder/policy.py. Every value in this file comes from that brief/spec."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

API = fl.load_api(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tools/openapi.json")
SPEC = json.load(open(ROOT / "out/kestrel.spec.json"))["spec"]
HOLIDAYS = [h["date"] for h in SPEC["calendar"]["holidays"]]          # R83/R109: CP-7 4.3 + memo item 4 (Founders' Day)
CB = SPEC["callback"]                                                   # R113: 09:00-18:00, today later than now, next 2 business days
BANK = "Kestrel Bank"

nodes = {}

# ---------------------------------------------------------------- terminals: code list v3 + memo item 5 (HSHP)
FINS = {
    "promise": ("promise", "PRM", "Thank you for your time, {{title}} {{last_name}}. Goodbye."),
    "paid": ("paid", "AP", "Payments made today show on our side on the next business day. Thank you for letting me know, {{title}} {{last_name}}. Goodbye."),   # R60 verbatim, fixed text
    "transferred_restructuring": ("transferred", "TRS", "Thank you, {{title}} {{last_name}}. A colleague will take over now. Goodbye."),
    "transferred_human": ("transferred", "TRH", "Thank you, {{title}} {{last_name}}. A colleague will take over now. Goodbye."),
    "transferred_support": ("transferred", "TSP", "Thank you, {{title}} {{last_name}}. A colleague from our customer care team will take over now. Goodbye."),
    "refused": ("no_promise", "RF", "I understand. Thank you for your time, {{title}} {{last_name}}. Goodbye."),
    "hardship": ("no_promise", "HSHP", "Thank you for your time, {{title}} {{last_name}}, and take care. Goodbye."),   # memo item 5: HSHP replaces HARD from 14 Oct
    "dispute": ("no_promise", "DSP", "Thank you for telling me. Thank you for your time, {{title}} {{last_name}}. Goodbye."),
    "service_error": ("no_promise", "SVC", "I am sorry, I could not record that because of a technical problem. Thank you for your time, {{title}} {{last_name}}. Goodbye."),
    "failed": ("not_verified", "IDF", "I am sorry, for security I cannot continue by phone. You can use the Kestrel mobile app or visit a branch. Thank you, goodbye."),
    "declined": ("not_verified", "IDD", "I understand. Nothing can be discussed without the security questions. Thank you for your time, goodbye."),
    "callback": ("not_reached", "CBK", "Thank you, we will call back then. Goodbye."),
    "no_callback": ("not_reached", "NCB", "Thank you for your help. Goodbye."),
    "wrong_number": ("not_reached", "WN", "I apologise for the inconvenience. Thank you, goodbye."),
    "deceased": ("not_reached", "DEC", "Please accept my condolences. Goodbye."),
    "unclear": ("not_reached", "UNC", "I am sorry, I could not confirm who I am speaking with. Thank you, goodbye."),
}
for key, (outcome, reason, farewell) in FINS.items():
    fl.end_pair(key, outcome, reason, farewell, nodes)

# ---------------------------------------------------------------- setup: calendar, callback window, default close
SETUP_EXTRA = r'''
vars['outcome'] = 'not_reached'
vars['reason'] = 'UNC'
'''
SETUP = fl.SETUP_CODE(HOLIDAYS, callback_rule={"open": CB["open"], "close": CB["close"], "same_day": bool(CB.get("same_day", True)),
                                               "days_ahead": int(CB.get("days_ahead_business", 2))},
                      extra=SETUP_EXTRA, weekday_rule="first_after_plus7")

# ---------------------------------------------------------------- opening (R13-R20)
OPEN_LINE = "This is the digital assistant of Kestrel Bank. Please note that this call is recorded. Am I speaking with {{first_name}} {{last_name}}?"
WHO_VALUES = ["customer", "someone_else", "wrong_number", "deceased", "refuses", "unclear"]
WHO_DESC = ("Who answered, judged ONLY from the person's latest message. "
            "customer = they confirm they are {{first_name}} {{last_name}}: 'yes', 'speaking', 'that's me', or they say the customer's own name. "
            "someone_else = another person answered (a relative, partner, flatmate, colleague), or says the customer is not here / not available, or offers to take a message. "
            "wrong_number = says this number does not belong to that person / they do not know them. "
            "deceased = says the customer has died / passed away. "
            "refuses = says they do not want to talk / not interested. "
            "unclear = anything else: 'hello', 'go ahead', 'who's asking', 'what is this about', a question, silence.")
OPENING_ROUTES = [
    ("customer", "ask_phone", "the customer confirmed who they are"),
    ("deceased", "fin_deceased", "the customer has died"),
    ("wrong_number", "fin_wrong_number", "wrong number"),
    ("someone_else", "third_party", "someone else answered"),
]
nodes["opening"] = fl.conv(
    "opening",
    "If you have not spoken yet, say exactly: \"" + OPEN_LINE + "\" Do not call any tool in this turn. Do not say why you are calling.",
    on_enter={"type": "tts", "text": OPEN_LINE},
    extraction=[fl.ext("who1", WHO_VALUES, WHO_DESC)], first_only=True)
INITIAL = fl.conversation_first("opening", SETUP, "who1", OPENING_ROUTES, "opening_retry", nodes)

ASIDES_TXT = ("who you are -> 'I am Kestrel Bank's digital assistant.'; a robot or AI -> say exactly \"I am Kestrel Bank's digital assistant.\"; "
              "a scam -> say they are welcome to hang up and call the number on the back of their card or on their statement; "
              "what it is about -> it is a personal banking matter you can only discuss with {{first_name}} {{last_name}}.")
nodes["opening_retry"] = fl.conv(
    "opening_retry",
    "You asked whether you are speaking with {{first_name}} {{last_name}}, but the answer did not confirm it. This is the second and last ask. "
    "No tool call is allowed in this turn. Never say why you are calling; never say arrears, overdue, late, collections, debt, payment, instalment or any product name.\n"
    "If the person asked a question, answer it in one short sentence first: " + ASIDES_TXT + " "
    "If they said they do not want to talk, say this will only take a moment. "
    "Then ask exactly: \"Am I speaking with {{first_name}} {{last_name}}?\"",
    extraction=[fl.ext("who2", WHO_VALUES, WHO_DESC)],
    transitions=[
        fl.eq("who2", "customer", "ask_phone", "the customer confirmed who they are"),
        fl.eq("who2", "deceased", "fin_deceased", "the customer has died"),
        fl.eq("who2", "wrong_number", "fin_wrong_number", "wrong number"),
        fl.eq("who2", "someone_else", "third_party", "someone else answered"),
        fl.eq("who2", "refuses", "fin_declined", "does not want to talk, said twice"),
        fl.always("fin_unclear"),
    ])

# ---------------------------------------------------------------- third party (R22-R29)
cb_tool = fl.api_tool(
    API, "schedule_callback",
    description="Book a callback for the customer. CALL it as soon as the person names a day and time inside the allowed window.",
    field_descriptions={"date": "Callback date as YYYY-MM-DD. Must be one of the allowed days.",
                        "time": "Callback time as HH:MM, 24 hour, between %s and %s." % (CB["open"], CB["close"])},
    pre=fl.normalise_pre({"date": "date", "time": "time"}, date_order="dmy"),
    post=fl.ok_post("Callback booked.", "The booking failed. Try schedule_callback once more with the same values."))

nodes["third_party"] = fl.conv(
    "third_party",
    "You called for {{title}} {{last_name}} ({{first_name}}) but someone else is on the line.\n"
    "STRICT: Say only that it is a personal banking matter that you can only discuss with {{title}} {{last_name}}, and ask when he or she can be reached. Nothing more. "
    "Never say arrears, overdue, late, collections, debt, payment, instalment or any product name, even if they ask or offer to pay or help: a relative cannot answer security questions, "
    "cannot be told anything about the account and cannot act for the customer on this call; if they offer to help or to settle anything, say only 'I am sorry, I can only discuss this with {{title}} {{last_name}} personally' (never the word payment, pay or account) and go back to asking when {{title}} {{last_name}} can be reached.\n"
    "Now: {{today_text}}, {{now_time}}.\n{{callback_text}}\n"
    "- If they give a day and time inside the window, call schedule_callback with date YYYY-MM-DD and time HH:MM. If they give only a day, ask for a time; if only a vague time like 'morning', propose a precise time inside the window and ask if it suits.\n"
    "- If the day or time is outside the window, propose the nearest slot inside it, ONCE (the counter below says whether you already did). "
    "If they do not take it (second answer still outside the window, or they cannot say when), do not book: call transition_to_fin_no_callback.\n"
    "After every tool result, speak or call the next tool.",
    tools=[cb_tool],
    extraction=[fl.ext("tp_status", ["none", "wrong_number", "deceased"],
                       "From the person's latest message: wrong_number if they say this number does not belong to the customer or they do not know the customer; deceased if they say the customer has died; otherwise none.")],
    transitions=[
        fl.ok_true("schedule_callback", "fin_callback", "callback booked"),
        fl.eq("tp_status", "deceased", "fin_deceased", "customer died"),
        fl.eq("tp_status", "wrong_number", "fin_wrong_number", "wrong number"),
        fl.intent_tool("fin_no_callback",
                       "No callback can be booked: the nearest slot inside the window was proposed once and not taken, or the person cannot say when the customer is reachable.",
                       "No callback inside the window"),
    ])

# ---------------------------------------------------------------- identity (R30-R37): phone_last4 then date_of_birth, 2 wrong answers end the check
HINTS = {"day_month_swapped": "Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month as a word, for example 14 March 1988."}
MAX_WRONG = "Second wrong answer: the check has ended. Say nothing about the account or the reason for the call."
ALL_VERIFIED = "Both answers are correct. Identity verified."
STOP_LEFT = ("1", "0")   # the service allows three wrong answers; Kestrel ends the check at the second (wrong_answers_left 1)

transfer_general = fl.api_tool(API, "transfer_to_agent", baked={"queue": "general"},
                               description="Transfer the call to a human agent. CALL it straight away when the customer asks for a person; do not ask whether you can help first.")

ID_COMMON = ("Rules for this step:\n"
             "- Never say arrears, overdue, late, collections, debt, payment, instalment or any product name, and never say why you are calling. If asked what the call is about or how much they owe, say you can explain right after the security questions.\n"
             "- If the customer asks a question back (why you need it, who is calling, robot, scam): answer in one short sentence (" + ASIDES_TXT + "), then say that these questions are there to protect their account and nothing can be discussed without them, then ask the same question again.\n"
             "- If the customer asks for a person or a human agent: call transfer_to_agent at once.\n"
             "- After every tool result, speak to the customer or call the next tool. Follow what_to_do_next.")

REFUSAL_DESC = ("From the customer's LATEST message only: refused if they refuse to answer the security question, say they do not want to talk, "
                "or ask AGAIN what the call is about instead of answering (after it was already explained). human if they ask for a person or a human agent. "
                "none if they give an answer or say anything else." + fl.QUESTION_ENUM_CLAUSE + fl.REFUSAL_NONE_CLAUSE)

nodes["ask_phone"] = fl.conv(
    "ask_phone",
    "The person confirmed they are {{title}} {{last_name}}; from now on address them as {{title}} {{last_name}}. You must check identity with two security questions, one at a time. "
    "Now ask the first: the last four digits of the phone number the bank holds for them.\n"
    "When they give four digits, call verify_identity with answer = the four digits only. " + fl.latest_value_note(4) + "\n" + ID_COMMON,
    tools=[fl.api_tool(API, "verify_identity", baked={"field": "phone_last4"}, pre=fl.compose_pre(fl.reset_pre(["question_count_phone"]), fl.normalise_pre({"answer": "digits"})) if hasattr(fl, "compose_pre") else fl.normalise_pre({"answer": "digits"}),
                       description="Check the last four digits of the phone number. CALL it every time the customer gives four digits.",
                       field_descriptions={"answer": "Exactly four digits."},
                       post=fl.verify_post("What are the last four digits of the phone number we hold for you?", HINTS, MAX_WRONG, all_verified_text=ALL_VERIFIED,
                                           verified_text="Correct. Now ask the second security question: the date of birth.", stop_left=STOP_LEFT)), transfer_general],
    extraction=[fl.ext("refusal_phone", ["none", "refused", "question", "human"], REFUSAL_DESC)],
    transitions=[
        fl.is_true("verify_identity_response.data.verified", "ask_dob", "phone digits correct"),
        fl.eq("verify_identity_response.data.wrong_answers_left", "1", "fin_failed", "second wrong answer"),
        fl.eq("verify_identity_response.data.wrong_answers_left", "0", "fin_failed", "wrong answers exhausted"),
        fl.transferred("fin_transferred_human", "transferred"),
        fl.eq("refusal_phone", "refused", "count_decline_phone", "customer declined"),
        fl.eq("refusal_phone", "question", "qb_phone", "asks a question back"),
    ])

nodes["ask_dob"] = fl.conv(
    "ask_dob",
    "The phone digits were correct. Now ask the second security question: their date of birth.\n"
    "When they give it, call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 1990-03-05). "
    "If they give only part of the date, ask for the rest before calling the tool. " + fl.latest_value_note(what="the date") + "\n" + ID_COMMON,
    tools=[fl.api_tool(API, "verify_identity", baked={"field": "date_of_birth"}, pre=fl.compose_pre(fl.reset_pre(["question_count_dob"]), fl.normalise_pre({"answer": "date"}, date_order="dmy")) if hasattr(fl, "compose_pre") else fl.normalise_pre({"answer": "date"}, date_order="dmy"),
                       description="Check the date of birth. CALL it every time the customer gives a full date of birth.",
                       field_descriptions={"answer": "The date of birth as YYYY-MM-DD."},
                       post=fl.verify_post("What is your date of birth?", HINTS, MAX_WRONG, all_verified_text=ALL_VERIFIED, stop_left=STOP_LEFT)), transfer_general],
    extraction=[fl.ext("refusal_dob", ["none", "refused", "question", "human"], REFUSAL_DESC)],
    transitions=[
        fl.is_true("verify_identity_response.data.all_verified", "load_account", "identity verified"),
        fl.eq("verify_identity_response.data.wrong_answers_left", "1", "fin_failed", "second wrong answer"),
        fl.eq("verify_identity_response.data.wrong_answers_left", "0", "fin_failed", "wrong answers exhausted"),
        fl.transferred("fin_transferred_human", "transferred"),
        fl.eq("refusal_dob", "refused", "count_decline_dob", "customer declined"),
        fl.eq("refusal_dob", "question", "qb_dob", "asks a question back"),
    ])

for stage in ["phone", "dob"]:
    nodes[f"qb_{stage}"] = fl.question_back_node(stage, f"ask_{stage}", "fin_declined")
    code = fl.counter_code("decline_count", 2, "decline_route", reset={"refusal_dob": "none", "refusal_phone": "none"})   # explain once, then IDD
    nodes[f"count_decline_{stage}"] = fl.code_node(f"count_decline_{stage}", code, [
        fl.eq("decline_route", "close", "fin_declined", "declined again"), fl.always(f"ask_{stage}")])

# ---------------------------------------------------------------- payment: policy as code (email + CP-7 4.1-4.8 + memo)
NOTE_ENUM = fl.tool_spec(API, "add_note")["fields"]["reason"]["enum"]
POLICY = pol.Policy(
    HOLIDAYS,
    texts={
        "question": "Can you pay [amount] [when]?",
        "today_when": "today, [date]",
        "tomorrow_when": "tomorrow, [date]",
        "question_product": "For your [words], can you pay [amount] [when]?",
        "question_all": "Are you able to clear all of these today?",                       # R40 verbatim
        "weekend_or_holiday": "A payment promised for [named] would not process until the following business day, as the bank is closed that day. The nearest business day before it is [date].",   # 4.6
        "after_deadline": "The latest date I can record for your [words] is [deadline], the last day that can be recorded.",   # 4.6
        "before_today": "[named] has already passed; it must be a day from today onwards.",     # 4.6
        "below_floor": "[named] cannot be recorded. The lowest amount I can record for your [words] is [floor]. The remainder stays overdue and we will be in touch about it.",   # 4.5
        "above_full": "The overdue amount is [full], so I will record [full].",                 # 4.5: record the full amount
        "vague": "Which exact day would that be?",                                               # 4.6 ask once
        "vague_deadline": "The latest date I can record for your [words] is [deadline].",
        "too_much_floor": "I understand. I can offer [floor] for your [words]. The remainder stays overdue and we will be in touch about it.",   # email + 4.5
        "exhausted": "I understand.",
        "one_by_one": "Let us go through them one by one.",
        "next_product": "Next, your [words].",
        "paid": "Payments made today show on our side on the next business day. I will not take a promise for your [words].",   # R60 verbatim
        "dispute": "I understand. I will not take a promise for your [words].",                  # R61
        "hardship": "I am sorry to hear that. Would you like me to put you through to our customer care team?",   # R49 verbatim + support offer once
        "human_first": "I will put you through to a colleague now.",                            # human_limit 1: never used as a question
        "notalk_first": "This will only take a moment.",                                        # R63 once
        "readback_head": "To confirm: your ",
        "readback_item": "[words], [amount], [when]",
        "readback_sep": "; your ",
        "own_deadline": ", which is the latest date I can record for it",
        "moved_bd": ", the nearest business day before the day you named",
        "readback_tail": ". Shall I record that?",                                               # R54 verbatim
        "recorded": "Your promise is recorded.",
        "recorded_many": "Your promises for your [list] are recorded.",
        "after_recorded": "We will email you a confirmation of this arrangement.",               # R59 verbatim, once per call
        "rec_failed": "I could not record the promise for your [words] because of a technical problem.",
        "anything_else": "Is there anything else I can help you with?",
        "wrap_change": "A recorded promise cannot be changed or cancelled on this call.",
    },
    multi=True, notes=True,
    note_reasons={s: s for s in ("refused", "hardship", "dispute", "paid", "service_error") if s in NOTE_ENUM},
    notes_on_transfer=False,                               # no notes at all after a transfer
    fin_keys={"promise": "promise", "paid": "paid", "default": "refused", "refused": "refused",
              "hardship": "hardship", "dispute": "dispute", "service_error": "service_error"},
    fail_max=3,                                             # three tries in total for the same promise
    human_limit=1,                                          # a person: straight away
    notalk_limit=2,                                         # say once it only takes a moment; second time close
    closed_day_move="before",                               # 4.6: nearest business day BEFORE the named closed day
    weekday_rule="first_after_plus7",                       # 4.7
    vague_again="deadline",                                 # 4.6: after the one ask, propose a date (the latest date when the week's last day is past it)
    above_full="agree",                                     # 4.5: record the full amount
    asides={
        "robot": {"when": "asks whether they are talking to a robot, a machine or an AI", "say": "I am Kestrel Bank's digital assistant."},
        "scam": {"when": "asks whether this call is a scam or genuine", "say": "You are welcome to hang up and call the number on the back of your card or on your statement."},
    })

BANDS = SPEC["bands"]
PREPARE_BODY = fl.products_from_vars() + r'''
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
a1 = bd_after(today)                                    # 4.8 attempt 1: the next business day after the call date
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
            floor = min(2.0 * float(p.get('minimum_payment')), past_due)   # memo item 3: twice the minimum payment, never more than the overdue amount
        except Exception:
            floor = past_due
        floor_name = 'twice the minimum payment'
    else:
        words = ptype.replace('_', ' ') if ptype else 'loan'
        try:
            floor = float(p.get('instalment_amount'))               # 4.2
        except Exception:
            floor = past_due
        floor_name = 'instalment amount'
    days_late = int(float(p.get('days_late') or 0))
    if 1 <= days_late <= 10:
        d21 = today + datetime.timedelta(days=21)                    # band F: 21 calendar days, last business day before if needed
        deadline = d21 if isbd(d21) else prev_bd(d21)
        rungs = [('full_or_floor', a1)]
    else:
        deadline = addbd(today, 5)                                   # band S (and over 45): 5th business day (memo item 1)
        rungs = [('full_or_floor', a1), ('floor', deadline)]        # memo item 2: two attempts
    register_product(vars, pid, words, past_due, floor, floor_name, deadline, rungs)
    items.append((words, past_due, days_late, deadline))
name = str(vars.get('title') or '') + ' ' + str(vars.get('last_name') or '')
statement = 'Thank you, ' + name + '. I am calling from the arrears team about an overdue payment. '
for w, pd, dl_, dd in items:
    statement += 'Your ' + w + ' has an overdue amount of ' + fmt(pd) + ', ' + str(dl_) + ' days overdue. '
if len(items) == 1:
    statement += 'Are you able to clear the overdue amount today?'
else:
    statement += 'Are you able to clear all of these today?'
lines = []
for w, pd, dl_, dd in items:
    lines.append(w + ': overdue ' + fmt(pd) + ', ' + str(dl_) + ' days overdue, latest date ' + txt_short(dd))
vars['products_facts'] = '; '.join(lines)
vars['outcome'] = 'no_promise'
vars['reason'] = 'RF'
'''
PREPARE = POLICY.prepare_code(PREPARE_BODY, "statement", fallbacks={
    "say_next": "Thank you. I am calling from the arrears team about an overdue payment. Are you able to clear the overdue amount today?",
    "products_facts": ""})

nodes["load_account"] = fl.api_node(
    "load_account", fl.api_tool(API, "get_account", description="Get the products in arrears.", retries=2),
    [fl.always("prepare")], mapping=[{"path": "data.products", "variable": "products"}])
nodes["prepare"] = fl.code_node("prepare", PREPARE, [fl.always("negotiate")])

TOPIC_DESC = ("What the customer's LATEST message says, if it is one of these. "
              "hardship = mentions illness, a bereavement, losing their job, or anything of that kind (this wins over every other value, even when they also name a date or an amount). "
              "already_paid = says they have ALREADY paid the overdue amount (not 'I will pay'). "
              "dispute = says the amount or product is not theirs, they never had it ('that is not mine'). "
              "new_plan = asks for a plan, lower instalments, or more time in general. Saying an amount is too much is NOT new_plan; a different amount or date for a payment is NOT new_plan." + fl.PLAN_REQUEST_CLAUSE + " "
              "human = asks to speak to a person, a human, an agent or a colleague. "
              "no_talk = says they do not want to talk or do not want this call (not a refusal to pay). "
              "none = anything else: offers, yes or no answers, refusals to pay, questions.")
STANCE_DESC = ("The customer's answer to the agent's LATEST payment proposal, from the customer's latest message only. "
               "accept = agrees to exactly what the agent proposed ('yes', 'okay', 'fine', 'that works'). "
               "refuse = a flat refusal, a no with no date and no amount ('no', 'I can't', 'not today'), or a non-answer that avoids the question ('I don't know', 'maybe'). "
               "too_much = says the full amount is too much, too high, or that they cannot pay that much or all of it, without naming an amount. "
               "offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. "
               "other = anything else: a question, small talk, a request.")
KIND_DESC = ("From the customer's LATEST message only. exact = they name a specific payment day (a date, a weekday, 'tomorrow', 'the 30th') or a specific amount of money, or both. "
             "vague = only a vague period without a day ('next week', 'end of the month', 'when I get paid'); also 'I don't know the exact day' after being asked for it. "
             "none = no date, amount or period in the latest message (also 'yes', 'no', questions).")
FOR_DESC = ("Which product the customer's LATEST message is about, in the order the agent listed the products: first, second or third "
            "(match the product they name, e.g. 'the credit card', 'the car loan'); pick that one even when they mention the other products only to "
            "refuse or exclude them. all = all of them, everything, both, or one date or amount for everything. none = no product named.")
DATE_DESC = ("The payment date the customer names in their LATEST message, as they said it. 'next <weekday>' is the first such weekday after today (seven days later if today is that weekday); "
             "'this <weekday>' or a bare weekday is the same day (today if today is that weekday). Leave it empty when the latest message names no specific day.")
AMOUNT_DESC = ("The amount of money the customer offers to pay in their LATEST message, as a number ('six forty' = 640). "
               "Leave it empty when the latest message names no amount. A day of the month is not an amount.")
REF_DESC = ("Whether the customer's LATEST message names the payment amount BY REFERENCE instead of as a number. "
            "floor = the lowest amount the agent can accept: 'the minimum', 'the floor', 'the instalment', 'the lowest amount', 'twice the minimum'. "
            "full = the whole overdue amount ('all of it', 'the full amount', 'everything') ONLY when they offer to pay it; a message saying they cannot or will not pay that amount is none. none = no such reference (also when they say a number).")
CONFIRM_DESC = ("The customer's answer to the read-back question 'Shall I record that?', from their latest message only. "
                "yes = a clear yes ('yes', 'please', 'go ahead', 'that's right'). "
                "change = they give a different amount or a different date for a promise. "
                "no = a plain no without a new amount or date. other = anything else, for example a question.")

topic = fl.ext("topic", ["none", "hardship", "already_paid", "dispute", "new_plan", "human", "no_talk"], TOPIC_DESC)
offer_for = fl.ext("offer_for", ["none", "all", "first", "second", "third"], FOR_DESC)
TOPIC_TRS = POLICY.topic_transitions()

FACTS = ("FACTS\n- Products: {{products_facts}}.\n- Today: {{today_text}}.\n")
COMMON = ("- If asked whether you are a robot or an AI: say exactly \"I am Kestrel Bank's digital assistant.\" If asked whether this is a scam: they are welcome to hang up and call the number on the back of their card or on their statement.\n"
          "- Nothing else is on the table: no discount, no waiver, no payment holiday, no plan, no fees, no credit file, no legal action, no 'collectors'. Never ask the customer how much they can pay: the system proposes every amount.\n"
          "- A question these facts do not answer: say exactly \"I don't have that information.\"\n"
          "- No tool call is allowed here. Never say that a promise is recorded.\n")

NEGOTIATE = ("You are talking with {{title}} {{last_name}}, who is verified, about an overdue payment. The line you just said and the offer in STATE were decided by the system from the bank's rules.\n"
             "- Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. The only offer you may make is the current offer in STATE, word for word.\n"
             "- If the customer asks a question or says something else, answer it in one short sentence, then ask the current offer again.\n"
             + COMMON + FACTS)
neg_ext = [topic, POLICY.stance_extraction(STANCE_DESC), offer_for] + POLICY.offer_extraction(DATE_DESC, AMOUNT_DESC, KIND_DESC, ref_desc=REF_DESC)
neg_trs = TOPIC_TRS + POLICY.offer_guard_transitions() + POLICY.stance_transitions()
nodes["negotiate"] = POLICY.negotiate_node(NEGOTIATE, neg_ext, neg_trs)

CONFIRM = ("You read back the promise and asked \"Shall I record that?\". It is recorded only after a clear yes.\n"
           "- If the customer asks something, answer it in one short sentence, then ask again: \"Shall I record that?\".\n"
           + COMMON + FACTS)
nodes["confirm"] = POLICY.confirm_node(CONFIRM, CONFIRM_DESC, DATE_DESC, AMOUNT_DESC, topic_entry=topic, topic_trs=TOPIC_TRS, ref_desc=REF_DESC)

HS_ANSWER_DESC = ("From the customer's LATEST message. support_yes = they want to be put through to the customer care team. "
                  "support_no = they do not want to be put through, say no to that offer, or say they cannot pay and want nothing more. "
                  "accept_offer = they agree to the date and amount the agent just proposed. "
                  "none = anything else, for example a question.")
HARDSHIP = ("The customer mentioned a hardship (illness, a bereavement, job loss or the like). You said \"I am sorry to hear that.\" and offered once to put them through to the customer care team.\n"
            "- Make NO persuasion attempt. Never propose an amount or a date yourself.\n"
            "- If they ask a question, answer in one short sentence and wait for their answer: the customer care team is offered once (on entering), never again.\n"
            + COMMON + FACTS)
nodes["hardship"] = POLICY.hardship_node(HARDSHIP, HS_ANSWER_DESC, KIND_DESC, DATE_DESC, AMOUNT_DESC, ref_desc=REF_DESC)

WRAP_DESC = ("From the customer's LATEST message, after the agent said the promise is recorded and asked whether there is anything else. "
             "done = nothing else ('no', 'that's all', 'thanks', 'goodbye'). "
             "human = asks to speak to a person, a human or an agent. "
             "new_plan = asks for a plan, lower instalments or more time in general. "
             "change = asks to change, move or cancel a promise just recorded. "
             "question = asks a question. other = anything else.")
WRAPUP = ("The promises in STATE are recorded. You said so and asked whether there is anything else.\n"
          "- If the customer asks a question, answer it in one or two sentences from these facts or say \"I don't have that information.\", then ask whether there is anything else you can help with.\n"
          "- A recorded promise cannot be changed or cancelled on this call.\n"
          + COMMON + FACTS)
nodes["wrapup"] = POLICY.wrapup_node(WRAPUP, WRAP_DESC)

POLICY.add_event_nodes(nodes)
POLICY.record_nodes(nodes, API)

for q, fin, line in [("restructuring", "fin_transferred_restructuring", "I will put you through to the team that can help with that."),
                     ("support", "fin_transferred_support", "I will put you through to our customer care team now."),
                     ("general", "fin_transferred_human", "I will put you through to a colleague now.")]:
    nodes[f"xfer_{q}"] = fl.api_node(
        f"xfer_{q}", fl.api_tool(API, "transfer_to_agent", baked={"queue": q}, description="Transfer.", retries=1),
        [fl.always(fin)], on_enter={"type": "tts", "text": line})

close_call = fl.close_call_tool(
    API,
    outcome_desc="promise: a promise was recorded. paid: already paid. transferred: handed to a person. no_promise: verified, no promise. not_verified: identity not passed. not_reached: the customer was not reached.",
    reason_desc="The dialler code: PRM, AP, TRS, TRH, TSP, RF, HSHP, DSP, SVC, IDF, IDD, CBK, NCB, WN, DEC, UNC.")

SYSTEM = ("You are Kestrel Bank's digital assistant on an outbound phone call to {{title}} {{last_name}}. Speak English. Keep every turn to one or two short sentences. Once identity is confirmed, address the customer as {{title}} {{last_name}}.\n"
          "Always:\n"
          "- If asked whether you are a robot or an AI: say exactly \"I am Kestrel Bank's digital assistant.\", then continue.\n"
          "- If asked whether this is a scam: say they are welcome to hang up and call the number on the back of their card or on their statement, then continue.\n"
          "- Never invent figures, dates or reasons. A question you cannot answer from the tools: say \"I don't have that information.\"\n"
          "- Never offer a discount, waiver, payment holiday, plan or any term you were not given. Never mention fees, the credit file, legal action or collectors.\n"
          "- Do not say goodbye or end the call yourself: the call is closed for you.\n"
          "- Call at most one tool per message. When a rule says to call a tool, call it: saying it is not enough.\n"
          "- After every tool result, speak to the customer or call the next tool. Never end a turn with nothing. Follow what_to_do_next in a tool result.\n"
          "- Say amounts as plain numbers, for example 420.50, and dates as weekday, day and month, for example Friday 16 October.")

wf = fl.assemble(INITIAL, nodes, SYSTEM, [close_call], conduct=True)

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT / "out/kestrel.workflow.json"
    fl.write_workflow(wf, out)
    print("nodes:", len(nodes), "->", out)
