# Rule inventory: conflicts and doubts (harrow.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Rules found by only one extraction sample (confidence low)

- **R66** (_openapi.json /verify_identity_, samples C): An unreadable `answer` is rejected with ok=false and not counted as a wrong answer; phone_last4 is four digits.
- **R75** (_harrow.md Document 4 intro_, samples B): The closing sentence is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.
- **R94** (_openapi.json /create_promise_, samples C): `create_promise` requires customer_id, product_id, amount, date (format date); one per product.

## Values a fresh reader could not confirm (chain-of-verification)

- **R68** (_harrow.md Document 3 item 2_) **mismatch**: From go-live (14 October 2026) the credit card floor changes from `minimum_payment` to half of `past_due`, rounded up to the next multiple of 5, never more than `past_due`; loans stay at `instalment_amount`.
  - inventory values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "percent", "percent": 50, "field": "past_due", "round": "up to next multiple of 5", "cap_to_full": true}}, {"product_types": ["personal_loan"], "rule": {"type": "field", "field": "instalment_amount"}}, {"product_types": ["car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - not in the verifier's answer: ['50']
  - verifier (in force): credit_card: half of past_due rounded up to next multiple of 5, capped at past_due; personal_loan: instalment_amount; car_loan: instalment_amount
  - verifier (earlier): credit_card: minimum_payment (changed from 2026-10-14)
  - quote (not in force): "| credit_card | `minimum_payment` |"
  - quote: "from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`. Loans stay at the instalment amount."
  - quote: "| personal_loan | `instalment_amount` |"
  - quote: "| car_loan | `instalment_amount` |"

## Dated decisions (which statement is in force)

- **T1** topic `campaign_review_decisions`: This only says decisions are coming later. It decides nothing itself; the actual decisions are in the 9 Oct minutes.
  - R02: not_policy -- "We have a campaign review on Friday the 9th and I expect a few decisions to come out of it, so I will send the minutes on as well."
- **T2** topic `call_variables`: Both come from the same mail section, fit together and are never changed later.
  - R03: in_force -- "Personal customers who are 1 to 45 days behind on one, two or three products: a credit card, a personal loan, a car loan."
  - R04: in_force -- "The dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now`, the date and time of the call in the form `2026-10-14T11:00`."
- **T3** topic `third_party_callback_booking`: The third-party callback rules (mail plus AHS 5.6a) and the second-look rules (AHS 5.7) cover different parts of the topic. The 9 Oct minutes confirm the second-look rules without changing them.
  - R16: in_force -- "We never call back the same day: the window is in AHS-5 5.6a."
  - R61: in_force -- "A callback is booked on the next business day after the call date or the business day after that, never the call date itself, at a time from 10:00 to 16:00, both included."
  - R62: in_force -- "On the 3rd business day after the call date, at a time the customer chooses from 12:00 to 18:00, both included."
  - R72: in_force -- "No change to the rules; the 12:00–18:00 hours stay."
- **T4** topic `wrong_answer_rule`: The review turned down the switch to the three-in-total rule and kept the one-retry-per-question rule, so the original rule stays in force.
  - R20: in_force -- "Our rule is per question: each question may be answered wrongly once and asked again; a second wrong answer to the SAME question ends the check."
  - R73: in_force -- "No: we keep one retry per question."
- **T5** topic `create_promise_retry`: The mail and the Standard say the same thing and fit together.
  - R31: in_force -- "If `create_promise` fails, try once more."
  - R63: in_force -- "`create_promise` is called at most twice for the same arrangement (one retry)."
- **T6** topic `close_call_last`: The mail, the code card and the API spec agree: close_call comes last and always has a reason. R95 cites harrow.openapi.json, which is not in this pack; its quote is taken from the code card, which says the same thing.
  - R43: in_force -- "Every call ends with the closing sentence for its code and then exactly one `close_call`, the last tool call, with an outcome and a code from the card."
  - R95: in_force -- "Every `close_call` has one `outcome` from the dialler's list (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from this card."
- **T7** topic `business_days_closure_days`: The later minutes (9 Oct) move the cut-over closure day from 13 Nov to 6 Nov. The other closure days stay the same.
  - R44: superseded by R71 -- "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."
  - R71: in_force -- "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."
- **T8** topic `band_deadline`: The 9 Oct minutes change the Middle band's last date from the 6th to the 4th business day. The Early and Late bands are unchanged.
  - R48: superseded by R69 -- "Agreed: their last date for a full payment is **the 4th business day after the call date**."
  - R69: in_force -- "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **T9** topic `card_floor`: The minutes change the credit card floor from go-live (14 Oct). The loan floors stay at the instalment amount.
  - R49: superseded by R68 -- "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
  - R68: in_force from 2026-10-14 -- "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
- **T10** topic `band_limits`: This was only discussed and nothing was decided. The Early band stays at 1–7 days.
  - R70: not_policy -- "The question of widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November."
- **T11** topic `aob_non_policy`: These are 'any other business' items that have nothing to do with the calls.
  - R100: not_policy -- "The Christmas lunch is on Friday 11 December."

## Structured spec (`spec.json`) problems

- two rules in force set different values: callback.open: "10:00" (R61) -> "12:00" (R62) (the later one is used)
- two rules in force set different values: callback.close: "16:00" (R61) -> "18:00" (R62) (the later one is used)

