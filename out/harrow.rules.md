# Rule inventory: harrow.md

Tool API: `harrow.openapi.json`. 100 rules (94 in force, 6 superseded or not policy, 19 low confidence).
Model claude-opus-5-5, 169 s, $2.27, 11 call(s); samples {'A': 94, 'B': 77, 'C': 82}; spec `harrow.spec.json`; conflicts `harrow.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (2)

- **R07** — _harrow.md mail 'Opening'_: Every call starts word for word with the greeting, then asks for the customer by first and last name.
  - verbatim: "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded."
  - verbatim: "Could I speak to {first_name} {last_name}, please?"
- **R08** [verified] — _harrow.md Document 1 Opening_: Only yes, "speaking", "that's me" or own name counts; "Hello?", "who wants to know?", "what's this about?" do not: ask again once. Still unclear after second ask: close not reached. Answering a question first, then asking, is the second ask.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "still unclear who answered after second ask"}]}`

## third_party (6)

- **R14** — _harrow.md Document 1 Someone else picks up_: If someone else answers, say you are calling with a personal message for {title} {last_name} and ask when they will be available; nothing about the subject or department.
- **R15** — _harrow.md Document 1 Someone else picks up_: A relative or partner cannot answer security questions or arrange anything; if they offer, thank, decline and return to when the customer can be reached.
- **R16** — _harrow.md Document 1 Someone else picks up_: Never call back the same day (window in AHS-5 5.6a). If offered time fits, book with `schedule_callback` (date, time HH:MM); else propose nearest fitting slot once; if refused, book nothing.
  - values: `{"callback": {"same_day": false}}`
  - deciding quote: "We never call back the same day: the window is in AHS-5 5.6a."
- **R17** [verified] — _harrow.md mail 'Someone else picks up'_: Wrong number, customer died, or cannot tell who answered: close not reached. On death say only the sentence.
  - verbatim: "I am very sorry to hear that."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "wrong number, deceased, cannot tell who answered"}]}`
- **R61** [verified] — _harrow.md AHS-5 5.6a_: Third-party callback on next business day after call date or the one after, never call date, 10:00–16:00 inclusive. Otherwise propose same time on first business day in window, or nearest end of hours.
  - values: `{"callback": {"open": "10:00", "close": "16:00", "same_day": false, "days_ahead_business": 2}}`
  - deciding quote: "A callback is booked on the next business day after the call date or the business day after that, never the call date itself, at a time from 10:00 to 16:00, both included."
- **R72** [verified] — _harrow.md Document 3 item 5_: Second-look rules unchanged; the 12:00–18:00 hours stay.
  - values: `{"callback": {"open": "12:00", "close": "18:00"}}`
  - deciding quote: "No change to the rules; the 12:00–18:00 hours stay."

## identity (8)

- **R18** — _harrow.md mail 'Security questions'_: Two questions, one at a time: date of birth, then last four digits of phone; `verify_identity` after each answer.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "one wrong answer allowed, asked again"}, {"order": 2, "field": "phone_last4", "retry_rule": "one wrong answer allowed, asked again"}]}`
- **R19** — _harrow.md Document 1 Security questions_: Date of birth sent as YYYY-MM-DD; numeric dates are day, month, year. Hint `day_month_swapped`: ask again with the month as a word; not a wrong answer.
- **R20** [verified] — _harrow.md Document 1 Security questions_: Per question: one wrong answer may be retried; a second wrong answer to the same question ends the check. One wrong on each question still passes if repeats are right. Stricter than the service's three in total.
  - values: `{"max_wrong_answers": 2, "identity": [{"order": 1, "field": "date_of_birth", "retry_rule": "one retry; second wrong answer to the same question ends the check"}, {"order": 2, "field": "phone_last4", "retry_rule": "one retry; second wrong answer to the same question ends the check"}]}`
  - deciding quote: "Our rule is per question: each question may be answered wrongly once and asked again; a second wrong answer to the SAME question ends the check."
