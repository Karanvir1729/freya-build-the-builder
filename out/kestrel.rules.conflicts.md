# Rule inventory: conflicts and doubts (kestrel.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Values a later rule replaced that another rule in force still carries

The rule named "new" replaced the value; the rule below still has it. Use the new value (outcome rows with a stale reason are left out of spec.json).

- **R51** (_kestrel.md email of 6 Oct 'Hardship'_) still has ['hard'], replaced by R111 (old rule R116): If the customer declines the transfer, call `add_note` reason `hardship` on every product with the circumstance in the customer's own words, and close `no_promise` with the hardship code from the list (HARD in v3).
- **R117** (_kestrel.md code list v3 closing codes table_) still has ['hard'], replaced by R111 (old rule R116): Same table as R33 (listed as the overridden target of memo item 5); see R33 for every row. HARD applies for hardship-declined-transfer until 14 October 2026.

## Rules found by only one extraction sample (confidence low)

- **R02** (_openapi.json /verify_identity_, samples C): An unreadable `date_of_birth` value is rejected by `verify_identity` with `ok=false` and is not counted as a wrong answer; the service reports `wrong_answers_left`, `verified`, `all_verified` and a `hint`.
- **R04** (_openapi.json /create_promise_, samples C): `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` in date format; success is `ok: true` with a `promise_id`.
- **R05** (_openapi.json /transfer_to_agent_, samples C): `transfer_to_agent` requires `customer_id` and `queue` from the enum `restructuring`, `general`, `support`.
- **R44** (_kestrel.md email of 6 Oct 'Getting to a promise'_, samples C): If the customer turns down the floor, that is a flat refusal.
- **R47** (_kestrel.md email of 6 Oct 'Getting to a promise'_, samples C): When the attempts are used up, stop; never repeat an offer the customer has already turned down.
- **R75** (_kestrel.md email of 6 Oct 'Closing'_, samples C): Thank the customer and say goodbye before closing.
- **R88** (_kestrel.md CP-7 section 4.5 table row 2_, samples A): If the customer proposes an amount from the floor up to the full amount, both included, accept it as proposed.
- **R89** (_kestrel.md CP-7 section 4.5 table row 3_, samples A): If the customer proposes more than the full amount, record the full amount.

## Values that differ between the extraction samples

- **R104** (_kestrel.md memo item 1_): Band S attempts: A93 keeps 3 (item 1 only); B92 and C100 give 2 (folding in memo item 2).; A93 has ['3'] where C100 has ['2']
  - chosen: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}, "text": "fresh arrears, unchanged"}, {"name": "S", "min_days": 11, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}, "text": "standing arrears; latest date brought forward from 7th to 5th business day"}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "not in the digital campaign; if returned, treat as Band S"}]}`
  - A93: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}, "attempts": 1, "text": "fresh arrears"}, {"name": "S", "min_days": 11, "max_days": 45, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}, "attempts": 3, "text": "standing arrears"}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "treat as Band S"}]}`
  - B92: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}}, {"name": "S", "min_days": 11, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "not in the digital campaign; if returned, treat as Band S"}]}`

## Values a fresh reader could not confirm (chain-of-verification)

- **R76** (_kestrel.md email of 6 Oct 'Closing'_) **mismatch**: Thank the customer and say goodbye, then exactly one `close_call`, the last tool call of every call, always with an outcome and a code from the list (including promise closes, which carry PRM).
  - inventory values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer afterwards"}]}`
  - not in the verifier's answer: ['prm']
  - verifier (in force): thank the customer and say goodbye, then exactly 1 close_call as the last tool call, always with customer_id, an outcome (promise, paid, transferred, no_promise, not_verified, not_reached) and exactly 1 code from the list in reason
  - quote: "Thank the customer and say goodbye. Then exactly one `close_call`, the last tool call of every call, always with an outcome and a code from the list."

## Dated decisions (which statement is in force)

- **T1** topic `founders_day_closure`: The email only announces that a memo will fix Founders' Day; the decision itself is in the memo of 12 Oct (block T9).
  - R07: not_policy -- "Dialler Ops are due to issue one before go-live with the Founders' Day date and a couple of tweaks from the Compliance review, so watch out for it."
- **T2** topic `callback_window`: The memo of 12 Oct, effective 14 Oct, extends the callback window end to 18:00 and overrides CP-7 4.4 and the email; the email's 'may extend' remark was only a heads-up.
  - R23: superseded by R113 -- "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."
  - R24: not_policy -- "Nothing more. A callback must sit inside the window in CP-7 section 4.4: today, later than `now`, or one of the next two business days, between 09:00 and 17:00 (Ops may extend the evening end, check the memo)."
  - R86: superseded by R113 -- "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."
  - R113: in_force from 2026-10-14 -- "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."
