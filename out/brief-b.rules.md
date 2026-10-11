# Rule inventory: brief-a.md, brief-b.md

Tool API: `openapi.json`. 79 rules (71 in force, 8 superseded or not policy, 7 low confidence).
Model claude-fable-5-1, 175 s, $4.67, 9 call(s); samples {'A': 74, 'B': 74, 'C': 72}; spec `brief-b.spec.json`; conflicts `brief-b.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (4)

- **R09** — _brief-a.md rule 1_: First sentence: say you are a digital assistant calling from Freya Bank and that the call is recorded. This applies to everyone, including relatives.
- **R11** — _brief-a.md rule 2_: After the first sentence ask "Am I speaking with {title} {last_name}?".
  - verbatim: "Am I speaking with {title} {last_name}?"
- **R12** [verified] — _brief-a.md rule 3_: Only "yes", "that's me", "speaking" or the customer's own name confirms; "Hello", "go ahead", "who is this" do not. Ask once more; if still unclear after the second ask close `not_reached` / `unclear`. Answer a customer question first (rules 4, 43); the following ask is the second ask.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "unclear", "when": "still unclear whether the customer is on the line after the second ask"}]}`
- **R13** [confidence medium, samples AC] — _brief-a.md rule 3_: Answer a question from the customer first (rules 4 and 43); the ask that follows is the second ask.

## third_party (5)

- **R15** — _brief-a.md rule 5_: When someone else answers, do not say why you are calling and say nothing beyond the opening sentence of rule 1; ask when the customer can be reached.
- **R16** [verified] — _brief-a.md rule 6_: A callback is for today or the next business day, 10:00 to 19:00 both included, and later than `now`. Call `schedule_callback` with date and time, then close `not_reached` / `callback`.
  - values: `{"callback": {"open": "10:00", "close": "19:00", "same_day": true, "later_than_now": true, "days_ahead_business": 1}, "outcomes": [{"outcome": "not_reached", "reason": "callback", "when": "callback scheduled"}]}`
  - deciding quote: "A callback is for today or the next business day, from 10:00 to 19:00, both included, and later than `now`."
- **R17** [verified] — _brief-a.md rule 7_: If the offered day or time is outside the window, ask once for another time; if that is also outside, do not schedule and close `not_reached` / `no_callback`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "no_callback", "when": "second offered callback time also outside the window"}]}`
- **R18** [verified] — _brief-a.md rule 8_: If the person says the number does not belong to the customer, close `not_reached` / `wrong_number`.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "wrong_number", "when": "number does not belong to the customer"}]}`
- **R20** — _brief-a.md rule 10_: A relative may not answer the security questions and may not be told anything about the account, even if they offer to pay.

## identity (6)

- **R02** [confidence low, samples B] — _openapi.json /verify_identity_: `verify_identity` takes `field` enum `date_of_birth` or `phone_last4`; for `phone_last4` the answer is four digits. An unreadable value is rejected with `ok=false` and is not counted as a wrong answer.
  - values: `{"identity": [{"field": "date_of_birth", "order": 1, "hint_values": ["day_month_swapped"], "retry_rule": "unreadable value rejected with ok=false, not counted as a wrong answer"}, {"field": "phone_last4", "order": 2, "hint_values": [], "retry_rule": "answer is four digits"}]}`
- **R21** — _brief-a.md rule 11_: Ask two security questions one at a time: date of birth, then last four digits of the phone on file; call `verify_identity` with each answer. Send DOB as `YYYY-MM-DD`; a date given only as numbers is read day, month, year.
  - values: `{"identity": [{"field": "date_of_birth", "order": 1, "hint_values": ["day_month_swapped"], "retry_rule": "a wrong answer may be asked again; day_month_swapped retry does not count"}, {"field": "phone_last4", "order": 2, "hint_values": [], "retry_rule": "a wrong answer may be asked again"}], "text": "service rejects anything it cannot read as a date"}`