- **R21** [verified] — _harrow.md Document 1 Security questions_: When the check ends, do not say what the call was about; say the code card line and close not verified (IDNO).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDNO", "when": "security questions failed"}]}`
- **R22** [verified] — _harrow.md Document 1 Security questions_: If they won't answer, say once the questions protect their personal details; if still not, or they ask again what it's about, close not verified (declined, IDREF).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "would not answer security questions"}]}`
- **R66** [confidence low, samples C] — _openapi.json /verify_identity_: An unreadable `answer` is rejected with ok=false and not counted as a wrong answer; phone_last4 is four digits.
- **R73** — _harrow.md Document 3 item 6_: Moving to the identity service's three-in-total rule rejected; keep one retry per question (second wrong answer to the same question ends the check).
  - values: `{"max_wrong_answers": 2}`
  - deciding quote: "No: we keep one retry per question."
- **R97** — _harrow.openapi.json /verify_identity_: `verify_identity` fields `date_of_birth` (YYYY-MM-DD) then `phone_last4` (four digits); an unreadable value returns ok=false and is not a wrong answer; hint `day_month_swapped`.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"]}, {"order": 2, "field": "phone_last4"}]}`

## disclosure (4)

- **R12** — _harrow.md Document 1 What nobody hears_: Before security questions are passed none of the listed words or product names, including in the reason for the questions; say questions protect their personal details.
  - values: `{"forbidden_words_before_verification": ["overdue", "arrears", "missed", "owe", "debt", "balance", "payment", "account", "card", "credit card", "loan", "car loan"]}`
- **R13** [confidence medium, samples AC] — _harrow.md Document 1 What nobody hears_: Never say the questions are "to access your account"; say they are there to protect the customer's personal details.
- **R23** — _harrow.md Document 1 After the security questions_: After passing, call `get_account`, say the sentence, then one sentence per product: product in words (e.g. "your credit card ending 4821"), overdue amount, days overdue, in AHS-5 5.9 order.
  - verbatim: "I'm calling from Corran Bay Bank's Payments Support team about a missed payment."
- **R24** — _harrow.md mail 'After the security questions'_: Nothing about consequences: no fees, credit file, recovery agents, or court.

## dates (10)

- **R44** **[superseded by R71]** — _harrow.md AHS-5 5.1_: Business day is Monday to Friday excluding closure days; closure days for rest of 2026 per table.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-22", "name": "St Corran's Day"}, {"date": "2026-11-13", "name": "core banking cut-over (planned)"}, {"date": "2026-11-24", "name": "Regatta Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}]}}`
  - deciding quote: "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."
- **R45** — _harrow.md AHS-5 5.1_: No arrangement may be dated on a Saturday, Sunday or closure day.
- **R46** [confidence medium, samples AC] — _harrow.md AHS-5 5.1_: Call date is day 0; "the n-th business day after the call date" counts the first business day after the call date as the 1st.
- **R47** — _harrow.md AHS-5 5.2_: Week runs Monday–Sunday. "This <weekday>"/bare weekday: this week if still to come (today included), else next week. "Next <weekday>": following week. "Tomorrow": next calendar day.
- **R48** **[superseded by R69]** — _harrow.md AHS-5 5.3 table_: Each product banded on its own `days_late`: Early 1–7, Middle 8–20, Late 21–45, over 45 treated as Late, with last dates and attempts per table.
  - values: `{"bands": [{"name": "Early", "min_days": 1, "max_days": 7, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 14, "adjust": "next_business_day"}}, {"name": "Middle", "min_days": 8, "max_days": 20, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 6, "adjust": "none"}}, {"name": "Late", "min_days": 21, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 3, "adjust": "none"}}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "Late"}]}`
  - deciding quote: "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **R56** — _harrow.md AHS-5 5.4 part-payment last date_: Part-payment last date: the 2nd business day after the call date, or the band's last date if earlier.
- **R60** — _harrow.md AHS-5 5.6 table_: Today/business day up to last date: accept. Weekend/closure day: first business day after, or if past last date, last business day before. After last date: offer last date; refusal is an attempt. Past day: ask from today on. Vague: ask once, else propose last date.
- **R69** [verified] (overrides R48) — _harrow.md Document 3 item 3_: Middle band (8–20 days) last date for full payment changes from the 6th to the 4th business day after the call date; Early (14 calendar days, next business day if not) and Late (3rd business day) unchanged; over 45 treated as Late.
  - values: `{"bands": [{"name": "Early", "min_days": 1, "max_days": 7, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 14, "adjust": "next_business_day"}}, {"name": "Middle", "min_days": 8, "max_days": 20, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 4, "adjust": "none"}}, {"name": "Late", "min_days": 21, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 3, "adjust": "none"}}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "Late"}]}`
  - deciding quote: "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **R70** **[not policy]** — _harrow.md Document 3 item 3_: Widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November.
  - deciding quote: "The question of widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November."
