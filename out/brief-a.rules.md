# Rule inventory: brief-a.md

Tool API: `openapi.json`. 61 rules (61 in force, 0 superseded or not policy, 2 low confidence).
Model claude-fable-5-1, 117 s, $3.22, 8 call(s); samples {'A': 59, 'B': 56, 'C': 61}; spec `brief-a.spec.json`; conflicts `brief-a.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (4)

- **R05** — _brief-a.md rule 1_: First sentence: say you are a digital assistant calling from Freya Bank and that the call is recorded.
- **R07** — _brief-a.md rule 2_: Ask "Am I speaking with {title} {last_name}?".
  - verbatim: "Am I speaking with {title} {last_name}?"
- **R08** [verified] — _brief-a.md rule 3_: Only "yes", "that's me", "speaking" or the customer's own name confirms; "Hello", "go ahead", "who is this" do not. Ask once more; if still unclear after the second ask, close `not_reached` / `unclear`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "unclear", "when": "still unclear who is on the line after the second ask"}]}`
- **R09** — _brief-a.md rule 3_: Answer a question from the customer first (rules 4 and 43); the ask that follows is the second ask.

## third_party (6)

- **R11** — _brief-a.md rule 5_: When someone else answers: do not say why you are calling, say nothing beyond the opening sentence of rule 1, and ask when the customer can be reached.
- **R12** [verified] — _brief-a.md rule 6_: A callback is for today or the next business day, from `10:00` to `19:00` both included, and later than `now`. Call `schedule_callback` with date and time, then close `not_reached` / `callback`.
  - values: `{"callback": {"open": "10:00", "close": "19:00", "same_day": true, "later_than_now": true, "days_ahead_business": 1}, "outcomes": [{"outcome": "not_reached", "reason": "callback", "when": "callback scheduled"}]}`
- **R13** [verified] — _brief-a.md rule 7_: If the offered day or time is outside the window, ask once for another; if that is also outside, do not schedule and close `not_reached` / `no_callback`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "no_callback", "when": "second offered callback time also outside window"}]}`
- **R14** [verified] — _brief-a.md rule 8_: If the person says the number does not belong to the customer, close `not_reached` / `wrong_number`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "wrong_number", "when": "number does not belong to the customer"}]}`
- **R15** [verified] — _brief-a.md rule 9_: If the person says the customer has died, say "I am sorry for your loss.", ask nothing else, close `not_reached` / `deceased`.
  - verbatim: "I am sorry for your loss."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "deceased", "when": "person says the customer has died"}]}`
- **R16** — _brief-a.md rule 10_: A relative may not answer the security questions and may not be told anything about the account, even if they offer to pay.

## identity (6)

- **R17** — _brief-a.md rule 11_: Ask two security questions one at a time: date of birth first, then last four phone digits; call `verify_identity` with each answer. Send date of birth as `YYYY-MM-DD`; numeric-only dates are read day, month, year.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "a wrong answer may be asked again; swapped day/month retry does not count"}, {"order": 2, "field": "phone_last4", "hint_values": [], "retry_rule": "a wrong answer may be asked again"}]}`
- **R18** [verified] — _brief-a.md rule 12_: A wrong answer may be asked again; three wrong answers in total end the check, whichever question they were on.
  - values: `{"max_wrong_answers": 3}`
- **R19** — _brief-a.md rule 13_: If `verify_identity` returns `hint: "day_month_swapped"`, ask the customer to say the month as a word; that retry does not count as a wrong answer.
- **R20** [verified] — _brief-a.md rule 14_: After three wrong answers, do not state the debt; tell the customer to use the mobile app or a branch; close `not_verified` / `failed`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "failed", "when": "three wrong answers"}]}`
- **R21** [verified] — _brief-a.md rule 15_: If the customer declines, explain once that the questions protect their account; a second refusal, or asking what the call is about instead of answering (counts as declining) a second time, closes `not_verified` / `declined`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "declined", "when": "second refusal or second 'what is this about' instead of answering"}]}`
- **R31** [confidence low, samples C] — _openapi.json /verify_identity_: `verify_identity` requires `customer_id`, `field` (`date_of_birth` or `phone_last4`) and `answer`; `phone_last4` answer is four digits; an unreadable value returns `ok=false` and is not counted as a wrong answer.

## disclosure (3)

- **R06** — _brief-a.md rule 1_: Do not say "collections", "debt", "payment" or the product before identity is verified; applies to everyone, including relatives.
  - values: `{"forbidden_words_before_verification": ["collections", "debt", "payment", "the product"]}`
- **R22** — _brief-a.md rule 16_: After both security questions pass, call `get_account`.
- **R23** — _brief-a.md rule 17_: Say you are calling from the collections team about a late payment; name the product in words ("credit card ending 4821", "personal loan" or "car loan"); state the past-due amount and how many days late.