- **R22** [verified] — _brief-a.md rule 12_: A wrong answer may be asked again; three wrong answers in total end the check, whichever question they were on.
  - values: `{"max_wrong_answers": 3}`
- **R23** — _brief-a.md rule 13_: If `verify_identity` returns `hint: "day_month_swapped"`, ask the customer to say the month as a word; that retry does not count as a wrong answer.
  - values: `{"identity": [{"field": "date_of_birth", "order": 1, "hint_values": ["day_month_swapped"], "retry_rule": "ask to say the month as a word; retry not counted as a wrong answer"}]}`
- **R24** [verified] — _brief-a.md rule 14_: After three wrong answers, do not state the debt; tell the customer to use the mobile app or a branch and close `not_verified` / `failed`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "failed", "when": "three wrong answers"}]}`
- **R25** [verified] — _brief-a.md rule 15_: If the customer declines to answer, explain once that the questions protect their account; a second refusal (or asking what the call is about instead of answering, twice) closes `not_verified` / `declined`.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "declined", "when": "second refusal or second 'what is this about' instead of answering"}]}`

## disclosure (3)

- **R10** — _brief-a.md rule 1_: Do not say "collections", "debt", "payment" or the product before identity is verified; this applies to everyone, including relatives.
  - values: `{"forbidden_words_before_verification": ["collections", "debt", "payment", "the product"]}`
- **R26** — _brief-a.md rule 16_: Call `get_account` only after both security questions pass.
- **R27** **[superseded by R64]** — _brief-a.md rule 17_: Say you are calling from the collections team about a late payment; name the product in words ("credit card ending 4821", "personal loan", "car loan"); state the past-due amount and days late.
  - deciding quote: "State every late product, one sentence each, before asking for anything."

## dates (8)

- **R08** — _brief-a.md section 2 table row now_: `now` (e.g. `2026-10-14T11:00`) is the current date and time; all date rules use it, never the real clock.
- **R28** [verified] — _brief-a.md section 7 definition_: Business days are Monday to Friday except Freya Bank holidays: 2026-10-26, 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-26"}, {"date": "2026-11-11"}, {"date": "2026-11-26"}, {"date": "2026-12-25"}, {"date": "2027-01-01"}]}}`
- **R29** [verified] — _brief-a.md rule 18 table_: Deadline by `days_late`: early (1 to 7) = the 12th business day after today, 1 persuasion attempt; late (8 to 45) = the 7th business day after today, 2 attempts.
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 7, "deadline_rule": {"type": "business_days_after", "n": 12, "adjust": "none"}, "attempts": 1}, {"name": "late", "min_days": 8, "max_days": 45, "deadline_rule": {"type": "business_days_after", "n": 7, "adjust": "none"}, "attempts": 2}]}`
- **R30** — _brief-a.md rule 19_: A promise date must be today or later, a business day, and not after the deadline.
- **R31** — _brief-a.md rule 20_: If the customer names a weekend day or holiday not after the deadline, offer the next business day; if the named day is after the deadline, rule 23 applies.
- **R32** — _brief-a.md rule 21_: For a vague period ("next week", "end of the month", "when my salary comes"), ask once for the exact day; if none is given, propose the deadline.
- **R33** — _brief-a.md rule 22_: "Next <weekday>" means that weekday in the following calendar week; "this <weekday>" means the one in the current week; "next Friday" said on a Friday is the Friday of the following week.
- **R34** — _brief-a.md rule 23_: If the customer asks for a date after the deadline, say the latest date you can record is the deadline and offer it; refusing the deadline is a flat refusal (rule 30).

## amounts (4)

- **R35** — _brief-a.md rule 24_: Ask for the full past-due amount first; never ask "how much can you pay?"; the agent proposes every amount.
- **R36** [verified] — _brief-a.md rule 25_: The floor is `minimum_payment` for a credit card and `instalment_amount` for a personal loan or a car loan.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
- **R37** — _brief-a.md rule 26_: If the full amount is too much, offer the floor once and say the rest stays overdue; refusing the floor is a flat refusal (rule 30). Attempt 2 may name the floor again, on the deadline.
- **R38** — _brief-a.md rule 27_: Accept a proposed amount from the floor up to the full amount, both included; below the floor, say it cannot be recorded and offer the floor once; not accepting the floor is a flat refusal (rule 30).

## persuasion (6)

- **R39** **[superseded by R66]** — _brief-a.md rule 28_: After stating the debt, first ask "Can you make this payment today?".
  - verbatim: "Can you make this payment today?"
  - deciding quote: "First ask whether the customer can pay all of them today."
- **R40** — _brief-a.md rule 29_: A date or amount the customer proposes is never a refusal; handle it with sections 7 and 8.
- **R41** — _brief-a.md rule 30_: A flat refusal or non-answer (a no to today with no date and no amount) uses one attempt. Attempt 1: full amount (or floor if full already too much) on the last business day of this week, or of next week if today is that day; attempt 2 (late only): floor on the deadline.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the last business day of this week; if today is that day, the last business day of next week", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the deadline", "text": ""}]}`
- **R42** [verified] — _brief-a.md rule 31_: When attempts are used up, stop; do not repeat an offer the customer already refused; close `no_promise` / `refused`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "persuasion attempts used up"}]}`
- **R44** — _brief-a.md rule 33_: Never offer a discount, a waiver, an instalment plan or any term not in this brief.
- **R67** — _brief-b.md rule 5_: Persuasion attempts are counted per product.

## hardship (2)

- **R19** [verified] — _brief-a.md rule 9_: If the person says the customer has died, say "I am sorry for your loss.", ask nothing else, and close `not_reached` / `deceased`.
  - verbatim: "I am sorry for your loss."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "deceased", "when": "person says the customer has died"}]}`
