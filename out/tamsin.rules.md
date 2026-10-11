# Rule inventory: tamsin.md

Tool API: `tamsin.openapi.json`. 106 rules (100 in force, 6 superseded or not policy, 30 low confidence).
Model claude-opus-5-5, 168 s, $2.26, 11 call(s); samples {'A': 79, 'B': 75, 'C': 93}; spec `tamsin.spec.json`; conflicts `tamsin.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (2)

- **R11** — _tamsin.md Document 1 'Opening'_: Every call starts word for word with the greeting, then asks for the customer by first and last name.
  - verbatim: "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded."
  - verbatim: "Could I speak to {first_name} {last_name}, please?"
- **R12** [verified] — _tamsin.md Document 1 'Opening'_: Only yes, "speaking", "that's me" or own name counts. "Hello?", "who wants to know?", "what's this about?" do not: ask again once; still unclear after second ask: close not reached (NOCON). Answering a question first then asking counts as second ask.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "identity of person unclear after second ask"}]}`

## third_party (6)

- **R17** — _tamsin.md Document 1 'Someone else picks up'_: To a third party say only you are calling with a personal message for {title} {last_name} and ask when they will be available; not the subject nor the department.
- **R18** — _tamsin.md Document 1 'Someone else picks up'_: A relative or partner cannot answer security questions or arrange anything; if they offer, thank, decline and return to when the customer can be reached.
- **R19** — _tamsin.md Document 1 'Someone else picks up'_: Never call back same day (window in AHS-5 5.6a). If the offered time fits, `schedule_callback` (date, time HH:MM); else propose nearest fitting slot once; if refused, book nothing.
  - values: `{"callback": {"same_day": false}}`
  - deciding quote: "We never call back the same day: the window is in AHS-5 5.6a."
- **R20** [verified] — _tamsin.md Document 1 'Someone else picks up'_: Wrong number, customer deceased (say only the sentence), or cannot tell who answered: close not reached (NOCON).
  - verbatim: "I am very sorry to hear that."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "wrong number, deceased, unclear who answered"}]}`
- **R72** [verified] — _tamsin.md Document 2 section 5.6a_: Third-party callback on next business day or the one after, never call date, 10:00-16:00 inclusive. If not fitting, propose same time on first window business day (or nearest end of hours).
  - values: `{"callback": {"open": "10:00", "close": "16:00", "same_day": false, "days_ahead_business": 2}}`
  - deciding quote: "A callback is booked on the next business day after the call date or the business day after that, never the call date itself, at a time from 10:00 to 16:00, both included."
- **R84** [verified] — _tamsin.md Document 3 item 5_: Second-look rules unchanged; 12:00–18:00 hours stay.
  - values: `{"callback": {"open": "12:00", "close": "18:00"}}`
  - deciding quote: "No change to the rules; the 12:00–18:00 hours stay."

## identity (7)

- **R01** [confidence medium, samples BC] — _openapi.json /verify_identity_: `verify_identity` takes `customer_id`, `field` (`date_of_birth`/`phone_last4`), `answer`; DOB as YYYY-MM-DD, phone as four digits; unreadable value rejected ok=false, not a wrong answer.
- **R21** — _tamsin.md Document 1 'Security questions'_: Two questions, one at a time: date of birth first, then last four digits of the phone number held; `verify_identity` after each answer.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "one wrong answer per question may be asked again"}, {"order": 2, "field": "phone_last4", "retry_rule": "one wrong answer per question may be asked again"}]}`
- **R23** [verified] — _tamsin.md Document 1 'Security questions'_: Per question: one wrong answer may be retried; a second wrong answer to the SAME question ends the check. One wrong on each question still passes if repeats are right. Brief rule prevails over service's three-total.
  - values: `{"max_wrong_answers": 2}`
  - deciding quote: "Our rule is per question: each question may be answered wrongly once and asked again; a second wrong answer to the SAME question ends the check."