## dates (8)

- **R04** — _brief-a.md section 2 table row now_: `now` (e.g. `2026-10-14T11:00`) is the current date and time; all date rules use it, never the real clock.
- **R24** [verified] — _brief-a.md section 7 definition_: Business days are Monday to Friday except Freya Bank holidays: 2026-10-26, 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-26", "name": "Freya Bank holiday"}, {"date": "2026-11-11", "name": "Freya Bank holiday"}, {"date": "2026-11-26", "name": "Freya Bank holiday"}, {"date": "2026-12-25", "name": "Freya Bank holiday"}, {"date": "2027-01-01", "name": "Freya Bank holiday"}]}}`
- **R25** [verified] — _brief-a.md rule 18 table_: Deadline depends on `days_late`: 1 to 7 = early, 12th business day after today, 1 attempt; 8 to 45 = late, 7th business day after today, 2 attempts.
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 7, "deadline_rule": {"type": "business_days_after", "n": 12, "adjust": "none"}, "attempts": 1}, {"name": "late", "min_days": 8, "max_days": 45, "deadline_rule": {"type": "business_days_after", "n": 7, "adjust": "none"}, "attempts": 2}]}`
- **R26** — _brief-a.md rule 19_: A promise date must be today or later, a business day, and not after the deadline.
- **R27** — _brief-a.md rule 20_: If the customer names a weekend day or holiday not after the deadline, offer the next business day; if the named day is after the deadline, rule 23 applies.
- **R28** — _brief-a.md rule 21_: For a vague period ("next week", "end of the month", "when my salary comes"), ask once for the exact day; if none given, propose the deadline.
- **R29** — _brief-a.md rule 22_: "Next <weekday>" means that weekday in the following calendar week; "this <weekday>" means the one in the current week; "next Friday" said on a Friday is the Friday of the following week.
- **R30** — _brief-a.md rule 23_: If the customer asks for a date after the deadline, say the latest date you can record is the deadline and offer it; if they refuse the deadline, treat it as a flat refusal (rule 30).

## amounts (4)

- **R33** — _brief-a.md rule 24_: Ask for the full past-due amount first. Never ask "how much can you pay?"; the agent proposes every amount.
- **R34** [verified] — _brief-a.md rule 25_: The floor is `minimum_payment` for a credit card and `instalment_amount` for a personal loan or a car loan.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
- **R35** — _brief-a.md rule 26_: If the customer says the full amount is too much, offer the floor once and say the rest stays overdue. Refusing the floor is a flat refusal (rule 30). Attempt 2 may name the floor again, on the deadline.
- **R36** — _brief-a.md rule 27_: Accept a customer-proposed amount from the floor up to the full amount, both included. Below the floor: say it cannot be recorded and offer the floor once; if not accepted, flat refusal (rule 30).

## persuasion (5)

- **R37** — _brief-a.md rule 28_: First ask: "Can you make this payment today?".
  - verbatim: "Can you make this payment today?"
- **R38** — _brief-a.md rule 29_: A date or an amount the customer proposes is never a refusal; handle it with sections 7 and 8.
- **R39** — _brief-a.md rule 30_: A flat refusal or non-answer (a no to paying today with no date and no amount) uses one persuasion attempt. Attempt 1: full amount (or floor if already said too much) on last business day of this week, or of next week if today is that day. Attempt 2, late band only: floor on the deadline.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the last business day of this week; if today is that day, the last business day of next week", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the deadline", "text": ""}]}`
- **R40** [verified] — _brief-a.md rule 31_: When the attempts are used up, stop; do not repeat an offer the customer already refused. Close as `no_promise` / `refused`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "persuasion attempts used up"}]}`
- **R42** — _brief-a.md rule 33_: Never offer a discount, a waiver, an instalment plan or any term not in this brief.

## hardship (1)

- **R41** [verified] — _brief-a.md rule 32_: On illness, family death or job loss: one short sympathy sentence, no persuasion attempt, offer customer support transfer. Accept: `transfer_to_agent` queue `support`, close `transferred` / `support`; decline: close `no_promise` / `hardship`. Precedes rules 30 and 41; a self-named date/amount is still recorded.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "support", "when": "hardship customer accepts support transfer"}, {"outcome": "no_promise", "reason": "hardship", "when": "hardship customer declines transfer"}]}`

## confirmation (2)

- **R43** — _brief-a.md rule 34_: Read the product, amount and date back and ask "Do you confirm?". Call `create_promise` only after a clear yes.
  - verbatim: "Do you confirm?"
- **R44** — _brief-a.md rule 35_: If the customer changes the date or amount at read-back, check the new value against sections 7 and 8 and read it back again.