- **T3** topic `never_ask_how_much`: Email and CP-7 4.5 say the same thing and the memo does not touch it; both stand together.
  - R41: in_force -- "Never ask the customer how much they can pay, in any wording: the assistant proposes every amount."
  - R92: in_force -- "| asks "how much should I pay?" or similar | the assistant proposes every amount; it never asks the customer how much they can pay |"
- **T4** topic `card_floor`: 'Ops are reviewing the card floor' is a pointer to a pending decision; the actual card floor is decided in memo item 3 (block T8).
  - R43: not_policy -- "If the customer says the full amount is too much, offer the floor for that product once (CP-7 section 4.2; Ops are reviewing the card floor, again see the memo), and when you do, say that the remainder stays overdue and we will be in touch about it."
  - R43: not_policy -- "If the customer says the full amount is too much, offer the floor for that product once (CP-7 section 4.2; Ops are reviewing the card floor, again see the memo), and when you do, say that the remainder stays overdue and we will be in touch about it."
- **T5** topic `attempt_definition`: Both define the attempt identically; the memo changes the number of attempts, not the definition.
  - R46: in_force -- "A flat refusal, a non-answer, or a no to paying today with no date and no amount uses up one persuasion attempt."
  - R100: in_force -- "A persuasion attempt is used whenever the customer refuses flatly, gives no answer, or says no to paying today without naming a date or an amount."
- **T6** topic `attempts_exhausted`: Consistent and complementary (email adds the RF close); untouched by the memo.
  - R48: in_force -- "Record the product as refused in the notes (see the code list for the note reasons) and, if nothing else applies, close as no promise with code RF."
  - R102: in_force -- "When the attempts are used up the assistant stops and the product is recorded as refused."
- **T7** topic `band_table`: Memo items 1 and 2 (same date, same author) jointly replace the CP-7 4.1 table: Band S latest date 5th business day and two attempts; Band F unchanged.
  - R80: superseded by R104 -- "The latest promise date in the standing band (11 to 45 days) is brought forward from the 7th business day after the call date to the **5th business day** after the call date."
  - R104: in_force from 2026-10-14 -- "The latest promise date in the standing band (11 to 45 days) is brought forward from the 7th business day after the call date to the **5th business day** after the call date."
  - R105: in_force from 2026-10-14 -- "From Wednesday: **two attempts in Band S, one in Band F**, exactly as the table in 4.8 reads without its last row."
- **T8** topic `floor_table`: Memo item 3 changes the credit card floor from 14 Oct; loan floors unchanged.
  - R81: superseded by R108 -- "For credit cards the floor becomes **twice the minimum payment (2 x `minimum_payment`)**, but never more than the overdue amount."
  - R108: in_force from 2026-10-14 -- "For credit cards the floor becomes **twice the minimum payment (2 x `minimum_payment`)**, but never more than the overdue amount."
- **T9** topic `calendar_closure_days`: CP-7 4.3 anticipates Founders' Day being added by memo; memo item 4 adds 30 Oct as a closure day and changes nothing else in the calendar, so both apply together (full list: 30 Oct, 20 Nov, 24/25/28/31 Dec).
  - R83: in_force -- "A business day is a Monday to Friday that is not a closure day."
  - R109: in_force from 2026-10-14 -- "The Executive has fixed Founders' Day 2026 on **Friday 30 October**."
- **T10** topic `attempt_ladder`: Memo item 2 withdraws attempt 3 from 14 Oct; the ladder is the 4.8 table without its last row.
  - R101: superseded by R106 -- "The third persuasion attempt, the "final-offer repeat" in section 4.8, is withdrawn."
  - R106: in_force from 2026-10-14 -- "The third persuasion attempt, the "final-offer repeat" in section 4.8, is withdrawn."
- **T11** topic `closing_code_table`: Memo item 5 replaces HARD with HSHP from 14 Oct; the rest of code list v3 is unchanged and carried in R111.
  - R111: in_force from 2026-10-14 -- "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
  - R116: superseded by R111 -- "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
- **T12** topic `multi_product_no_promise_close`: The seriousness order is unchanged but the hardship code in it becomes HSHP from 14 Oct, so the v3 version is superseded.
  - R112: in_force from 2026-10-14 -- "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
  - R121: superseded by R112 -- "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."

## Structured spec (`spec.json`) problems

- two rules in force set different values: bands[F].text: "fresh arrears, unchanged" (R104) -> "fresh arrears" (R105) (the later one is used)
- two rules in force set different values: bands[S].text: "standing arrears; latest date brought forward from 7th to 5th business day" (R104) -> "standing arrears" (R105) (the later one is used)
- two rules in force set different values: bands[over 45].text: "not in the digital campaign; if returned, treat as Band S" (R104) -> "treat as Band S" (R105) (the later one is used)

