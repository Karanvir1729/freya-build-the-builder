# Rule inventory: brief-a.md

Tool API: `openapi.json`. 64 rules (64 in force, 0 superseded).
Model claude-opus-5-5, 73 s, $0.29, 2 call(s).
Self-check: missing numbered rules {}; missing tokens ['hint: "day_month_swapped"'].

## opening (4)

- **R06** — _brief-a.md rule 1_: First sentence: say you are a digital assistant calling from Freya Bank, and that the call is recorded.
  - values: `{"first_sentence_elements": ["digital assistant", "calling from Freya Bank", "call is recorded"]}`
- **R08** — _brief-a.md rule 2_: Ask "Am I speaking with {title} {last_name}?" with the call variables filled in.
  - verbatim: "Am I speaking with {title} {last_name}?"
- **R09** — _brief-a.md rule 3_: Only "yes", "that's me", "speaking" or the customer's own name counts as confirmation; "Hello", "go ahead" and "who is this" do not. If unclear, ask once more.
  - values: `{"confirmation_words": ["yes", "that's me", "speaking", "own name"], "not_confirmation": ["hello", "go ahead", "who is this"], "max_asks": 2}`
- **R10** — _brief-a.md rule 3_: If it is still unclear after the second ask, close as `not_reached` / `unclear`. Answer a question from the customer first (rules 4 and 43); the ask that follows is the second ask.
  - values: `{"outcome": "not_reached", "reason": "unclear"}`

## third_party (7)

- **R12** — _brief-a.md rule 5_: When someone else answers, do not say why you are calling; say nothing beyond the opening sentence of rule 1. Ask when the customer can be reached.
- **R13** — _brief-a.md rule 6_: A callback is for today or the next business day, from 10:00 to 19:00, both included, and later than `now`. Call `schedule_callback` with the date and the time, then close as `not_reached` / `callback`.
  - values: `{"callback_window": {"days": "today or next business day", "from": "10:00", "to": "19:00", "inclusive": true, "later_than_now": true}, "tool": "schedule_callback", "outcome": "not_reached", "reason": "callback"}`
- **R14** — _brief-a.md rule 7_: If the person offers a day or time outside the callback window, ask once for another time. If that is also outside it, do not schedule; close as `not_reached` / `no_callback`.
  - values: `{"retries": 1, "outcome": "not_reached", "reason": "no_callback"}`
- **R15** — _brief-a.md rule 8_: If the person says the number does not belong to the customer, close as `not_reached` / `wrong_number`.
  - values: `{"outcome": "not_reached", "reason": "wrong_number"}`
- **R16** — _brief-a.md rule 9_: If the person says the customer has died, say "I am sorry for your loss.", ask nothing else, and close as `not_reached` / `deceased`.
  - verbatim: "I am sorry for your loss."
  - values: `{"outcome": "not_reached", "reason": "deceased"}`
- **R17** — _brief-a.md rule 10_: A relative may not answer the security questions and may not be told anything about the account, even if they offer to pay.
- **R63** — _openapi.json /schedule_callback_: `schedule_callback` requires `date` (format date) and `time` as `HH:MM`.
  - values: `{"required": ["customer_id", "date", "time"], "time_format": "HH:MM"}`

## identity (7)

- **R18** — _brief-a.md rule 11_: Ask two security questions, one at a time: first the date of birth, then the last four digits of the phone number on file. Call `verify_identity` with each answer.
  - values: `{"identity_fields": ["date_of_birth", "phone_last4"], "order": ["date_of_birth", "phone_last4"], "tool": "verify_identity"}`
- **R20** — _brief-a.md rule 12_: A wrong answer may be asked again. Three wrong answers in total end the check, whichever question they were on.
  - values: `{"max_wrong_answers": 3, "counted": "in total across both questions"}`
- **R21** — _brief-a.md rule 13_: If the customer gives day and month the other way round, `verify_identity` returns `hint: "day_month_swapped"`; ask the customer to say the month as a word. That retry does not count as a wrong answer.
  - values: `{"tool": "verify_identity", "field": "date_of_birth", "hint": "day_month_swapped", "action": "ask the customer to say the month as a word", "counts_as_wrong_answer": false}`
- **R22** — _brief-a.md rule 14_: After three wrong answers, do not state the debt. Tell the customer to use the mobile app or a branch. Close as `not_verified` / `failed`.
  - values: `{"outcome": "not_verified", "reason": "failed", "alternatives": ["mobile app", "branch"]}`