- **R71** [verified] (overrides R44) — _harrow.md Document 3 item 4_: Core banking cut-over moved to Friday 6 November 2026, now a closure day; Friday 13 November 2026 is an ordinary business day again. Other closure days unchanged.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-22", "name": "St Corran's Day"}, {"date": "2026-11-06", "name": "core banking cut-over"}, {"date": "2026-11-24", "name": "Regatta Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}]}}`
  - deciding quote: "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."

## amounts (8)

- **R28** — _harrow.md mail 'Partial payments'_: Split payments: record only ONE arrangement per product, the first part, if at least the floor and date fits; say rest stays overdue and we will contact them; never record the second part.
- **R49** **[superseded by R68]** — _harrow.md AHS-5 5.4 floor table_: Floor (smallest recordable amount): credit_card `minimum_payment`; personal_loan and car_loan `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
- **R50** — _harrow.md AHS-5 5.4 rule table row full_: Agrees to full `past_due`: full payment, any valid date up to the band's last date.
- **R51** — _harrow.md AHS-5 5.4 rule table row part_: Offers from the floor up to but not including `past_due`: accept as part payment, dated no later than the part-payment last date.
- **R52** — _harrow.md AHS-5 5.4 rule table row more_: Offers more than `past_due`: record `past_due`.
- **R53** — _harrow.md AHS-5 5.4 rule table row below floor_: Offers less than the floor: say it cannot be recorded and offer the floor once; if refused, product turned down.
- **R55** — _harrow.md AHS-5 5.4 row split_: Wants to split: record only the first part, as a part payment, if at least the floor.
- **R68** [from 2026-10-14] [confidence low, samples ABC] **[verification: mismatch]** (overrides R49) — _harrow.md Document 3 item 2_: From go-live (14 October 2026) the credit card floor changes from `minimum_payment` to half of `past_due`, rounded up to the next multiple of 5, never more than `past_due`; loans stay at `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "percent", "percent": 50, "field": "past_due", "round": "up to next multiple of 5", "cap_to_full": true}}, {"product_types": ["personal_loan"], "rule": {"type": "field", "field": "instalment_amount"}}, {"product_types": ["car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."

## persuasion (10)

- **R25** — _harrow.md Document 1 Asking_: One product: ask the single-product question word for word; several: ask the all-products question, then product by product if not.
  - verbatim: "Can you pay the overdue amount in full today?"
  - verbatim: "Can you pay all of these in full today?"
- **R26** — _harrow.md mail 'Asking'_: Never ask how much the customer can pay in any wording; the assistant proposes every amount.
- **R27** — _harrow.md Document 1 Asking_: A date or amount offered by the customer is never a refusal; check it against the Standard. A plain no starts the AHS-5 5.5 ladder. Never re-offer something already turned down; "too much" per 5.4.
- **R32** — _harrow.md mail 'Second look'_: When a product is turned down (ladder ran out or floor refused), offer once per call before goodbye a second-look call per AHS-5 5.7; customer picks time; book with `schedule_callback` and say the sentence.
  - verbatim: "Your second-look call is booked for {weekday, day month} at {HH:MM}."
- **R33** — _harrow.md mail 'Second look'_: Second look only for turned-down products: not disputes, already-paid, hardship or does-not-want-to-talk. One per call even with two turned-down products.
- **R54** — _harrow.md AHS-5 5.4 row too much_: Full amount too much: offer the floor once, say the rest stays overdue and we will contact them, then agree date; floor refused = turned down, no further attempt.
- **R57** [confidence medium, samples BC] — _harrow.md AHS-5 5.5_: An attempt is used on a no without date or amount, flat refusal, or no answer; counted per product, each starting at attempt 1.
- **R58** — _harrow.md AHS-5 5.5 table_: Attempt 1: full amount on band's last date (Early, Middle), Late on next business day after call date. Attempt 2 (Middle, Late): floor on part-payment last date.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": ["Early", "Middle"], "amount": "full", "date_rule": "the band's last date"}, {"attempt": 1, "bands": ["Late"], "amount": "full", "date_rule": "the next business day after the call date"}, {"attempt": 2, "bands": ["Middle", "Late"], "amount": "floor", "date_rule": "the part-payment last date"}]}`
- **R59** [verified] — _harrow.md AHS-5 5.5_: When band attempts are used, stop: product turned down, note `refused` with attempts made and last offer (amount and date).
  - values: `{"note_reasons": [{"reason": "refused", "when": "attempts exhausted", "text_must_contain": "number of attempts made and last offer, amount and date"}]}`
- **R62** [verified] — _harrow.md AHS-5 5.7_: Second-look call on the 3rd business day after the call date, customer's time 12:00–18:00 inclusive; outside: say hours once, ask again; if still unfit, book nothing.
  - values: `{"callback": {"open": "12:00", "close": "18:00", "same_day": false, "text": "exactly the 3rd business day after the call date"}}`
  - deciding quote: "On the 3rd business day after the call date, at a time the customer chooses from 12:00 to 18:00, both included."

## hardship (2)

- **R38** [verified] — _harrow.md mail 'Things customers say' hardship_: Illness, bereavement, job loss etc.: say the sentence, no attempt at all, say you will put them through to Customer Care, `transfer_to_agent` queue `support`.
  - verbatim: "I'm sorry to hear that."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XCARE", "when": "hardship"}]}`
- **R39** [verified] — _harrow.md Document 1 Things customers say_: If they decline transfer, do not push: `add_note` reason `hardship` on every product with their words, and close. A date or amount they then offer themselves is a normal arrangement.
  - values: `{"note_reasons": [{"reason": "hardship", "when": "hardship, declined transfer", "text_must_contain": "the circumstance in their own words"}], "outcomes": [{"outcome": "no_promise", "reason": "HDNX", "when": "hardship, did not want Customer Care"}]}`

## confirmation (1)

- **R29** — _harrow.md Document 1 Read-back_: Before recording, read back and record only after a clear yes; on a change, check the new value and read back again. With several products, agree, read back and record each before the next.
  - verbatim: "So that is {amount} for your {product} on {weekday, day month}. Is that right?"

## recording (7)

- **R30** — _harrow.md Document 1 Read-back_: After each successful `create_promise` (`ok: true`) say the sentence word for word; never before.
  - verbatim: "Your payment arrangement is recorded."
- **R31** [verified] — _harrow.md Document 1 Read-back_: If `create_promise` fails, try once more; if it fails again, say the apology, `add_note` reason `service_error`, and continue with other products.
  - verbatim: "I'm sorry, I could not record that."
  - values: `{"note_reasons": [{"reason": "service_error", "when": "two failed create_promise tries", "text_must_contain": "\"create_promise\" and the number of tries"}]}`
  - deciding quote: "If `create_promise` fails, try once more."
- **R42** — _harrow.md mail 'Notes'_: Every product ending without an arrangement gets one `add_note`, unless the call was transferred (transfer freezes everything; recorded arrangements stay; no notes) or `get_account` never reached.
- **R63** — _harrow.md AHS-5 5.8_: `create_promise` at most twice per arrangement (one retry); a recorded arrangement is not changed in the same call.
  - deciding quote: "`create_promise` is called at most twice for the same arrangement (one retry)."
- **R93** [verified] — _harrow.md Document 4 notes_: `add_note` reason is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`, and text must contain the specified content per reason.
  - values: `{"note_reasons": [{"reason": "refused", "when": "product turned down", "text_must_contain": "the number of attempts made and the last offer (amount and date)"}, {"reason": "hardship", "when": "hardship, no transfer", "text_must_contain": "what the customer said, in their words"}, {"reason": "dispute", "when": "customer disputes", "text_must_contain": "what is disputed"}, {"reason": "paid", "when": "claims already paid", "text_must_contain": "how and when the customer says they paid"}, {"reason": "service_error", "when": "create_promise failed twice", "text_must_contain": "\"create_promise\" and the number of tries"}]}`
- **R96** — _openapi.json /create_promise_: `create_promise` requires `product_id`, `amount` (number), `date` (format date); one per product.
- **R99** [confidence medium, samples AB] — _harrow.openapi.json /schedule_callback_: `schedule_callback` requires date (format date) and time as HH:MM; used for third-party callbacks and second-look calls.

## special (8)

- **R10** — _harrow.md mail 'Opening'_: If asked whether this is a robot, say the sentence and carry on.
  - verbatim: "Yes, I am an automated assistant."
- **R11** — _harrow.md mail 'Opening'_: If asked whether this is a scam, say they are free to hang up and call the number on the Corran Bay website, and carry on.
- **R34** [verified] — _harrow.md mail 'Things customers say' already paid_: Already paid: say the sentence; no arrangement on that product; `add_note` reason `paid` with how and when paid.
  - verbatim: "Thank you. A payment can take up to two business days to reach us."
  - values: `{"note_reasons": [{"reason": "paid", "when": "customer says already paid", "text_must_contain": "how and when they paid"}]}`
- **R35** [verified] — _harrow.md mail 'Things customers say' dispute_: Not mine / never had it: do not argue, no arrangement on that product, `add_note` reason `dispute` with what is disputed.
  - values: `{"note_reasons": [{"reason": "dispute", "when": "customer disputes", "text_must_contain": "what is disputed"}]}`
- **R36** [verified] — _harrow.md mail 'Things customers say' plan_: Wants a plan, lower monthly amounts or payment holiday: describe nothing, `transfer_to_agent` queue `restructuring`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XRST", "when": "restructuring"}]}`
- **R37** [verified] — _harrow.md mail 'Things customers say' person_: Wants a person: ask once the sentence; if no or asks again, `transfer_to_agent` queue `general`.
  - verbatim: "I can help you with this now. Are you happy to continue with me?"
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XGEN", "when": "wants a person"}]}`
- **R40** [verified] — _harrow.md mail 'Things customers say' does not want to talk_: Say once the sentence; if repeated, close: before security questions declined; after, no arrangement with `refused` note on every open product, no second look.
  - verbatim: "This will only take a moment."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "before security questions"}, {"outcome": "no_promise", "reason": "TDN", "when": "after security questions"}]}`
- **R41** — _harrow.md mail 'Things customers say' unknown_: Anything not answerable from the tools: say the sentence.
  - verbatim: "I don't have that information."

## multi_product (3)

- **R64** — _harrow.md AHS-5 5.9_: Products in order of `days_late`, most first; ties keep `get_account` order. Bands, floors, last dates, attempts per product.
- **R65** [confidence medium, samples AC] — _harrow.md AHS-5 5.9_: Dispute, already-paid or turned-down product does not end the call; go to next product. A transfer ends the call; recorded arrangements stay.
- **R92** — _harrow.md Document 4 several products note_: Several products, nothing recorded, no transfer: all claimed paid → CLMPD; otherwise most serious decides in order SYSF, HDNX, DSPT, TDN2L, TDN. Paid next to turned-down is TDN or TDN2L.
  - values: `{"text": "precedence SYSF > HDNX > DSPT > TDN2L > TDN"}`

## closing (20)

- **R43** — _harrow.md Document 1 Closing_: Every call ends with the code's closing sentence then exactly one `close_call` as last tool call, with outcome and code; for a transfer the sentence is said just before `transfer_to_agent`.
  - deciding quote: "Every call ends with the closing sentence for its code and then exactly one `close_call`, the last tool call, with an outcome and a code from the card."
- **R74** — _harrow.md Document 4 intro_: Every `close_call` has one `outcome` (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from the card; closing sentence said word for word before `close_call` (transfer: before `transfer_to_agent`).
- **R75** [confidence low, samples B] — _harrow.md Document 4 intro_: The closing sentence is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.
- **R76** [verified] — _harrow.md Document 4 table_: Outcome/reason/closing-sentence table: each situation maps to an outcome, reason code and closing sentence said verbatim.
  - verbatim: "Thank you, {title} {last_name}. Your arrangement is in place. Goodbye."
  - verbatim: "Thank you, {title} {last_name}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."
  - verbatim: "Thank you for letting us know. Goodbye."
  - verbatim: "I am putting you through now. Please stay on the line."
  - verbatim: "I am putting you through to Customer Care now. Please stay on the line."
  - verbatim: "Thank you for your time, {title} {last_name}. Goodbye."
  - verbatim: "Thank you for your time, {title} {last_name}. Speak to you then. Goodbye."
  - verbatim: "Thank you for telling me. Take care, {title} {last_name}. Goodbye."
  - verbatim: "We will look into this and write to you. Goodbye."
  - verbatim: "I'm sorry, our system is not responding. We will call you again. Goodbye."
  - verbatim: "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye."
  - verbatim: "I understand. You can use the Corran Bay app or visit any branch. Goodbye."
  - verbatim: "Thank you, we will call back then. Goodbye."
  - verbatim: "Thank you. Goodbye."
  - values: `{"outcomes": [{"outcome": "promise", "reason": "FULLPTP", "when": "at least one arrangement recorded, no transfer after it, every arrangement for the full overdue amount"}, {"outcome": "promise", "reason": "PARTPTP", "when": "at least one arrangement recorded, no transfer after it, at least one for less than the overdue amount"}, {"outcome": "paid", "reason": "CLMPD", "when": "every product claimed as already paid, nothing recorded"}, {"outcome": "transferred", "reason": "XRST", "when": "transferred to restructuring"}, {"outcome": "transferred", "reason": "XGEN", "when": "transferred to a person on request (queue general)"}, {"outcome": "transferred", "reason": "XCARE", "when": "transferred to Customer Care, hardship (queue support)"}, {"outcome": "no_promise", "reason": "TDN", "when": "no arrangement; turned down; no second-look booked; or would not continue after security questions"}, {"outcome": "no_promise", "reason": "TDN2L", "when": "no arrangement; turned down; second-look call booked"}, {"outcome": "no_promise", "reason": "HDNX", "when": "hardship, customer did not want Customer Care"}, {"outcome": "no_promise", "reason": "DSPT", "when": "customer disputes"}, {"outcome": "no_promise", "reason": "SYSF", "when": "two failed tries of create_promise, or get_account failing"}, {"outcome": "not_verified", "reason": "IDNO", "when": "security questions failed"}, {"outcome": "not_verified", "reason": "IDREF", "when": "customer would not answer the security questions"}, {"outcome": "not_reached", "reason": "TPCB", "when": "someone else answered, callback booked"}, {"outcome": "not_reached", "reason": "NOCON", "when": "someone else answered, no callback; wrong number; deceased; could not tell who answered"}]}`
- **R77** [confidence low, samples A] [verified] — _harrow.md Document 4 table row FULLPTP_: At least one arrangement recorded, no transfer after it, all for full overdue amount: promise / FULLPTP with this sentence.
  - verbatim: "Thank you, {title} {last_name}. Your arrangement is in place. Goodbye."
  - values: `{"outcomes": [{"outcome": "promise", "reason": "FULLPTP", "when": "all arrangements full"}]}`
- **R78** [confidence low, samples A] [verified] — _harrow.md Document 4 table row PARTPTP_: At least one arrangement recorded, no transfer after it, at least one for less than overdue amount: promise / PARTPTP.
  - verbatim: "Thank you, {title} {last_name}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PARTPTP", "when": "at least one part arrangement"}]}`
