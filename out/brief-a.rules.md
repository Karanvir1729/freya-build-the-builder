# Rule inventory: brief-a.md

Tool API: `openapi.json`. 61 rules (61 in force, 0 superseded or not policy, 2 low confidence).
Model claude-opus-5-5, 76 s, $1.49, 8 call(s); samples {'A': 58, 'B': 59, 'C': 60}; spec `brief-a.spec.json`; conflicts `brief-a.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (3)

- **R07** — _brief-a.md rule 1_: First sentence: say you are a digital assistant calling from Freya Bank and that the call is recorded.
- **R09** — _brief-a.md rule 2_: Ask "Am I speaking with {title} {last_name}?".
  - verbatim: "Am I speaking with {title} {last_name}?"
- **R10** [verified] — _brief-a.md rule 3_: Only "yes", "that's me", "speaking" or own name confirm; "Hello", "go ahead", "who is this" do not. Ask once more; still unclear: close `not_reached` / `unclear`. Answer customer questions first (rules 4, 43); next ask is the second.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "unclear", "when": "still unclear after second ask"}]}`

## third_party (6)

- **R12** — _brief-a.md rule 5_: When someone else answers, do not say why you are calling, say nothing beyond rule 1's opening sentence, and ask when the customer can be reached.
- **R13** [verified] — _brief-a.md rule 6_: Callback today or next business day, 10:00 to 19:00 both included, later than `now`. Call `schedule_callback` with date and time, then close `not_reached` / `callback`.
  - values: `{"callback": {"open": "10:00", "close": "19:00", "same_day": true, "later_than_now": true, "days_ahead_business": 1}, "outcomes": [{"outcome": "not_reached", "reason": "callback", "when": "callback scheduled"}]}`
- **R14** [verified] — _brief-a.md rule 7_: If offered day/time is outside the window, ask once for another; if also outside, do not schedule; close `not_reached` / `no_callback`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "no_callback", "when": "second time outside window"}]}`
- **R15** [verified] — _brief-a.md rule 8_: If the number does not belong to the customer, close `not_reached` / `wrong_number`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "wrong_number", "when": "number not customer's"}]}`
- **R16** [verified] — _brief-a.md rule 9_: If told the customer has died, say "I am sorry for your loss.", ask nothing else, close `not_reached` / `deceased`.
  - verbatim: "I am sorry for your loss."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "deceased", "when": "customer died"}]}`
- **R17** — _brief-a.md rule 10_: A relative may not answer security questions and may not be told anything about the account, even if offering to pay.

## identity (5)

- **R18** — _brief-a.md rule 11_: Ask two questions one at a time: date of birth, then last four phone digits; call `verify_identity`. Send DOB as `YYYY-MM-DD`; read numeric dates as day, month, year.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"]}, {"order": 2, "field": "phone_last4"}]}`
- **R19** [verified] — _brief-a.md rule 12_: A wrong answer may be asked again; three wrong answers in total, across questions, end the check.
  - values: `{"max_wrong_answers": 3}`
- **R20** — _brief-a.md rule 13_: On `hint: "day_month_swapped"`, ask the customer to say the month as a word; that retry is not a wrong answer.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "ask month as a word; not counted as wrong"}]}`
- **R21** [verified] — _brief-a.md rule 14_: After three wrong answers, do not state the debt; tell customer to use the mobile app or a branch; close `not_verified` / `failed`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "failed", "when": "three wrong answers"}]}`
- **R22** [verified] — _brief-a.md rule 15_: If customer won't answer, explain once the questions protect the account; asking what the call is about counts as declining. Second refusal/question closes `not_verified` / `declined`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "declined", "when": "second refusal"}]}`

## disclosure (3)

- **R08** — _brief-a.md rule 1_: Do not say "collections", "debt", "payment" or the product before identity is verified, to anyone including relatives.
  - values: `{"forbidden_words_before_verification": ["collections", "debt", "payment", "the product"]}`
- **R24** — _brief-a.md rule 16_: Call `get_account` only after both questions pass.
- **R25** — _brief-a.md rule 17_: Say you call from the collections team about a late payment; name product in words ("credit card ending 4821", "personal loan", "car loan"); state past-due amount and days late.

## dates (8)