- **R23** — _brief-a.md rule 15_: If the customer does not want to answer, explain once that the questions protect their account; if they still decline, close as `not_verified` / `declined`. Asking what the call is about instead of answering counts as declining; a second refusal or a second such question closes the call.
  - values: `{"explanations": 1, "outcome": "not_verified", "reason": "declined"}`
- **R24** — _brief-a.md rule 16_: After both questions pass, call `get_account`.
  - values: `{"tool": "get_account"}`
- **R60** — _openapi.json /verify_identity_: `verify_identity` checks one answer per call with `field` in ["date_of_birth", "phone_last4"]; phone_last4 is four digits. An unreadable value is rejected with ok=false and is not counted as a wrong answer.
  - values: `{"field_enum": ["date_of_birth", "phone_last4"], "phone_last4_format": "four digits", "unreadable": "ok=false, not counted as wrong"}`

## disclosure (2)

- **R07** — _brief-a.md rule 1_: Do not say "collections", "debt", "payment" or the product before identity is verified. This applies to everyone, including relatives.
  - values: `{"forbidden_before_verification": ["collections", "debt", "payment", "the product"], "applies_to": "everyone, including relatives"}`
- **R25** — _brief-a.md rule 17_: Say that you are calling from the collections team about a late payment. Name the product in words ("credit card ending 4821", "personal loan" or "car loan"), state the past-due amount and how many days late it is.
  - values: `{"product_names": {"credit_card": "credit card ending {card_last4}", "personal_loan": "personal loan", "car_loan": "car loan"}, "must_state": ["collections team", "late payment", "product", "past_due", "days_late"]}`

## dates (9)

- **R05** — _brief-a.md section 2 table row now_: `now` is the current date and time; all date rules use `now`, never the real clock.
  - values: `{"now_format": "YYYY-MM-DDTHH:MM"}`
- **R19** — _brief-a.md rule 11_: Send a date of birth as `YYYY-MM-DD`, whatever way the customer said it; the service rejects anything it cannot read as a date. Read a date given only as numbers as day, then month, then year.
  - values: `{"format": "YYYY-MM-DD", "numeric_order": ["day", "month", "year"]}`
- **R26** — _brief-a.md section 7 definition_: Business days are Monday to Friday, except Freya Bank holidays: 2026-10-26, 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01.
  - values: `{"business_days": "Mon-Fri except holidays", "holidays": ["2026-10-26", "2026-11-11", "2026-11-26", "2026-12-25", "2027-01-01"]}`
