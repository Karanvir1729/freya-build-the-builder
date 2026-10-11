# Rule inventory: conflicts and doubts (tamsin.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Rules found by only one extraction sample (confidence low)

- **R04** (_openapi.json /schedule_callback_, samples B): `schedule_callback` requires `date` (format date) and `time` as HH:MM; used for third-party callbacks and second-look calls.
- **R08** (_tamsin.md Document 1 'Who we ring'_, samples A): `customer_id` goes into every tool call.
- **R33** (_tamsin.md Document 1 'Read-back'_, samples A): With several products, agree, read back and record each product before moving to the next.
- **R37** (_tamsin.md Document 1 'Second look'_, samples B): If agreed, book with `schedule_callback` (day/hours per 5.7, customer picks time) and say the confirmation line.
- **R52** (_tamsin.md Document 2 section 5.1_, samples A): No arrangement may be dated on a Saturday, Sunday or closure day.
- **R68** (_tamsin.md Document 2 section 5.6 table row non-business_, samples A): Saturday, Sunday or closure day up to last date: offer first business day after; if later than last date, offer last business day before the named day.
- **R69** (_tamsin.md Document 2 section 5.6 table row too late_, samples A): Day after last date: say the last date is the latest recordable day and offer it; refusal counts as an attempt.
- **R70** (_tamsin.md Document 2 section 5.6 table row past_, samples A): Day before today: cannot be recorded; ask for a day from today on.
- **R71** (_tamsin.md Document 2 section 5.6 table row vague_, samples A): Vague time ("next week", "end of the month", "payday"): ask once for exact day; if none, propose the applicable last date.
- **R78** (_tamsin.openapi.json /verify_identity_, samples C): An unreadable DOB value is rejected with ok=false and not counted as a wrong answer; phone_last4 is four digits.
- **R87** (_tamsin.md Document 4 intro_, samples B): The closing sentence for the code is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.

## Values a fresh reader could not confirm (chain-of-verification)

- **R80** (_tamsin.md Document 3 item 2_) **mismatch**: From go-live (14 October 2026) the credit_card floor changes from `minimum_payment` to half of `past_due`, rounded up to the next multiple of 5, never more than `past_due`; personal_loan and car_loan stay `instalment_amount`.
  - inventory values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "percent", "percent": 50, "field": "past_due", "round": "up to the next multiple of 5", "cap_to_full": true}}, {"product_types": ["personal_loan"], "rule": {"type": "field", "field": "instalment_amount"}}, {"product_types": ["car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - not in the verifier's answer: ['50']
  - verifier (in force): credit_card: half of past_due rounded up to next multiple of 5, capped at past_due; personal_loan: instalment_amount; car_loan: instalment_amount
  - verifier (earlier): credit_card: minimum_payment (changed from 2026-10-14)
  - quote (not in force): "| credit_card | `minimum_payment` |"
  - quote: "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
  - quote: "Loans stay at the instalment amount."

## Dated decisions (which statement is in force)

- **T1** topic `third_party_callback_booking`: The mail's no-same-day rule and the 5.6a window for third-party callbacks fit together. The second-look rules in 5.7 were confirmed unchanged by the 9 October minutes, so all four apply.
  - R19: in_force -- "We never call back the same day: the window is in AHS-5 5.6a."
  - R72: in_force -- "A callback is booked on the next business day after the call date or the business day after that, never the call date itself, at a time from 10:00 to 16:00, both included."
  - R73: in_force -- "On the 3rd business day after the call date, at a time the customer chooses from 12:00 to 18:00, both included."
  - R84: in_force -- "No change to the rules; the 12:00–18:00 hours stay."
- **T2** topic `wrong_answer_limit`: The review turned down the switch to three wrong answers in total and confirmed the existing one-retry-per-question rule. So the confirmation and the original rule both apply.
  - R23: in_force -- "Our rule is per question: each question may be answered wrongly once and asked again; a second wrong answer to the SAME question ends the check."
  - R85: in_force -- "No: we keep one retry per question."
- **T3** topic `campaign_review`: This only announces that decisions will come later. It decides nothing.
  - R49: not_policy -- "We have a campaign review on Friday the 9th and I expect a few decisions to come out of it, so I will send the minutes on as well."
- **T4** topic `no_non_business_dates`: Both come from the Standard, and no later document changes them.
  - R50: in_force -- "The call date counts as day 0; "the n-th business day after the call date" counts the first business day after the call date as the 1st."
  - R52: in_force -- "No arrangement may be dated on a Saturday, a Sunday or a closure day."
- **T5** topic `closure_days`: The 9 October minutes move the cut-over closure day from 13 November to 6 November. That is the latest decision, so it replaces the Standard's list.
  - R51: superseded by R83 -- "Friday 13 November is an ordinary working day again."
  - R83: in_force -- "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."
- **T6** topic `band_deadline`: The minutes change the Middle band's last date from the 6th to the 4th business day and restate the other bands unchanged. The assistant is checked against the minutes from go-live.
  - R54: superseded by R81 -- "Agreed: their last date for a full payment is **the 4th business day after the call date**."
  - R81: in_force from 2026-10-14 -- "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **T7** topic `floors`: From go-live the credit card floor is half of `past_due`, rounded up to the next multiple of 5. The loan floors are unchanged.
  - R55: superseded by R80 -- "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
  - R56: in_force -- "Loans stay at the instalment amount."
  - R80: in_force from 2026-10-14 -- "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
- **T8** topic `bands`: This was discussion only, with nothing decided. The existing bands stay.
  - R82: not_policy -- "The question of widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November."
- **T9** topic `close_call_codes`: The code card v2 is the current list of closing codes, and nothing later changes it.
  - R86: in_force -- "The closing sentence is said, word for word, before `close_call` (for a transfer, before `transfer_to_agent`)."
  - R88: in_force -- "Every `close_call` has one `outcome` from the dialler's list (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from this card."
- **T10** topic `aob_non_policy`: This is an AOB item unrelated to the calls.
  - R106: not_policy -- "The Christmas lunch is on Friday 11 December."

## Structured spec (`spec.json`) problems

- two rules in force set different values: callback.open: "10:00" (R72) -> "12:00" (R73) (the later one is used)
- two rules in force set different values: callback.close: "16:00" (R72) -> "18:00" (R73) (the later one is used)