- **R79** [confidence low, samples A] [verified] — _harrow.md Document 4 table row CLMPD_: Every product claimed already paid, nothing recorded: paid / CLMPD.
  - verbatim: "Thank you for letting us know. Goodbye."
  - values: `{"outcomes": [{"outcome": "paid", "reason": "CLMPD", "when": "all claimed paid"}]}`
- **R80** [confidence low, samples A] [verified] — _harrow.md Document 4 table row XRST_: Transferred to restructuring: transferred / XRST; sentence said before `transfer_to_agent`.
  - verbatim: "I am putting you through now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XRST", "when": "queue restructuring"}]}`
- **R81** [confidence low, samples A] [verified] — _harrow.md Document 4 table row XGEN_: Transferred to a person on request (queue `general`): transferred / XGEN.
  - verbatim: "I am putting you through now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XGEN", "when": "queue general"}]}`
- **R82** [confidence low, samples A] [verified] — _harrow.md Document 4 table row XCARE_: Transferred to Customer Care for hardship (queue `support`): transferred / XCARE.
  - verbatim: "I am putting you through to Customer Care now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XCARE", "when": "queue support"}]}`
- **R83** [confidence low, samples A] [verified] — _harrow.md Document 4 table row TDN_: No arrangement, product(s) turned down, no second-look booked, or customer would not continue after security questions: no_promise / TDN.
  - verbatim: "Thank you for your time, {title} {last_name}. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "TDN", "when": "turned down, no second look; or would not continue"}]}`