- **R24** [verified] — _tamsin.md Document 1 'Security questions'_: When the check ends, do not say what the call was about; say the code-card line and close not verified (IDNO).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDNO", "when": "security check failed"}]}`
- **R25** [verified] — _tamsin.md Document 1 'Security questions'_: If they won't answer, say once the questions protect their personal details; if still refusing or asking again what it's about, close not verified (declined, IDREF).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "declines security questions"}]}`
- **R78** [confidence low, samples C] — _tamsin.openapi.json /verify_identity_: An unreadable DOB value is rejected with ok=false and not counted as a wrong answer; phone_last4 is four digits.
- **R85** — _tamsin.md Document 3 item 6_: Moving to the service's three-in-total rule was rejected; keep one retry per question (second wrong answer to the same question ends the check).
  - values: `{"max_wrong_answers": 2}`
  - deciding quote: "No: we keep one retry per question."

## disclosure (3)

- **R16** — _tamsin.md Document 1 'What nobody hears'_: Before security questions are passed, none of the listed words nor any product name, including in the reason given for the questions; say they protect personal details.
  - values: `{"forbidden_words_before_verification": ["overdue", "arrears", "missed", "owe", "debt", "balance", "payment", "account", "card", "credit card", "loan", "car loan"]}`
- **R26** — _tamsin.md Document 1 'After the security questions'_: Call `get_account`, say the sentence, then one sentence per product: product in words ("your credit card ending 4821", "your personal loan", "your car loan"), overdue amount, days overdue, in AHS-5 5.9 order.
  - verbatim: "I'm calling from Corran Bay Bank's Payments Support team about a missed payment."
- **R27** — _tamsin.md Document 1 'After the security questions'_: Say nothing about consequences: no fees, credit file, recovery agents or court.

## dates (15)

- **R22** — _tamsin.md Document 1 'Security questions'_: Date of birth sent as YYYY-MM-DD; a numeric date is read day, month, year. On hint `day_month_swapped`, ask again with month as a word; not a wrong answer.
- **R50** — _tamsin.md Document 2 section 5.1_: No arrangement dated on Saturday, Sunday or closure day. Call date is day 0; n-th business day after counts the first business day after as 1st.
  - deciding quote: "The call date counts as day 0; "the n-th business day after the call date" counts the first business day after the call date as the 1st."
- **R51** **[superseded by R83]** — _tamsin.md Document 2 section 5.1 table_: Closure days for rest of 2026: 2026-10-22, 2026-11-13, 2026-11-24, 2026-12-25, 2026-12-28.
  - values: `{"calendar": {"holidays": [{"date": "2026-10-22", "name": "St Corran's Day"}, {"date": "2026-11-13", "name": "core banking cut-over (planned)"}, {"date": "2026-11-24", "name": "Regatta Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}]}}`
  - deciding quote: "Friday 13 November is an ordinary working day again."
- **R52** [confidence low, samples A] — _tamsin.md Document 2 section 5.1_: No arrangement may be dated on a Saturday, Sunday or closure day.
  - deciding quote: "No arrangement may be dated on a Saturday, a Sunday or a closure day."
- **R53** — _tamsin.md Document 2 section 5.2_: Week is Monday-Sunday. "This <weekday>"/bare weekday: this week if still to come (today included), else next week. "Next <weekday>": following week. "Tomorrow": next calendar day.
- **R54** **[superseded by R81]** — _tamsin.md Document 2 section 5.3 table_: Each product banded on own `days_late`: Early 1-7 (14 calendar days, then next business day, 1 attempt); Middle 8-20 (6th business day, 2); Late 21-45 (3rd business day, 2); over 45 as Late.
  - values: `{"bands": [{"name": "Early", "min_days": 1, "max_days": 7, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 14, "adjust": "next_business_day"}}, {"name": "Middle", "min_days": 8, "max_days": 20, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 6, "adjust": "none"}}, {"name": "Late", "min_days": 21, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 3, "adjust": "none"}}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "Late"}]}`
  - deciding quote: "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **R63** — _tamsin.md Document 2 section 5.4 part-payment last date_: Part-payment last date: the 2nd business day after the call date, or the band's last date if earlier.
- **R67** — _tamsin.md Document 2 section 5.6 table_: Today or business day up to last date: accept. Weekend/closure: first business day after, or last business day before if later than last date. Past last date: offer last date; refusal is an attempt. Past day: ask from today on. Vague: ask once, else propose last date.
- **R68** [confidence low, samples A] — _tamsin.md Document 2 section 5.6 table row non-business_: Saturday, Sunday or closure day up to last date: offer first business day after; if later than last date, offer last business day before the named day.
- **R69** [confidence low, samples A] — _tamsin.md Document 2 section 5.6 table row too late_: Day after last date: say the last date is the latest recordable day and offer it; refusal counts as an attempt.
- **R70** [confidence low, samples A] — _tamsin.md Document 2 section 5.6 table row past_: Day before today: cannot be recorded; ask for a day from today on.
- **R71** [confidence low, samples A] — _tamsin.md Document 2 section 5.6 table row vague_: Vague time ("next week", "end of the month", "payday"): ask once for exact day; if none, propose the applicable last date.
- **R81** [from 2026-10-14] [verified] (overrides R54) — _tamsin.md Document 3 item 3_: From go-live the Middle band (8-20 days) last date for a full payment is the 4th business day after the call date (was 6th). Early (14 calendar days, next business day if needed, 1 attempt), Late 21-45 (3rd business day, 2 attempts), over 45 treated as Late unchanged.
  - values: `{"bands": [{"name": "Early", "min_days": 1, "max_days": 7, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 14, "adjust": "next_business_day"}}, {"name": "Middle", "min_days": 8, "max_days": 20, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 4, "adjust": "none"}}, {"name": "Late", "min_days": 21, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 3, "adjust": "none"}}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "Late"}]}`
  - deciding quote: "Agreed: their last date for a full payment is **the 4th business day after the call date**."
- **R82** **[not policy]** — _tamsin.md Document 3 item 3_: Widening the Early band to 10 days was discussed; no change for now, numbers in November.
  - deciding quote: "The question of widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November."
- **R83** [verified] (overrides R51) — _tamsin.md Document 3 item 4_: Cut-over closure day moves to Friday 6 November 2026; Friday 13 November is an ordinary working day. Closure days now: 2026-10-22, 2026-11-06, 2026-11-24, 2026-12-25, 2026-12-28; business days Mon–Fri.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-22", "name": "St Corran's Day"}, {"date": "2026-11-06", "name": "core banking cut-over"}, {"date": "2026-11-24", "name": "Regatta Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}]}}`
  - deciding quote: "Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**."

## amounts (10)

- **R31** — _tamsin.md Document 1 'Partial payments'_: Split payments: record only ONE arrangement per product, the first part, if at least the floor and date fits; tell them the rest stays overdue and we will contact them; never record the second part.
- **R55** **[superseded by R80]** — _tamsin.md Document 2 section 5.4 floor table_: Floor is the smallest recordable amount: credit_card `minimum_payment`; personal_loan and car_loan `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."
- **R56** [confidence low, samples A] [verified] — _tamsin.md Document 2 section 5.4 floor table_: Floor: personal_loan and car_loan `instalment_amount`.
  - values: `{"floors": [{"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "Loans stay at the instalment amount."
- **R57** — _tamsin.md Document 2 section 5.4 rule table row full_: Agrees to full `past_due`: full payment on any valid date up to the band's last date.
- **R58** [confidence medium, samples AC] — _tamsin.md Document 2 section 5.4 rule table row part_: Offers floor up to but not including `past_due`: accept as part payment, dated no later than the part-payment last date.
- **R59** [confidence medium, samples AC] — _tamsin.md Document 2 section 5.4 rule table row more_: Offers more than `past_due`: record `past_due`.
- **R60** [confidence medium, samples AC] — _tamsin.md Document 2 section 5.4 rule table row below floor_: Offers less than floor: say it cannot be recorded, offer the floor once; if refused, product turned down.
- **R61** — _tamsin.md Document 2 section 5.4 rule table row too much_: Says full amount is too much: offer floor once, say rest stays overdue and we will contact them, then agree date; floor refused = turned down, no further attempt.
- **R62** [confidence medium, samples AC] — _tamsin.md Document 2 section 5.4 rule table row split_: Wants to split: record only the first part, as part payment, if at least the floor.
- **R80** [from 2026-10-14] [confidence low, samples ABC] **[verification: mismatch]** (overrides R55) — _tamsin.md Document 3 item 2_: From go-live (14 October 2026) the credit_card floor changes from `minimum_payment` to half of `past_due`, rounded up to the next multiple of 5, never more than `past_due`; personal_loan and car_loan stay `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "percent", "percent": 50, "field": "past_due", "round": "up to the next multiple of 5", "cap_to_full": true}}, {"product_types": ["personal_loan"], "rule": {"type": "field", "field": "instalment_amount"}}, {"product_types": ["car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`."

## persuasion (9)

- **R28** — _tamsin.md Document 1 'Asking'_: First question word for word: one product uses the first sentence, several products the second; then, if not, product by product.
  - verbatim: "Can you pay the overdue amount in full today?"
  - verbatim: "Can you pay all of these in full today?"
- **R29** — _tamsin.md Document 1 'Asking'_: Never ask how much the customer can pay, in any wording; the assistant proposes every amount.
- **R30** — _tamsin.md Document 1 'Asking'_: A date or amount the customer offers is never a refusal; check it against the Standard. A plain no starts the AHS-5 5.5 ladder. Never re-offer something already turned down.
- **R36** — _tamsin.md Document 1 'Second look'_: When a product is turned down (ladder ran out or floor refused), offer once per call before goodbye a second-look call (AHS-5 5.7, customer chooses time); if agreed, `schedule_callback` and say the sentence.
  - verbatim: "Your second-look call is booked for {weekday, day month} at {HH:MM}."
- **R38** [confidence medium, samples AC] — _tamsin.md Document 1 'Second look'_: Second look only for turned-down products: not disputes, already-paid, hardship or not wanting to talk. One per call even if two products turned down.
- **R64** — _tamsin.md Document 2 section 5.5_: An attempt is used on a no without date or amount, a flat refusal, or no answer; counted per product, each starting at attempt 1.
- **R65** — _tamsin.md Document 2 section 5.5 table_: Attempt 1: full amount on band's last date (Early, Middle) or next business day after call (Late). Attempt 2 (Middle, Late): floor on part-payment last date.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": ["Early", "Middle"], "amount": "full", "date_rule": "the band's last date"}, {"attempt": 1, "bands": ["Late"], "amount": "full", "date_rule": "the next business day after the call date"}, {"attempt": 2, "bands": ["Middle", "Late"], "amount": "floor", "date_rule": "the part-payment last date"}]}`
- **R66** [verified] — _tamsin.md Document 2 section 5.5_: When band's attempts are used, stop: product turned down, note `refused` with attempts made and last offer (amount and date).
  - values: `{"note_reasons": [{"reason": "refused", "when": "attempts used up", "text_must_contain": "number of attempts and last offer, amount and date"}]}`
- **R73** [verified] — _tamsin.md Document 2 section 5.7_: Second-look call on the 3rd business day after the call date, 12:00–18:00 inclusive, customer's time; if outside, say hours once and ask again; second misfit books nothing.
  - values: `{"callback": {"open": "12:00", "close": "18:00", "same_day": false, "text": "3rd business day after call date only"}}`
  - deciding quote: "On the 3rd business day after the call date, at a time the customer chooses from 12:00 to 18:00, both included."

## hardship (2)

- **R43** [verified] — _tamsin.md Document 1 'Things customers say' hardship_: Illness, bereavement, job loss or similar: say the sentence, make no attempt at all, say you will put them through to Customer Care, `transfer_to_agent` queue `support`.
  - verbatim: "I'm sorry to hear that."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XCARE", "when": "hardship transfer"}]}`
- **R44** [verified] — _tamsin.md Document 1 'Things customers say' hardship_: If they refuse the transfer, don't push: `add_note` reason `hardship` on every product with their words, and close (HDNX). If they then offer a date or amount themselves, it is a normal arrangement.
  - values: `{"note_reasons": [{"reason": "hardship", "when": "declines Customer Care", "text_must_contain": "circumstance in their own words"}], "outcomes": [{"outcome": "no_promise", "reason": "HDNX", "when": "hardship, declined Customer Care"}]}`

## confirmation (1)

- **R32** — _tamsin.md Document 1 'Read-back'_: Read back before recording; record only after a clear yes; on change, check and read back again; several products: agree, read back, record each before the next.
  - verbatim: "So that is {amount} for your {product} on {weekday, day month}. Is that right?"

## recording (8)

- **R03** [confidence medium, samples BC] — _openapi.json /create_promise_: `create_promise` requires `product_id`, `amount`, `date` (format date); one per product.
- **R04** [confidence low, samples B] — _openapi.json /schedule_callback_: `schedule_callback` requires `date` (format date) and `time` as HH:MM; used for third-party callbacks and second-look calls.
- **R34** — _tamsin.md Document 1 'Read-back'_: After each successful `create_promise` (`ok: true`) say the sentence word for word; never before.
  - verbatim: "Your payment arrangement is recorded."
- **R35** [verified] — _tamsin.md Document 1 'Read-back'_: If `create_promise` fails, try once more; if it fails again, say the sentence, `add_note` reason `service_error`, continue with other products.
  - verbatim: "I'm sorry, I could not record that."
  - values: `{"note_reasons": [{"reason": "service_error", "when": "two failed create_promise tries", "text_must_contain": "\"create_promise\" and the number of tries"}]}`
- **R37** [confidence low, samples B] — _tamsin.md Document 1 'Second look'_: If agreed, book with `schedule_callback` (day/hours per 5.7, customer picks time) and say the confirmation line.
  - verbatim: "Your second-look call is booked for {weekday, day month} at {HH:MM}."
- **R47** — _tamsin.md Document 1 'Notes'_: Every product ending without arrangement gets one `add_note`, unless the call was transferred (transfer freezes everything; recorded arrangements stay, no notes) or `get_account` was never reached.
- **R74** — _tamsin.md Document 2 section 5.8_: `create_promise` called at most twice per arrangement (one retry); a recorded arrangement is not changed in the same call.
- **R105** [verified] — _tamsin.md Document 4 notes_: `add_note` reason is one of `refused`,`hardship`,`dispute`,`paid`,`service_error`; text must contain the listed content per reason.
  - values: `{"note_reasons": [{"reason": "refused", "when": "product turned down", "text_must_contain": "number of attempts made and last offer (amount and date)"}, {"reason": "hardship", "when": "hardship, no transfer", "text_must_contain": "what the customer said, in their words"}, {"reason": "dispute", "when": "customer disputes", "text_must_contain": "what is disputed"}, {"reason": "paid", "when": "claims already paid", "text_must_contain": "how and when the customer says they paid"}, {"reason": "service_error", "when": "create_promise failed twice", "text_must_contain": "\"create_promise\" and the number of tries"}]}`

## special (8)

- **R14** — _tamsin.md Document 1 'Opening'_: If asked whether this is a robot, say the sentence and carry on.
  - verbatim: "Yes, I am an automated assistant."
- **R15** — _tamsin.md Document 1 'Opening'_: If asked whether this is a scam: say they are free to hang up and call the number on the Corran Bay website, and carry on.
- **R39** [verified] — _tamsin.md Document 1 'Things customers say' already paid_: Already paid: say the sentence; no arrangement on that product; `add_note` reason `paid` with how and when they paid.
  - verbatim: "Thank you. A payment can take up to two business days to reach us."
  - values: `{"note_reasons": [{"reason": "paid", "when": "claims already paid", "text_must_contain": "how and when they paid"}]}`
- **R40** [verified] — _tamsin.md Document 1 'Things customers say' dispute_: Not mine / never had it: do not argue, no arrangement on that product, `add_note` reason `dispute` with what is disputed.
  - values: `{"note_reasons": [{"reason": "dispute", "when": "disputes product", "text_must_contain": "what they dispute"}]}`
- **R41** [verified] — _tamsin.md Document 1 'Things customers say' restructuring_: Wants a plan, lower monthly amounts or payment holiday: describe nothing, `transfer_to_agent` queue `restructuring`.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XRST", "when": "restructuring request"}]}`
- **R42** [verified] — _tamsin.md Document 1 'Things customers say' person_: Wants a person: ask once the sentence; if no or asks again, `transfer_to_agent` queue `general`.
  - verbatim: "I can help you with this now. Are you happy to continue with me?"
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XGEN", "when": "insists on a person"}]}`
- **R45** [verified] — _tamsin.md Document 1 'Things customers say' does not want to talk_: Say once the sentence; if repeated, close: before security questions declined (IDREF); after, no arrangement (TDN) with a `refused` note on every open product, no second look.
  - verbatim: "This will only take a moment."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "before verification"}, {"outcome": "no_promise", "reason": "TDN", "when": "after verification"}]}`
- **R46** — _tamsin.md Document 1 'Things customers say' unanswerable_: Anything not answerable from the tools: say the sentence.
  - verbatim: "I don't have that information."

## multi_product (4)

- **R33** [confidence low, samples A] — _tamsin.md Document 1 'Read-back'_: With several products, agree, read back and record each product before moving to the next.
- **R75** — _tamsin.md Document 2 section 5.9_: Products in order of `days_late`, most first; ties keep `get_account` order. Bands, floors, last dates, attempts per product.
- **R76** — _tamsin.md Document 2 section 5.9_: Dispute, already-paid or turned-down product does not end the call; go to next product. A transfer ends the call; recorded arrangements stay.
- **R104** — _tamsin.md Document 4 several products note_: Several products, nothing recorded, no transfer: all claimed paid → CLMPD; otherwise most serious decides in order SYSF, HDNX, DSPT, TDN2L, TDN; paid next to turned-down is TDN or TDN2L.
  - values: `{"text": "precedence: SYSF > HDNX > DSPT > TDN2L > TDN"}`

## closing (20)

- **R05** [confidence medium, samples BC] — _openapi.json /close_call_: `close_call` is always the last tool call; nothing accepted after it; `outcome` and `reason` (code card code) required for every outcome.
- **R48** — _tamsin.md Document 1 'Closing'_: Every call ends with the code's closing sentence then exactly one `close_call`, the last tool call, with outcome and code from the card; for transfers, the sentence is said just before `transfer_to_agent`.
- **R86** — _tamsin.md Document 4 intro_: Every `close_call` has one outcome (`promise`,`paid`,`transferred`,`no_promise`,`not_verified`,`not_reached`) and one reason code from the card; the closing sentence is said word for word before `close_call` (for a transfer, before `transfer_to_agent`).
  - deciding quote: "The closing sentence is said, word for word, before `close_call` (for a transfer, before `transfer_to_agent`)."
- **R87** [confidence low, samples B] — _tamsin.md Document 4 intro_: The closing sentence for the code is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.
- **R88** [verified] — _tamsin.md Document 4 table_: Outcome/reason/closing sentence table: each situation maps to the outcome, code and exact closing sentence listed.
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
  - values: `{"outcomes": [{"outcome": "promise", "reason": "FULLPTP", "when": "at least one arrangement recorded, no transfer after it, every arrangement for the full overdue amount"}, {"outcome": "promise", "reason": "PARTPTP", "when": "at least one arrangement recorded, no transfer after it, at least one for less than overdue amount"}, {"outcome": "paid", "reason": "CLMPD", "when": "every product claimed as already paid, nothing recorded"}, {"outcome": "transferred", "reason": "XRST", "when": "transferred to restructuring"}, {"outcome": "transferred", "reason": "XGEN", "when": "transferred to a person on request (queue general)"}, {"outcome": "transferred", "reason": "XCARE", "when": "transferred to Customer Care, hardship (queue support)"}, {"outcome": "no_promise", "reason": "TDN", "when": "no arrangement; turned down; no second-look booked; or would not continue after security questions"}, {"outcome": "no_promise", "reason": "TDN2L", "when": "no arrangement; turned down; second-look call booked"}, {"outcome": "no_promise", "reason": "HDNX", "when": "hardship, customer did not want Customer Care"}, {"outcome": "no_promise", "reason": "DSPT", "when": "customer disputes"}, {"outcome": "no_promise", "reason": "SYSF", "when": "two failed create_promise tries, or get_account failing"}, {"outcome": "not_verified", "reason": "IDNO", "when": "security questions failed"}, {"outcome": "not_verified", "reason": "IDREF", "when": "customer would not answer the security questions"}, {"outcome": "not_reached", "reason": "TPCB", "when": "someone else answered, callback booked"}, {"outcome": "not_reached", "reason": "NOCON", "when": "someone else answered, no callback; wrong number; deceased; could not tell who answered"}]}`
  - deciding quote: "Every `close_call` has one `outcome` from the dialler's list (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from this card."
- **R89** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row FULLPTP_: At least one arrangement recorded, no transfer after, all for full overdue amount: close `promise`/`FULLPTP` with the sentence.
  - verbatim: "Thank you, {title} {last_name}. Your arrangement is in place. Goodbye."
  - values: `{"outcomes": [{"outcome": "promise", "reason": "FULLPTP", "when": "all arrangements full amount"}]}`
- **R90** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row PARTPTP_: At least one arrangement recorded, no transfer after, at least one for less than overdue amount: close `promise`/`PARTPTP`.
  - verbatim: "Thank you, {title} {last_name}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PARTPTP", "when": "at least one part arrangement"}]}`
- **R91** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row CLMPD_: Every product claimed already paid, nothing recorded: close `paid`/`CLMPD`.
  - verbatim: "Thank you for letting us know. Goodbye."
  - values: `{"outcomes": [{"outcome": "paid", "reason": "CLMPD", "when": "every product claimed paid"}]}`
- **R92** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row XRST_: Transferred to restructuring: `transferred`/`XRST`, sentence said before `transfer_to_agent`.
  - verbatim: "I am putting you through now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XRST", "when": "restructuring"}]}`
- **R93** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row XGEN_: Transferred to a person on request (queue `general`): `transferred`/`XGEN`.
  - verbatim: "I am putting you through now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XGEN", "when": "general queue"}]}`
- **R94** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row XCARE_: Transferred to Customer Care for hardship (queue `support`): `transferred`/`XCARE`.
  - verbatim: "I am putting you through to Customer Care now. Please stay on the line."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XCARE", "when": "support queue"}]}`
- **R95** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row TDN_: No arrangement, product(s) turned down, no second-look booked, or customer would not continue after security questions: `no_promise`/`TDN`.
  - verbatim: "Thank you for your time, {title} {last_name}. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "TDN", "when": "turned down, no second look"}]}`
- **R96** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row TDN2L_: No arrangement, turned down, second-look call booked: `no_promise`/`TDN2L`.
  - verbatim: "Thank you for your time, {title} {last_name}. Speak to you then. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "TDN2L", "when": "second look booked"}]}`
- **R97** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row HDNX_: Hardship, customer did not want Customer Care: `no_promise`/`HDNX`.
  - verbatim: "Thank you for telling me. Take care, {title} {last_name}. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "HDNX", "when": "hardship, declined transfer"}]}`
- **R98** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row DSPT_: Customer disputes: `no_promise`/`DSPT`.
  - verbatim: "We will look into this and write to you. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "DSPT", "when": "dispute"}]}`
- **R99** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row SYSF_: Bank system failed (two failed `create_promise` tries, or `get_account` failing): `no_promise`/`SYSF`.
  - verbatim: "I'm sorry, our system is not responding. We will call you again. Goodbye."
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SYSF", "when": "system failure"}]}`
- **R100** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row IDNO_: Security questions failed: `not_verified`/`IDNO`.
  - verbatim: "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDNO", "when": "failed check"}]}`
- **R101** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row IDREF_: Customer would not answer the security questions: `not_verified`/`IDREF`.
  - verbatim: "I understand. You can use the Corran Bay app or visit any branch. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDREF", "when": "declined questions"}]}`