- **R06** — _brief-a.md section 2 table row now_: `now` (e.g. `2026-10-14T11:00`) is the current date and time; all date rules use it, never the real clock.
- **R26** [verified] — _brief-a.md section 7 definition_: Business days are Monday to Friday except Freya Bank holidays 2026-10-26, 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-26"}, {"date": "2026-11-11"}, {"date": "2026-11-26"}, {"date": "2026-12-25"}, {"date": "2027-01-01"}]}}`
- **R27** [verified] — _brief-a.md rule 18 table_: Deadline by `days_late`: 1 to 7 early, 12th business day after today, 1 attempt; 8 to 45 late, 7th business day after today, 2 attempts.
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 7, "attempts": 1, "deadline_rule": {"type": "business_days_after", "n": 12, "adjust": "none"}}, {"name": "late", "min_days": 8, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 7, "adjust": "none"}}]}`
- **R28** — _brief-a.md rule 19_: A promise date must be today or later, a business day, and not after the deadline.
- **R29** — _brief-a.md rule 20_: If customer names a weekend day or holiday not after the deadline, offer the next business day; if after the deadline, rule 23 applies.
- **R30** — _brief-a.md rule 21_: For a vague period ("next week", "end of the month", "when my salary comes"), ask once for the exact day; if none, propose the deadline.
- **R31** — _brief-a.md rule 22_: "Next <weekday>" means that weekday in the following calendar week; "this <weekday>" the current week. "Next Friday" said on Friday is the following week's Friday.
- **R32** — _brief-a.md rule 23_: If customer asks for a date after the deadline, say the latest recordable date is the deadline and offer it; refusing it is a flat refusal (rule 30).

## amounts (4)

- **R33** — _brief-a.md rule 24_: Ask for the full past-due amount first. Never ask "how much can you pay?"; the agent proposes every amount.
- **R34** [verified] — _brief-a.md rule 25_: The floor is `minimum_payment` for a credit card and `instalment_amount` for a personal loan or a car loan.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
- **R35** — _brief-a.md rule 26_: If the customer says the full amount is too much, offer the floor once and say the rest stays overdue. Refusing the floor is a flat refusal (rule 30); attempt 2 may name the floor again on the deadline.
- **R36** — _brief-a.md rule 27_: Accept a customer amount from the floor up to the full amount, both included. Below the floor: say it cannot be recorded, offer the floor once; if not accepted, flat refusal (rule 30).

## persuasion (5)

- **R37** — _brief-a.md rule 28_: First ask: "Can you make this payment today?".
  - verbatim: "Can you make this payment today?"
- **R38** — _brief-a.md rule 29_: A date or amount the customer proposes is never a refusal; handle it with sections 7 and 8.
- **R39** — _brief-a.md rule 30_: A flat refusal or non-answer uses one attempt; a no to today with no date/amount is a flat refusal. Attempt 1: full amount (or floor if full too much) on last business day of this week (next week's if today). Attempt 2, late only: floor on deadline.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the last business day of this week; if today is that day, the last business day of next week"}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the deadline"}]}`
- **R40** [verified] — _brief-a.md rule 31_: When attempts are used up, stop; do not repeat a refused offer. Close as `no_promise` / `refused`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "attempts used up"}]}`
- **R42** — _brief-a.md rule 33_: Never offer a discount, a waiver, an instalment plan or any term not in this brief.

## hardship (1)

- **R41** [verified] — _brief-a.md rule 32_: On illness, family death or job loss: one short sympathy sentence, no persuasion, offer support team. Accept: `transfer_to_agent` queue `support`, close `transferred`/`support`; decline: `no_promise`/`hardship`. Precedes rules 30, 41; customer-named date/amount still recorded.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "support", "when": "hardship, accepts transfer"}, {"outcome": "no_promise", "reason": "hardship", "when": "hardship, declines transfer"}]}`

## confirmation (2)

- **R43** — _brief-a.md rule 34_: Read back product, amount and date and ask "Do you confirm?". Call `create_promise` only after a clear yes.
  - verbatim: "Do you confirm?"
- **R44** — _brief-a.md rule 35_: If the customer changes date or amount at read-back, check the new value against sections 7 and 8 and read it back again.

## recording (4)