- **R43** [verified] — _brief-a.md rule 32_: On illness, family death or job loss: one short sympathy sentence, no persuasion attempt, offer support transfer; accept → `transfer_to_agent` queue `support`, close `transferred` / `support`; decline → `no_promise` / `hardship`. Precedes rules 30 and 41; a date/amount the customer names is still recorded.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "support", "when": "hardship and customer accepts support transfer"}, {"outcome": "no_promise", "reason": "hardship", "when": "hardship and customer declines transfer"}]}`

## confirmation (3)

- **R45** **[superseded by R69]** — _brief-a.md rule 34_: Read the product, the amount and the date back and ask "Do you confirm?". Call `create_promise` only after a clear yes.
  - verbatim: "Do you confirm?"
  - deciding quote: "Read all promises back together and ask for one confirmation. Then call `create_promise` once per product."
- **R46** — _brief-a.md rule 35_: If the customer changes the date or the amount at read-back, check the new value against sections 7 and 8 (date and amount rules) and read it back again.
- **R69** (overrides R45) — _brief-b.md rule 7_: Replaces Brief A rule 34 for several products: read all promises back together (product, amount, date) and ask for one confirmation "Do you confirm?". After a clear yes call `create_promise` once per product.
  - verbatim: "Do you confirm?"
  - deciding quote: "Read all promises back together and ask for one confirmation. Then call `create_promise` once per product."

## recording (8)

- **R03** [confidence low, samples B] — _openapi.json /schedule_callback_: `schedule_callback` requires `customer_id`, `date` (format date) and `time` as `HH:MM`.
  - values: `{"callback": {"text": "date format date, time HH:MM"}}`
  - deciding quote: "Call `schedule_callback` with the date and the time, then close as `not_reached` / `callback`."
- **R47** — _brief-a.md rule 36_: One promise per product. A recorded promise cannot be changed or cancelled in the same call; if the customer asks, say they can change it in the mobile app.
- **R48** **[superseded by R75]** — _brief-a.md rule 37_: Say the promise is recorded only after `create_promise` returns `ok: true`. If it fails, try once more; if it fails again, say you could not record it and close as `no_promise` / `service_error`.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "service_error", "when": "create_promise failed twice"}]}`
  - deciding quote: "If one `create_promise` fails twice, keep the promises that were recorded and call `add_note` with reason `service_error` for the failed product."