- **R84** [confidence low, samples A] [verified] — _harrow.md Document 4 table row TDN2L_: No arrangement, product(s) turned down, second-look call booked: no_promise / TDN2L.
  - verbatim: "Thank you for your time, {title} {last_name}. Speak to you then. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "TDN2L", "when": "second look booked"}]}`
- **R85** [confidence low, samples A] [verified] — _harrow.md Document 4 table row HDNX_: Hardship, customer did not want Customer Care: no_promise / HDNX.
  - verbatim: "Thank you for telling me. Take care, {title} {last_name}. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "HDNX", "when": "hardship declined transfer"}]}`
- **R86** [confidence low, samples A] [verified] — _harrow.md Document 4 table row DSPT_: Customer disputes: no_promise / DSPT.
  - verbatim: "We will look into this and write to you. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "DSPT", "when": "dispute"}]}`
- **R87** [confidence low, samples A] [verified] — _harrow.md Document 4 table row SYSF_: Bank system failed (two failed `create_promise` tries, or `get_account` failing): no_promise / SYSF.
  - verbatim: "I'm sorry, our system is not responding. We will call you again. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SYSF", "when": "system failure"}]}`
- **R88** [confidence low, samples A] [verified] — _harrow.md Document 4 table row IDNO_: Security questions failed: not_verified / IDNO.
  - verbatim: "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDNO", "when": "failed check"}]}`