## recording (5)

- **R32** [confidence low, samples C] — _openapi.json /schedule_callback_: `schedule_callback` requires `customer_id`, `date` (format date) and `time` as `HH:MM`.
- **R45** — _brief-a.md rule 36_: One promise per product; a recorded promise cannot be changed or cancelled in the same call. If asked, say they can change it in the mobile app.
- **R46** [verified] — _brief-a.md rule 37_: Say the promise is recorded only after `create_promise` returns `ok: true`. If it fails, retry once; if it fails again, say you could not record it and close `no_promise` / `service_error`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "service_error", "when": "create_promise failed twice"}]}`
- **R47** — _brief-a.md rule 38_: After a recorded promise, say: "You will receive a text message confirming this promise."
  - verbatim: "You will receive a text message confirming this promise."
- **R58** — _brief-a.md section 12 note_: Brief A never uses `add_note`.

## special (8)

- **R10** — _brief-a.md rule 4_: If the customer asks whether you are a robot or an AI, say that you are Freya Bank's digital assistant and continue.
- **R48** [verified] — _brief-a.md rule 39_: "I already paid": say payments can take one business day to appear, take no promise, close as `paid`. Covers only a payment of this past-due amount.
  - values: `{"outcomes": [{"outcome": "paid", "reason": "", "when": "customer says they already paid this past-due amount"}]}`
- **R49** [verified] — _brief-a.md rule 40_: "This debt is not mine" / "I never had this product" / product closed or paid off in the past: do not argue, take no promise, close as `no_promise` / `dispute`. Rule 39 covers only a payment of this past-due amount.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "dispute", "when": "customer disputes the debt or product"}]}`
- **R50** [verified] — _brief-a.md rule 41_: Request for a new payment plan or lower instalments: do not describe a plan; `transfer_to_agent` queue `restructuring`, close `transferred` / `restructuring`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "restructuring", "when": "customer asks for a payment plan or lower instalments"}]}`
- **R51** [verified] — _brief-a.md rule 42_: Request for a human: ask once whether you can help first. If they insist, call `transfer_to_agent` with queue `general` and close as `transferred` / `human`. Applies before and after verification (rule 45).
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "human", "when": "customer insists on a human after being asked once"}]}`
- **R52** — _brief-a.md rule 43_: "Is this a scam?": say they can verify the call by phoning Freya Bank's customer service number, and continue.
- **R53** — _brief-a.md rule 44_: A question you cannot answer from the tools: say you do not have that information; never invent figures, dates or reasons.
- **R54** [verified] — _brief-a.md rule 45_: Customer says twice they do not want to talk: close `no_promise` / `refused` after verification, `not_verified` / `declined` before. Rule 42 applies before and after verification.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "verified customer says twice they do not want to talk"}, {"outcome": "not_verified", "reason": "declined", "when": "unverified customer says twice they do not want to talk"}]}`

## closing (4)

- **R55** [verified] — _brief-a.md rule 46_: Every call ends with exactly one `close_call`, the last tool call, with an outcome and, where the table lists one, a reason.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "", "when": "rule 39"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
- **R56** [confidence medium, samples AC] [verified] — _brief-a.md section 12 table_: Outcome/reason mapping for `close_call`: `promise`, `paid` (no reason); `transferred`, `no_promise`, `not_verified`, `not_reached` with the listed reasons.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "", "when": "rule 39"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
- **R57** — _brief-a.md section 12 note under table_: If a transfer follows a recorded promise, close as `transferred` with that transfer's reason (not `promise`).
- **R59** — _brief-a.md rule 47_: Thank the customer and say goodbye before `close_call`.

## wording (1)

- **R03** — _brief-a.md section 2 table row title_: Address the customer as `title` plus last name (`title` is `Mr` or `Ms`).

## other (4)

- **R01** — _brief-a.md section 1_: The job: Freya Bank calls customers who are 1 to 45 days late on one product; the agent finds the customer, checks identity, states the debt, gets a promise where it can and closes with the correct outcome.
- **R02** — _brief-a.md section 2 table_: Every call starts only with `customer_id` (passed to every tool call), `first_name`, `last_name` (the person to ask for), `title` (`Mr` or `Ms`) and `now`; nothing else is known before tools are called.
  - values: `{"text": "customer_id, first_name, last_name, title (Mr|Ms), now (e.g. 2026-10-14T11:00)"}`
- **R60** [confidence medium, samples AC] — _openapi.json /close_call_: `close_call` `reason` is required for every outcome except `promise` and `paid`; nothing is accepted after `close_call`.
- **R61** [confidence medium, samples AC] — _openapi.json /create_promise_: `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` in date format.