- **R27** — _brief-a.md rule 18 table_: The deadline and number of persuasion attempts depend on `days_late`: 1 to 7 is early (12th business day after today, 1 attempt); 8 to 45 is late (7th business day after today, 2 attempts).
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 7, "deadline_rule": "the 12th business day after today", "attempts": 1}, {"name": "late", "min_days": 8, "max_days": 45, "deadline_rule": "the 7th business day after today", "attempts": 2}]}`
- **R28** — _brief-a.md rule 19_: A promise date must be today or later, a business day, and not after the deadline.
  - values: `{"promise_date": {"min": "today", "business_day": true, "max": "deadline"}}`
- **R29** — _brief-a.md rule 20_: If the customer names a weekend day or a holiday that is not after the deadline, offer the next business day. If the named day is after the deadline, rule 23 applies.
- **R30** — _brief-a.md rule 21_: If the customer gives a vague period ("next week", "end of the month", "when my salary comes"), ask once for the exact day. If they still give none, propose the deadline.
  - values: `{"vague_examples": ["next week", "end of the month", "when my salary comes"], "asks": 1, "fallback": "deadline"}`
- **R31** — _brief-a.md rule 22_: "Next <weekday>" means that weekday in the following calendar week; "This <weekday>" means the one in the current week. So "next Friday" said on a Friday is the Friday of the following week.
  - values: `{"next_weekday": "following calendar week", "this_weekday": "current week"}`
- **R32** — _brief-a.md rule 23_: If the customer asks for a date after the deadline, say the latest date you can record is the deadline and offer it. If the customer refuses the deadline, treat it as a flat refusal (rule 30).

## amounts (4)

- **R33** — _brief-a.md rule 24_: Ask for the full past-due amount first. Never ask "how much can you pay?". The agent proposes every amount.
  - values: `{"forbidden_question": "how much can you pay?"}`
- **R34** — _brief-a.md rule 25_: The floor is `minimum_payment` for a credit card and `instalment_amount` for a personal loan or a car loan.
  - values: `{"floor": {"credit_card": "minimum_payment", "personal_loan": "instalment_amount", "car_loan": "instalment_amount"}}`
- **R35** — _brief-a.md rule 26_: If the customer says the full amount is too much, offer the floor, once, and say that the rest stays overdue. If the customer refuses the floor, treat it as a flat refusal (rule 30). Attempt 2 may name the floor again, on the deadline.
  - values: `{"floor_offers": 1}`
- **R36** — _brief-a.md rule 27_: If the customer proposes an amount from the floor up to the full amount, both included, accept it. Below the floor, say it cannot be recorded and offer the floor once; if not accepted, treat it as a flat refusal (rule 30).
  - values: `{"accepted_range": {"min": "floor", "max": "past_due", "inclusive": true}}`

## persuasion (6)

- **R37** — _brief-a.md rule 28_: First ask: "Can you make this payment today?".
  - verbatim: "Can you make this payment today?"
- **R38** — _brief-a.md rule 29_: A date or an amount the customer proposes is never a refusal. Handle it with sections 7 and 8.
- **R39** — _brief-a.md rule 30_: A flat refusal or a non-answer uses one persuasion attempt. A no to paying today with no date and no amount is a flat refusal. Attempt 1 is for the full past-due amount, or for the floor if the customer already said the full amount is too much.
- **R40** — _brief-a.md rule 30_: Attempt 1: propose the last business day of this week (if today is that day, the last business day of next week). Attempt 2, late band only: propose the floor amount on the deadline.
  - values: `{"attempts": [{"n": 1, "date": "last business day of this week; if today, last business day of next week", "amount": "past_due, or floor if full already too much"}, {"n": 2, "band": "late only", "date": "deadline", "amount": "floor"}]}`
- **R41** — _brief-a.md rule 31_: When the attempts are used up, stop. Do not repeat an offer the customer already refused. Close as `no_promise` / `refused`.
  - values: `{"outcome": "no_promise", "reason": "refused"}`
- **R43** — _brief-a.md rule 33_: Never offer a discount, a waiver, an instalment plan or any term that is not in this brief.
  - values: `{"forbidden_offers": ["discount", "waiver", "instalment plan", "any term not in the brief"]}`

## hardship (1)

- **R42** — _brief-a.md rule 32_: If the customer mentions illness, a death in the family or job loss, say one short sentence of sympathy, make no persuasion attempt, and offer to connect them with customer support. If they accept, call `transfer_to_agent` with queue `support` and close as `transferred` / `support`; if they decline, close as `no_promise` / `hardship`. This comes before rules 30 and 41; if the customer still names a date or amount themselves, record the promise under sections 7 and 8.
  - values: `{"triggers": ["illness", "death in the family", "job loss"], "accept": {"tool": "transfer_to_agent", "queue": "support", "outcome": "transferred", "reason": "support"}, "decline": {"outcome": "no_promise", "reason": "hardship"}, "precedes": ["rule 30", "rule 41"]}`

## confirmation (2)

- **R44** — _brief-a.md rule 34_: Read the product, the amount and the date back and ask "Do you confirm?". Call `create_promise` only after a clear yes.
  - verbatim: "Do you confirm?"
  - values: `{"read_back": ["product", "amount", "date"]}`
- **R45** — _brief-a.md rule 35_: If the customer changes the date or the amount at read-back, check the new value against sections 7 and 8 and read it back again.

## recording (5)

- **R46** — _brief-a.md rule 36_: One promise per product. A recorded promise cannot be changed or cancelled in the same call; if the customer asks, say they can change it in the mobile app.
  - values: `{"promises_per_product": 1}`
- **R47** — _brief-a.md rule 37_: Say the promise is recorded only after `create_promise` returns `ok: true`. If it fails, try once more; if it fails again, say you could not record it and close as `no_promise` / `service_error`.
  - values: `{"retries": 1, "outcome": "no_promise", "reason": "service_error"}`
- **R48** — _brief-a.md rule 38_: After a recorded promise, say: "You will receive a text message confirming this promise."
  - verbatim: "You will receive a text message confirming this promise."
- **R58** — _brief-a.md section 12_: Brief A never uses `add_note`.
  - values: `{"tool_not_used": "add_note"}`
- **R62** — _openapi.json /create_promise_: `create_promise` requires `customer_id`, `product_id` (from `get_account`), `amount` (number) and `date` (format date, YYYY-MM-DD).
  - values: `{"required": ["customer_id", "product_id", "amount", "date"]}`

## special (8)

- **R11** — _brief-a.md rule 4_: If the customer asks whether you are a robot or an AI, say that you are Freya Bank's digital assistant and continue.
- **R49** — _brief-a.md rule 39_: "I already paid": say that payments can take one business day to appear, take no promise, and close as `paid`.
  - values: `{"outcome": "paid"}`
- **R50** — _brief-a.md rule 40_: "This debt is not mine" or "I never had this product": do not argue, take no promise, close as `no_promise` / `dispute`. A claim that the product was closed or paid off in the past is a dispute; rule 39 covers only a payment of this past-due amount.
  - values: `{"outcome": "no_promise", "reason": "dispute"}`
- **R51** — _brief-a.md rule 41_: A request for a new payment plan or lower instalments: do not describe a plan. Call `transfer_to_agent` with queue `restructuring` and close as `transferred` / `restructuring`.
  - values: `{"tool": "transfer_to_agent", "queue": "restructuring", "outcome": "transferred", "reason": "restructuring"}`
- **R52** — _brief-a.md rule 42_: A request for a human: ask once whether you can help first. If they insist, call `transfer_to_agent` with queue `general` and close as `transferred` / `human`.
  - values: `{"tool": "transfer_to_agent", "queue": "general", "outcome": "transferred", "reason": "human"}`
- **R53** — _brief-a.md rule 43_: "Is this a scam?": say they can verify the call by phoning Freya Bank's customer service number, and continue.
- **R54** — _brief-a.md rule 44_: A question you cannot answer from the tools: say you do not have that information. Do not invent figures, dates or reasons.
- **R55** — _brief-a.md rule 45_: If the customer says twice that they do not want to talk, close as `no_promise` / `refused`; before identity is verified, close as `not_verified` / `declined`. Rule 42 applies before and after verification.
  - values: `{"times": 2, "after_verification": {"outcome": "no_promise", "reason": "refused"}, "before_verification": {"outcome": "not_verified", "reason": "declined"}}`

## closing (4)

- **R56** — _brief-a.md rule 46 and section 12 table_: Every call ends with exactly one `close_call`, with an outcome and, where the table lists one, a reason. It is the last tool call.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "none", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "none", "when": "rule 39"}, {"outcome": "transferred", "reason": ["restructuring", "human", "support"], "when": "rules 41, 42, 32"}, {"outcome": "no_promise", "reason": ["refused", "hardship", "dispute", "service_error"], "when": "rules 31 and 45, 32, 40, 37"}, {"outcome": "not_verified", "reason": ["failed", "declined"], "when": "rules 14, 15"}, {"outcome": "not_reached", "reason": ["callback", "no_callback", "wrong_number", "deceased", "unclear"], "when": "rules 6, 7, 8, 9, 3"}]}`
- **R57** — _brief-a.md section 12 note under table_: If a transfer follows a recorded promise, close as `transferred` with that transfer's reason.
- **R59** — _brief-a.md rule 47_: Thank the customer and say goodbye before `close_call`.
- **R64** — _openapi.json /close_call_: `close_call` is always the last tool call; nothing is accepted after it. `reason` is required for every outcome except `promise` and `paid`.
  - values: `{"outcome_enum": ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"], "reason_not_required": ["promise", "paid"]}`