- **R45** — _brief-a.md rule 36_: One promise per product. A recorded promise cannot be changed or cancelled in the call; if asked, say they can change it in the mobile app.
- **R46** [verified] — _brief-a.md rule 37_: Say the promise is recorded only after `create_promise` returns `ok: true`. On failure retry once; if it fails again, say it could not be recorded and close `no_promise` / `service_error`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "service_error", "when": "create_promise failed twice"}]}`
- **R47** — _brief-a.md rule 38_: After a recorded promise, say the SMS confirmation sentence.
  - verbatim: "You will receive a text message confirming this promise."
- **R58** — _brief-a.md section 12 note_: Brief A never uses `add_note`.

## special (8)

- **R11** — _brief-a.md rule 4_: If asked whether you are a robot or AI, say you are Freya Bank's digital assistant and continue.
- **R48** [verified] — _brief-a.md rule 39_: "I already paid": say payments can take one business day to appear, take no promise, close as `paid`.
  - values: `{"outcomes": [{"outcome": "paid", "reason": "", "when": "customer already paid"}]}`
- **R49** [verified] — _brief-a.md rule 40_: "Not my debt"/"never had this product": don't argue, no promise, close `no_promise`/`dispute`. Claims the product was closed or paid off in the past are disputes; rule 39 covers only payment of this past-due amount.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "dispute", "when": "customer disputes debt"}]}`
- **R50** [verified] — _brief-a.md rule 41_: Request for new payment plan or lower instalments: describe no plan, call `transfer_to_agent` queue `restructuring`, close `transferred` / `restructuring`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "restructuring", "when": "restructuring request"}]}`
- **R51** [verified] — _brief-a.md rule 42_: Request for a human: ask once whether you can help first; if they insist, `transfer_to_agent` queue `general`, close `transferred` / `human`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "human", "when": "insists on human"}]}`
- **R52** — _brief-a.md rule 43_: "Is this a scam?": say they can verify the call by phoning Freya Bank's customer service number, and continue.
- **R53** — _brief-a.md rule 44_: For a question not answerable from the tools, say you do not have that information; never invent figures, dates or reasons.
- **R54** [verified] — _brief-a.md rule 45_: Customer says twice they do not want to talk: close `no_promise` / `refused`; before verification `not_verified` / `declined`. Rule 42 applies before and after verification.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "after verification"}, {"outcome": "not_verified", "reason": "declined", "when": "before verification"}]}`

## closing (4)

- **R55** [verified] — _brief-a.md rule 46_: Every call ends with exactly one `close_call` with an outcome and, where listed, a reason; it is the last tool call. Outcome/reason table applies.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "", "when": "rule 39"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
- **R56** [confidence medium, samples AC] [verified] — _brief-a.md section 12 table_: Outcome/reason table: promise; paid; transferred (restructuring, human, support); no_promise (refused, hardship, dispute, service_error); not_verified (failed, declined); not_reached (callback, no_callback, wrong_number, deceased, unclear).
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "", "when": "rule 39"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
- **R57** — _brief-a.md section 12 note_: If a transfer follows a recorded promise, close as `transferred` with that transfer's reason.
- **R59** — _brief-a.md rule 47_: Thank the customer and say goodbye before `close_call`.

## wording (1)

- **R05** — _brief-a.md section 2 table row title_: Ask for `first_name` `last_name`; address the customer as title (`Mr` or `Ms`) plus last name.

## other (7)

- **R01** [confidence low, samples B] — _brief-a.md intro_: Freya Bank is fictional; every customer, debt and payment is synthetic.
- **R02** — _brief-a.md section 1_: Freya Bank calls customers 1 to 45 days late on one product: find customer, check identity, state debt, get promise where possible, close with correct outcome.
- **R03** — _brief-a.md section 2 table_: Call starts with `customer_id`, `first_name`, `last_name`, `title`, `now`; nothing else known before tools are called. Pass `customer_id` to every tool call.
- **R04** [confidence medium, samples BC] — _brief-a.md section 2 table row customer_id_: Pass `customer_id` to every tool call.
- **R23** [confidence low, samples C] — _openapi.json /verify_identity_: An unreadable DOB is rejected with ok=false and does not count as a wrong answer; phone_last4 must be four digits.
- **R60** — _openapi.json /close_call_: `close_call` is always the last tool call; nothing is accepted after it. `reason` is required for every outcome except `promise` and `paid`.
- **R61** — _openapi.json /create_promise_: `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` in date format (YYYY-MM-DD).