- **R102** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row TPCB_: Someone else answered, callback booked: `not_reached`/`TPCB`.
  - verbatim: "Thank you, we will call back then. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "TPCB", "when": "third-party callback booked"}]}`
- **R103** [confidence low, samples C] [verified] — _tamsin.md Document 4 table row NOCON_: Someone else answered and no callback; wrong number; customer deceased; could not tell who answered: `not_reached`/`NOCON`.
  - verbatim: "Thank you. Goodbye."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NOCON", "when": "not reached"}]}`

## wording (1)

- **R13** — _tamsin.md Document 1 'Opening'_: Once the right person is on the line, address them as {title} {last_name}.

## other (10)

- **R02** [confidence medium, samples BC] — _openapi.json /get_account_: `get_account` is refused until both security questions are passed; returns products with `type`, `card_last4`, `past_due`, `days_late`, `minimum_payment`, `instalment_amount`.
- **R06** — _tamsin.md Document 1 'Who we ring'_: Calls go to personal customers 1 to 45 days behind on one, two or three products: credit card, personal loan, car loan.
- **R07** — _tamsin.md Document 1 Who we ring_: Dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now` (e.g. `2026-10-14T11:00`); every date is worked out from `now`; `customer_id` goes into every tool call.
- **R08** [confidence low, samples A] — _tamsin.md Document 1 'Who we ring'_: `customer_id` goes into every tool call.
- **R09** — _tamsin.md Document 1 'Who we ring'_: Systems accept anything (a Sunday promise, one pound), so the assistant must enforce the rules itself. Where mail and AHS-5 differ, the Standard prevails.
- **R10** [confidence medium, samples BC] — _tamsin.md Document 1 intro_: Figures (bands, last dates, floors, closure days, hours) are in AHS-5 section 5; where the mail and the Standard differ, the Standard applies.
- **R49** **[not policy]** [confidence low, samples B] — _tamsin.md Document 1 intro_: Campaign review on Friday 9th expected to bring decisions; minutes to follow.
  - deciding quote: "We have a campaign review on Friday the 9th and I expect a few decisions to come out of it, so I will send the minutes on as well."
- **R77** [confidence low, samples C] [verified] — _tamsin.openapi.json /get_account_: `get_account` is refused until both questions are passed; if it fails, close as system failure.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SYSF", "when": "get_account fails"}]}`
- **R79** — _tamsin.md Document 3 item 1_: Go-live is the first dialler run on Wednesday 14 October 2026; the assistant is checked against these minutes from that day.
- **R106** **[not policy]** [confidence medium] — _tamsin.md Document 3 item 7_: AOB: Christmas lunch on Friday 11 December; Treasury dashboard moving to the new BI tool in January. Decides nothing for the calls; no rule for the assistant.
  - deciding quote: "The Christmas lunch is on Friday 11 December."
