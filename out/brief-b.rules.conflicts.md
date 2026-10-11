# Rule inventory: conflicts and doubts (brief-a.md, brief-b.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Rules found by only one extraction sample (confidence low)

- **R01** (_brief-a.md intro_, samples B): Brief A covers Freya Bank early-stage collections for one product; the bank, customers, debts and payments are fictional and synthetic. Read all of the brief; every rule applies.
- **R02** (_openapi.json /verify_identity_, samples B): `verify_identity` takes `field` enum `date_of_birth` or `phone_last4`; for `phone_last4` the answer is four digits. An unreadable value is rejected with `ok=false` and is not counted as a wrong answer.
- **R03** (_openapi.json /schedule_callback_, samples B): `schedule_callback` requires `customer_id`, `date` (format date) and `time` as `HH:MM`.
- **R06** (_brief-a.md section 2 table row customer_id_, samples B): Pass `customer_id` to every tool call.
- **R74** (_brief-b.md rule 10_, samples C): On any transfer (restructuring, support, human) add no notes at all, before or after it.
- **R77** (_openapi.json /create_promise_, samples A): `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` (format date); one per product.
- **R78** (_openapi.json /add_note_, samples A): `add_note` requires `customer_id`, `product_id` and `reason` (enum `refused`, `hardship`, `dispute`, `paid`, `service_error`); `text` is optional.

## Dated decisions (which statement is in force)

- **T1** topic `callback_tool_format`: The tool contract (date, HH:MM) and the business rule (window, same day/next business day, later than now, close reason) complement each other; nothing in Brief B touches callbacks.
  - R03: in_force -- "Call `schedule_callback` with the date and the time, then close as `not_reached` / `callback`."
  - R16: in_force -- "A callback is for today or the next business day, from 10:00 to 19:00, both included, and later than `now`."
- **T2** topic `call_scope`: Brief B states 'Every rule of Brief A applies unless a rule below replaces it' and its rule 1 replaces the one-product scope of Brief A section 1 with one to three products.
  - R04: superseded by R63 -- "`get_account` returns one to three products. Each has its own `past_due`, `days_late` and floor."
  - R63: in_force -- "`get_account` returns one to three products. Each has its own `past_due`, `days_late` and floor."
- **T3** topic `state_debt`: Brief B rule 2 changes how the debt is stated: every late product, one sentence each, before any ask. The wording elements of rule 17 (collections team, product in words, amount, days late) are carried into each sentence, but the single-product statement is replaced.
  - R27: superseded by R64 -- "State every late product, one sentence each, before asking for anything."
  - R64: in_force -- "State every late product, one sentence each, before asking for anything."
- **T4** topic `ask_pay_today`: Brief B rule 4 replaces the single 'Can you make this payment today?' with one question about all products, then per-product persuasion without re-asking about today.
  - R39: superseded by R66 -- "First ask whether the customer can pay all of them today."
  - R66: in_force -- "First ask whether the customer can pay all of them today."
- **T5** topic `readback_confirmation`: Brief B rule 7 changes the read-back and confirmation step: one combined read-back, one confirmation, then create_promise once per product.
  - R45: superseded by R69 -- "Read all promises back together and ask for one confirmation. Then call `create_promise` once per product."
  - R69: in_force -- "Read all promises back together and ask for one confirmation. Then call `create_promise` once per product."
- **T6** topic `create_promise_failure`: Brief B rule 11 replaces the service_error close with a per-product add_note and keeps already recorded promises; the closing then follows the Brief B closing section.
  - R48: superseded by R75 -- "If one `create_promise` fails twice, keep the promises that were recorded and call `add_note` with reason `service_error` for the failed product."
  - R75: in_force -- "If one `create_promise` fails twice, keep the promises that were recorded and call `add_note` with reason `service_error` for the failed product."
- **T7** topic `already_paid`: Brief B rule 9 replaces the immediate `paid` close with a per-product note and continuation; `paid` as an outcome survives only via the Brief B closing section when every product is noted paid.
  - R50: superseded by R72 -- "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
  - R72: in_force -- "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
- **T8** topic `dispute`: Brief B rule 9 replaces the immediate `no_promise` / `dispute` close with a per-product dispute note and continuation with the other products.
  - R51: superseded by R71 -- "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
  - R71: in_force -- "A dispute or an "already paid" claim on one product does not end the call. Note it and continue with the others."
- **T9** topic `restructuring_request`: Brief B rule 10 explicitly keeps Brief A rule 41 ('still transfers') and only adds what happens to recorded and unrecorded promises and that no notes are added on any transfer; the two complement each other.
  - R52: in_force -- "A restructuring request still transfers the call (Brief A rule 41)."
  - R73: in_force -- "On any transfer (restructuring, support, human) add no notes at all, before or after it."
- **T10** topic `close_call_outcome_table`: Brief B's closing section says the Brief A table applies and only adds the multi-product resolution (promise wins except rule 10 transfer; paid only if all noted paid; otherwise reason of the first non-paid note in get_account order).
  - R58: in_force -- "The outcome table of Brief A applies."
  - R76: in_force -- "With no promise recorded: if every product is noted `paid`, close as `paid`."
- **T11** topic `add_note_usage`: Brief B rule 8 introduces add_note per product without a promise (also when no product gets a promise), directly replacing 'Brief A never uses `add_note`'; the only exception is Brief B rule 10 (no notes on any transfer).
  - R60: superseded by R70 -- "For each product without a promise call `add_note` with that `product_id` and a reason: `refused`, `hardship`, `dispute`, `paid` or `service_error`."
  - R70: in_force -- "For each product without a promise call `add_note` with that `product_id` and a reason: `refused`, `hardship`, `dispute`, `paid` or `service_error`."