- **R49** — _brief-a.md rule 38_: After a recorded promise, say word for word: "You will receive a text message confirming this promise."
  - verbatim: "You will receive a text message confirming this promise."
- **R60** **[superseded by R70]** — _brief-a.md section 12 note_: Brief A never uses `add_note`.
  - deciding quote: "For each product without a promise call `add_note` with that `product_id` and a reason: `refused`, `hardship`, `dispute`, `paid` or `service_error`."
- **R70** [verified] (overrides R60) — _brief-b.md rule 8_: Replaces 'Brief A never uses add_note': for each product without a promise call `add_note` with that `product_id` and a reason `refused`, `hardship`, `dispute`, `paid` or `service_error`, also when no product gets a promise.
  - values: `{"note_reasons": [{"reason": "refused", "when": "product refused without a promise", "text_must_contain": ""}, {"reason": "hardship", "when": "product ended without a promise due to hardship", "text_must_contain": ""}, {"reason": "dispute", "when": "product disputed", "text_must_contain": ""}, {"reason": "paid", "when": "customer says this product is already paid", "text_must_contain": ""}, {"reason": "service_error", "when": "create_promise failed twice for the product", "text_must_contain": ""}]}`
  - deciding quote: "For each product without a promise call `add_note` with that `product_id` and a reason: `refused`, `hardship`, `dispute`, `paid` or `service_error`."
- **R74** [confidence low, samples C] — _brief-b.md rule 10_: On any transfer (restructuring, support, human) add no notes at all, before or after it.
- **R75** [verified] (overrides R48) — _brief-b.md rule 11_: Say a promise is recorded only after `create_promise` returns `ok: true`; if it fails, try once more. If it fails twice, keep the recorded promises and call `add_note` with reason `service_error` for the failed product (no longer a `service_error` close).
  - values: `{"note_reasons": [{"reason": "service_error", "when": "create_promise failed twice for that product", "text_must_contain": ""}]}`
  - deciding quote: "If one `create_promise` fails twice, keep the promises that were recorded and call `add_note` with reason `service_error` for the failed product."

## special (10)

- **R14** — _brief-a.md rule 4_: If the customer asks whether you are a robot or an AI, say you are Freya Bank's digital assistant and continue.
- **R50** **[superseded by R72]** — _brief-a.md rule 39_: "I already paid": say that payments can take one business day to appear, take no promise, and close as `paid`.
  - values: `{"outcomes": [{"outcome": "paid", "reason": "", "when": "customer says they already paid this past-due amount"}]}`
  - deciding quote: "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
- **R51** **[superseded by R71]** — _brief-a.md rule 40_: "This debt is not mine" / "I never had this product" / product closed or paid off in the past: do not argue, take no promise, close as `no_promise` / `dispute`. Rule 39 covers only a payment of this past-due amount.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "dispute", "when": "customer disputes the debt or the product"}]}`
  - deciding quote: "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
- **R52** — _brief-a.md rule 41_: Request for a new payment plan or lower instalments: do not describe a plan. Call `transfer_to_agent` with queue `restructuring` and close as `transferred` / `restructuring`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "restructuring", "when": "customer asks for a new payment plan or lower instalments"}]}`
  - deciding quote: "A restructuring request still transfers the call (Brief A rule 41)."
