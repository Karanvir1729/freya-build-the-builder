# Rule inventory: conflicts and doubts (ashvale.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Values a later rule replaced that another rule in force still carries

The rule named "new" replaced the value; the rule below still has it. Use the new value (outcome rows with a stale reason are left out of spec.json).

- **R69** (_ashvale.md message 2.4_) still has ['1'], replaced by R76 (old rule R16): From Monday 12 October 2026 the late band (10 days and over) latest date is the 5th business day after the call date (was 9th); proposal 2 goes out on that date; early band unchanged (18 calendar days, next business day if closed, 1 proposal).

## Rules found by only one extraction sample (confidence low)

- **R10** (_ashvale.md message 2.1 'Opening'_, samples A): If the person asks something first, answer it and then ask the 'May I speak with' question again; that ask counts as the second one.
- **R28** (_ashvale.md message 2.1 'The balance'_, samples A): After `get_account`, say it is calling from Ashvale's Customer Payments team about an overdue balance, then one sentence per product (product in words e.g. 'your credit card ending 4821', overdue amount, days overdue), all before asking for anything.
- **R31** (_ashvale.md message 2.1 Asking_, samples B): A date or an amount the customer comes up with is never a refusal: check it against the date and amount rules and carry on.
- **R47** (_ashvale.md message 2.1 Hardship_, samples B): If a hardship customer names a date or an amount themselves anyway, log it as normal.
- **R50** (_ashvale.md message 2.1 Read-back and logging_, samples B): If they change the date or the amount at read-back, check it again against the rules and read it back again.
- **R79** (_ashvale.md thread 4 message 4.2 create_promise_, samples C): With several products, after a `create_promise` failure carry on with the other products; the promises already logged stay.
- **R90** (_ashvale.md desk card v2 say it as written_, samples C): Say as written, the confirm question after the read-back, before `create_promise`.
- **R91** (_ashvale.md desk card v2 say it as written_, samples C): Say as written, once per call after the last promise is logged.
- **R92** (_ashvale.md desk card v2 say it as written_, samples C): Say as written when the customer says they have already paid.
- **R98** (_openapi.json /close_call_, samples B): `close_call` `reason` is required for every `outcome` except `promise` and `paid`; `outcome` is one of `promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`.
- **R99** (_openapi.json /schedule_callback_, samples A): `schedule_callback` requires `customer_id`, `date` (format date, YYYY-MM-DD) and `time` as HH:MM.

## Values that differ between the extraction samples

- **R54** (_ashvale.md message 2.1 'Other things people say'_): Paid close code: A51 and C45 give reason CLP; B53 gives reason "" (no code). -- chosen value verified against the brief
  - chosen: `{"note_reasons": [{"reason": "paid", "when": "customer says already paid", "text_must_contain": ""}], "outcomes": [{"outcome": "paid", "reason": "CLP", "when": "every product noted paid"}]}`
  - B53: `{"outcomes": [{"outcome": "paid", "reason": "", "when": "every product noted paid"}], "note_reasons": [{"reason": "paid", "when": "customer says already paid", "text_must_contain": ""}]}`

## Values a fresh reader could not confirm (chain-of-verification)

- **R66** (_ashvale.md message 2.1 'Closing'_) **mismatch**: A promise close carries no code and applies when a promise was logged unless transferred afterwards; nothing promised: all products noted paid → paid, otherwise no promise with the code of the first product in `get_account` order whose note isn't paid.
  - inventory values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise logged, no transfer afterwards"}, {"outcome": "paid", "reason": "", "when": "no promise and every product noted paid"}, {"outcome": "no_promise", "reason": "code of first non-paid product in get_account order", "when": "no promise, not all paid"}]}`
  - not in the verifier's answer: ['code of first non-paid product in get_account order']
  - verifier (in force): 1) At least 1 promise logged and no transfer afterwards: outcome=promise, reason empty. 2) Nothing promised and every product noted paid: outcome=paid, reason=CLP. 3) Nothing promised otherwise: outcome=no_promise with the reason code for the first product in get_account order whose note isn't paid (refused=RTP, hardship=VUL, dispute=DIS, service_error=SYS).
  - quote: "Thank them and say goodbye, then exactly one `close_call`, always the last tool call. A promise close carries no code. If nothing was promised: every product noted paid means close as paid; otherwise no promise with the code for the first product, in `get_account` order, whose note isn't paid. A promise logged on the call means a promise close, unless the call was transferred afterwards."
  - quote: "| at least one promise logged, no transfer afterwards | promise | leave empty (the dialler stamps it) |"
  - quote: "| customer says it is already paid; every product noted `paid` | paid | CLP |"