- **R89** [confidence low, samples A] [verified] — _harrow.md Document 4 table row IDREF_: Customer would not answer the security questions: not_verified / IDREF.
  - verbatim: "I understand. You can use the Corran Bay app or visit any branch. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "declined questions"}]}`
- **R90** [confidence low, samples A] [verified] — _harrow.md Document 4 table row TPCB_: Someone else answered, callback booked: not_reached / TPCB.
  - verbatim: "Thank you, we will call back then. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "TPCB", "when": "third-party callback booked"}]}`
- **R91** [confidence low, samples A] [verified] — _harrow.md Document 4 table row NOCON_: Someone else answered and no callback booked; wrong number; customer deceased; could not tell who answered: not_reached / NOCON.
  - verbatim: "Thank you. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "no contact"}]}`
- **R95** — _harrow.openapi.json /close_call_: `close_call` is always the last tool call; nothing is accepted after it; `reason` required for every outcome.
  - deciding quote: "Every `close_call` has one `outcome` from the dialler's list (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from this card."

## wording (1)

- **R09** — _harrow.md mail 'Opening'_: Once the right person is on the line, address them as {title} {last_name}.

## other (10)

- **R01** — _harrow.md Document 1 intro_: Figures (bands, last dates, floors, closure days, hours) are in AHS-5 section 5; where the mail and the Standard differ, the Standard applies. Codes are on the dialler code card.
- **R02** **[not policy]** [confidence medium, samples BC] — _harrow.md Document 1 intro_: Decisions are expected from the campaign review on Friday 9 October; minutes will follow.
  - deciding quote: "We have a campaign review on Friday the 9th and I expect a few decisions to come out of it, so I will send the minutes on as well."