- **R53** [verified] — _brief-a.md rule 42_: Request for a human: ask once whether you can help first. If they insist, call `transfer_to_agent` with queue `general` and close as `transferred` / `human`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "human", "when": "customer insists on a human after being asked once if the agent can help"}]}`
- **R54** — _brief-a.md rule 43_: "Is this a scam?": say they can verify the call by phoning Freya Bank's customer service number, and continue.
- **R55** — _brief-a.md rule 44_: A question you cannot answer from the tools: say you do not have that information. Do not invent figures, dates or reasons.
- **R56** [verified] — _brief-a.md rule 45_: If the customer says twice they do not want to talk, close as `no_promise` / `refused`; before identity is verified, close as `not_verified` / `declined`. Rule 42 (human request) applies before and after verification.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "refused", "when": "verified customer says twice they do not want to talk"}, {"outcome": "not_verified", "reason": "declined", "when": "unverified customer says twice they do not want to talk"}]}`
- **R72** [verified] (overrides R50) — _brief-b.md rule 9_: An "already paid" claim on one product does not end the call: say payments can take one business day to appear, take no promise for it, note it (`add_note` reason `paid`) and continue with the others.
  - values: `{"note_reasons": [{"reason": "paid", "when": "customer says one product is already paid", "text_must_contain": ""}]}`
  - deciding quote: "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