- **R96** (_ashvale.md code list v5 Notes_) **no_answer**: `add_note` `reason` is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`; `text` is one line in plain words (required by policy though optional in the API).
  - inventory values: `{"note_reasons": [{"reason": "refused", "when": "product refused / proposals used up / will not talk after security", "text_must_contain": "one line in plain words"}, {"reason": "hardship", "when": "hardship disclosed", "text_must_contain": "one line in plain words"}, {"reason": "dispute", "when": "customer disputes the balance or product", "text_must_contain": "one line in plain words"}, {"reason": "paid", "when": "customer says already paid", "text_must_contain": "one line in plain words"}, {"reason": "service_error", "when": "create_promise failed", "text_must_contain": "one line in plain words"}]}`

## Dated decisions (which statement is in force)

- **T1** topic `holiday_calendar`: The People Team list is the calendar message 2.1 tells the assistant to use; the two complement each other (holiday dates + business-day definition). Nothing later changes either.
  - R01: in_force from 2026-09-14 -- "On these days branches, the contact centre and payment processing are all closed:"
  - R33: in_force from 2026-09-07 -- "Business days are Monday to Friday except bank holidays; the People Team sends the calendar round, use that."
- **T2** topic `saturday_business_day`: Branch counter hours are a staff notice; business days for the assistant are Monday to Friday except bank holidays, and the Saturday counter-payment question was never decided.
  - R03: not_policy -- "Saturday opening at Kelso Street carries on as before for counter services."
- **T3** topic `callback_window`: The vendor notice is information, not a bank decision; Imogen decided the assistant's window on 5 October (08:30–17:00, up to two business days ahead), replacing message 2.1 and the desk card. The second-ask / CBX handling is carried over unchanged.
  - R16: superseded by R76 from 2026-09-07 -- "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
  - R73: not_policy -- "As flagged in the quarterly review, our evening pool closes from Monday 5 October."
  - R74: not_policy -- "On the plus side, scheduler 3.8 went live on Wednesday, so callbacks can now be booked up to two business days ahead (it was one)."
  - R76: in_force from 2026-10-05 -- "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
  - R88: superseded by R76 from 2026-09-21 -- "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
- **T4** topic `security_question_order`: Compliance decided on 1 October (confirmed by Imogen on 2 October, live 5 October) that the second wrong answer in total ends the check; order, retry hint, failure message and close stay as in message 2.1, so R21 remains in force alongside R80.
  - R21: in_force from 2026-09-07 -- "Date of birth first, then the last four digits of the phone number we hold, one question at a time, `verify_identity` after each answer."
  - R24: superseded by R80 from 2026-09-07 -- "On the dialler, the second wrong answer in total, whichever question it was on, ends the check, whatever `wrong_answers_left` says."
  - R80: in_force from 2026-10-05 -- "On the dialler, the second wrong answer in total, whichever question it was on, ends the check, whatever `wrong_answers_left` says."
- **T5** topic `band_deadline`: Message 2.4 (7 October, effective 12 October) is the latest decision: late band latest date becomes the 5th business day and proposal 2 moves to it; early band is unchanged. The desk card v2 (21 September) predates it.
  - R32: superseded by R69 from 2026-09-07 -- "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."
  - R44: superseded by R70 from 2026-09-07 -- "Proposal 2 goes out on that date too."
  - R69: in_force from 2026-10-12 -- "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."
  - R70: in_force from 2026-10-12 -- "Proposal 2 goes out on that date too."
  - R85: superseded by R69 from 2026-09-21 -- "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."
  - R86: superseded by R70 from 2026-09-21 -- "Proposal 2 goes out on that date too."
- **T6** topic `promise_date_validity`: The Saturday question was asked and never answered; the last decided rule (business day only) stays in force.
  - R34: in_force from 2026-09-07 -- "A promise date has to be today or later, a business day, and not after the product's latest date."
  - R67: not_policy -- "Quick one — if a customer says they'll come in and pay at the counter on a Saturday morning (we open 9 till 12), can the assistant log that?"
  - R71: not_policy -- "@Tomasz did anyone come back to you on the Saturday question?"
- **T7** topic `card_floor`: Message 2.3 raised the card floor from 21 September; the desk card v2 restates the same rule, so both are in force together. Loan floors unchanged.
  - R43: superseded by R68 from 2026-09-07 -- "From Monday 21 September, the smallest promise we take on a credit card is half the overdue balance, or the minimum payment where that's higher."
  - R68: in_force from 2026-09-21 -- "From Monday 21 September, the smallest promise we take on a credit card is half the overdue balance, or the minimum payment where that's higher."
  - R87: in_force from 2026-09-21 -- "- Credit card: half the overdue balance, or the minimum payment if higher."
- **T8** topic `hardship_handling`: Compliance decided (confirmed by Imogen 2 October, live 5 October) that hardship calls are not transferred: Financial Support sentence, hardship notes on every product, close no_promise/VUL. HDS is not on code list v5.
  - R46: superseded by R81 from 2026-09-07 -- "From Monday, hardship calls stay with the assistant."
  - R81: in_force from 2026-10-05 -- "From Monday, hardship calls stay with the assistant."
- **T9** topic `read_back`: The read-back itself is unchanged; message 4.2 (5 October) replaced the retry rule with one try and the new failure sentence. The vendor's incident report is background, not a decision.
  - R49: in_force from 2026-09-07 -- "Read back the product, the amount and the date and ask "Shall I go ahead and log that?"."
  - R52: superseded by R78 from 2026-09-07 -- "`create_promise` gets one try."
  - R75: not_policy -- "Root cause is on our side (gateway timeout shorter than the write); we're working on it."
  - R78: in_force from 2026-10-05 -- "`create_promise` gets one try."
- **T10** topic `close_call_last`: Code list v5 supplies the outcome/reason mapping (VUL added, HDS gone) but does not change that close_call is the single last tool call with no code on a promise close; the two complement each other.
  - R65: in_force from 2026-09-07 -- "Thank them and say goodbye, then exactly one `close_call`, always the last tool call."
  - R95: in_force from 2026-10-06 -- "Every `close_call` carries one `outcome` from the dialler's fixed list and, except a promise close, one code in `reason`."
- **T12** topic `close_call_reason_required`: The API schema only sets a minimum (reason optional on paid); the bank's code list v5 is the policy and requires CLP on a paid close, which satisfies the schema. Both apply together.
  - R94: in_force from 2026-10-06 -- "Every `close_call` carries one `outcome` from the dialler's fixed list and, except a promise close, one code in `reason`."
  - R98: in_force -- "| customer says it is already paid; every product noted `paid` | paid | CLP |"
- **T11** topic `bank_holidays`: A diary notice confirming no change; the holiday calendar from the People Team stands.
  - R72: not_policy -- "Monday 9 November is a normal working day for everyone, not a holiday, and nothing customer-facing moves."
- **T13** topic `calendar`: Branch opening is a diary note with no effect on the assistant's calendar, business days or call rules.
  - R100: not_policy -- "Opening hours as per the standard branch pattern."

## Structured spec (`spec.json`) problems

- two rules in force set different values: floors[credit_card]: {"type": "other", "text": "the higher of 50% of past_due and minimum_payment"} (R68) -> {"type": "other", "text": "half of past_due, or minimum_payment where that is higher"} (R87) (the later one is used)