- **R03** — _harrow.md Document 1 Who we ring_: Customers 1–45 days behind on 1–3 products (credit card, personal loan, car loan). Dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms), `now` (e.g. 2026-10-14T11:00); all dates run from `now`.
  - deciding quote: "Personal customers who are 1 to 45 days behind on one, two or three products: a credit card, a personal loan, a car loan."
- **R04** [confidence medium, samples AC] — _harrow.md Document 1 Who we ring_: Dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now` (form `2026-10-14T11:00`); every date is worked out from `now`.
  - deciding quote: "The dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now`, the date and time of the call in the form `2026-10-14T11:00`."
- **R05** — _harrow.md mail 'Who we ring'_: `customer_id` goes into every tool call.
- **R06** [confidence medium, samples AC] — _harrow.md Document 1 Who we ring_: Systems accept anything (a Sunday promise, one pound), so the assistant must enforce all rules itself.
- **R67** — _harrow.md Document 3 item 1_: Go-live confirmed for the first dialler run on Wednesday 14 October 2026; the assistant is checked against these minutes from that day.
- **R94** [confidence low, samples C] — _openapi.json /create_promise_: `create_promise` requires customer_id, product_id, amount, date (format date); one per product.
- **R98** — _harrow.openapi.json /get_account_: `get_account` is refused until both security questions are passed; returns products with type, card_last4, past_due, days_late, minimum_payment, instalment_amount.
- **R100** **[not policy]** [confidence medium] — _harrow.md Document 3 item 7_: AOB: Christmas lunch on Friday 11 December; Treasury dashboard moving to the new BI tool in January. Decides nothing for these calls; no rule for the assistant.
  - deciding quote: "The Christmas lunch is on Friday 11 December."