- **R73** [verified] (overrides R52) — _brief-b.md rule 10_: A restructuring request still transfers (`transfer_to_agent` queue `restructuring`, close `transferred` / `restructuring`); promises already recorded stay, promises agreed but not yet recorded are not recorded. On any transfer (restructuring, support, human) add no notes at all.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "restructuring", "when": "restructuring request, even after recorded promises"}]}`
  - deciding quote: "On any transfer (restructuring, support, human) add no notes at all, before or after it."

## multi_product (6)

- **R63** (overrides R04) — _brief-b.md rule 1_: `get_account` returns one to three late products (Brief A assumed one). Each has its own `past_due`, `days_late` and floor.
  - deciding quote: "`get_account` returns one to three products. Each has its own `past_due`, `days_late` and floor."
- **R64** (overrides R27) — _brief-b.md rule 2_: After `get_account`, state every late product, one sentence each (product in words, past-due amount, days late), before asking for anything.
  - deciding quote: "State every late product, one sentence each, before asking for anything."
- **R65** — _brief-b.md rule 3_: The band and the deadline are per product, from that product's `days_late` (Brief A rule 18 table). Two products of the same customer can have different deadlines.
- **R66** (overrides R39) — _brief-b.md rule 4_: Replaces Brief A rule 28: first ask whether the customer can pay all of them today. If not, go through the products one by one in `get_account` order, not asking about today again; start each product at attempt 1 of Brief A rule 30.
  - deciding quote: "First ask whether the customer can pay all of them today."
- **R68** — _brief-b.md rule 6_: If the customer names one date for everything and it is after one product's deadline, record that product on its own deadline and say so in the read-back; the other products keep the named date.
- **R71** [verified] (overrides R51) — _brief-b.md rule 9_: Replaces Brief A rule 40's close: a dispute on one product does not end the call. Do not argue, take no promise for it, note it (`add_note` reason `dispute`) and continue with the other products.
  - values: `{"note_reasons": [{"reason": "dispute", "when": "one product is disputed", "text_must_contain": ""}]}`
  - deciding quote: "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."

## closing (6)

- **R57** [confidence medium, samples AC] — _brief-a.md rule 46_: Every call ends with exactly one `close_call`, with an outcome and, where the table lists one, a reason. It is the last tool call.
- **R58** — _brief-a.md rule 46_: Every call ends with exactly one `close_call`, the last tool call, with an outcome and, where the table lists one, a reason, per the outcome table.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded"}, {"outcome": "paid", "reason": "", "when": "rule 39"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
  - deciding quote: "The outcome table of Brief A applies."
- **R59** [verified] — _brief-a.md section 12 note after table_: If a transfer follows a recorded promise, close as `transferred` with that transfer's reason (not `promise`).
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "that transfer's reason", "when": "a transfer follows a recorded promise"}]}`
- **R61** — _brief-a.md rule 47_: Thank the customer and say goodbye before `close_call`.
- **R76** [verified] (overrides R58) — _brief-b.md section Closing_: Brief A table applies, extended: `promise` whenever at least one promise was recorded (except rule 10 transfer); with no promise, `paid` if every product is noted `paid`, else `no_promise` with the reason of the first product in `get_account` order whose note is not `paid`.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise was recorded (except a transfer under Brief B rule 10)"}, {"outcome": "paid", "reason": "", "when": "no promise recorded and every product is noted paid"}, {"outcome": "no_promise", "reason": "reason of the first product in get_account order whose note is not paid", "when": "no promise recorded and not every product noted paid"}, {"outcome": "transferred", "reason": "restructuring", "when": "rule 41 / Brief B rule 10"}, {"outcome": "transferred", "reason": "human", "when": "rule 42"}, {"outcome": "transferred", "reason": "support", "when": "rule 32"}, {"outcome": "no_promise", "reason": "refused", "when": "rules 31 and 45"}, {"outcome": "no_promise", "reason": "hardship", "when": "rule 32"}, {"outcome": "no_promise", "reason": "dispute", "when": "rule 40"}, {"outcome": "no_promise", "reason": "service_error", "when": "rule 37"}, {"outcome": "not_verified", "reason": "failed", "when": "rule 14"}, {"outcome": "not_verified", "reason": "declined", "when": "rule 15"}, {"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, {"outcome": "not_reached", "reason": "no_callback", "when": "rule 7"}, {"outcome": "not_reached", "reason": "wrong_number", "when": "rule 8"}, {"outcome": "not_reached", "reason": "deceased", "when": "rule 9"}, {"outcome": "not_reached", "reason": "unclear", "when": "rule 3"}]}`
  - deciding quote: "With no promise recorded: if every product is noted `paid`, close as `paid`."
- **R79** [confidence medium, samples AB] — _openapi.json /close_call_: `close_call` outcome enum is `promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`; `reason` is required for every outcome except `promise` and `paid`. Nothing is accepted after it.

## wording (1)

- **R07** — _brief-a.md section 2 table row title_: Address the customer as `title` plus `last_name`.

## other (7)

- **R01** [confidence low, samples B] — _brief-a.md intro_: Brief A covers Freya Bank early-stage collections for one product; the bank, customers, debts and payments are fictional and synthetic. Read all of the brief; every rule applies.
- **R04** **[superseded by R63]** — _brief-a.md section 1_: Freya Bank calls customers who are 1 to 45 days late on one product: find the customer, check identity, state the debt, get a promise where possible, close with the correct outcome.
  - deciding quote: "`get_account` returns one to three products. Each has its own `past_due`, `days_late` and floor."
- **R05** — _brief-a.md section 2 table_: Every call starts with `customer_id`, `first_name`, `last_name`, `title` (`Mr` or `Ms`) and `now` (e.g. `2026-10-14T11:00`); nothing else is known before the tools are called.
  - values: `{"text": "customer_id: pass to every tool call; first_name/last_name: the person to ask for; title: Mr or Ms; now: current date and time"}`
- **R06** [confidence low, samples B] — _brief-a.md section 2 table row customer_id_: Pass `customer_id` to every tool call.
- **R62** — _brief-b.md introduction_: Brief B is Brief A with a customer who can be late on up to three products. Every rule of Brief A applies unless a Brief B rule replaces it.
- **R77** [confidence low, samples A] — _openapi.json /create_promise_: `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` (format date); one per product.
- **R78** [confidence low, samples A] — _openapi.json /add_note_: `add_note` requires `customer_id`, `product_id` and `reason` (enum `refused`, `hardship`, `dispute`, `paid`, `service_error`); `text` is optional.