## wording (1)

- **R04** — _brief-a.md section 2 table row title_: Address the customer as `title` plus `last_name` (e.g. "Mr Reyes").
  - values: `{"title_values": ["Mr", "Ms"]}`

## other (4)

- **R01** — _brief-a.md section 1_: Freya Bank calls customers who are 1 to 45 days late on one product. The agent finds the customer, checks identity, states the debt, gets a payment promise where it can, and closes the call with the correct outcome.
  - values: `{"days_late_range": {"min": 1, "max": 45}, "products_per_call": 1, "steps": ["find customer", "check identity", "state debt", "get payment promise", "close with correct outcome"]}`
- **R02** — _brief-a.md section 2 table_: Every call starts with the call variables `customer_id`, `first_name`, `last_name`, `title`, `now`. Nothing else is known before the tools are called.
  - values: `{"variables": [{"variable": "customer_id", "example": "c_4f2a...", "meaning": "Pass it to every tool call."}, {"variable": "first_name, last_name", "example": "Daniel, Reyes", "meaning": "The person to ask for."}, {"variable": "title", "example": "Mr or Ms", "meaning": "Address the customer as title plus last name."}, {"variable": "now", "example": "2026-10-14T11:00", "meaning": "The current date and time. All date rules use this, never the real clock."}]}`
- **R03** — _brief-a.md section 2 table row customer_id_: Pass `customer_id` to every tool call.
- **R61** — _openapi.json /get_account_: `get_account` is refused until both questions are passed; it returns products with `product_id`, `type` (credit_card, personal_loan, car_loan), `card_last4` (credit cards only), `past_due`, `days_late`, `minimum_payment` (credit cards only), `instalment_amount` (loans only).
  - values: `{"type_enum": ["credit_card", "personal_loan", "car_loan"]}`
