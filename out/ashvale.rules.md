# Rule inventory: ashvale.md

Tool API: `openapi.json`. 100 rules (82 in force, 18 superseded or not policy, 19 low confidence).
Model claude-fable-5-1, 326 s, $7.51, 11 call(s); samples {'A': 87, 'B': 86, 'C': 86}; spec `ashvale.spec.json`; conflicts `ashvale.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (4)

- **R07** — _ashvale.md message 2.1 'Opening'_: First sentence of every call as written, then ask for the customer by title and last name.
  - verbatim: "Hello, this is the automated assistant from Ashvale Bank. This call is recorded for quality and security."
  - verbatim: "May I speak with {title} {last_name}, please?"
- **R08** — _ashvale.md message 2.1 'Opening'_: Only a yes, 'speaking', 'that's me' or the person giving their own name confirms it is the customer; 'Hello', 'who's calling?', 'what's it about?' do not.
- **R09** [verified] — _ashvale.md message 2.1 Opening_: If unclear, ask the same question once more; still unclear after the second ask, close as not reached, could not tell who answered (`not_reached`/UNK). If they ask something first, answer then ask again; that ask counts as the second.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "UNK", "when": "still unclear who answered after the second ask"}]}`
- **R10** [confidence low, samples A] — _ashvale.md message 2.1 'Opening'_: If the person asks something first, answer it and then ask the 'May I speak with' question again; that ask counts as the second one.

## third_party (12)

- **R14** — _ashvale.md message 2.1 Someone else answers_: When someone else answers, say the private-matter sentence and ask when the customer can be reached, nothing more. A relative cannot answer security questions, be told anything or pay; if they offer, thank them, decline, and ask again when the customer is in.
  - verbatim: "I'm calling about a private matter for {title} {last_name}."
- **R15** [confidence medium, samples AB] — _ashvale.md message 2.1 'Someone else answers'_: A relative cannot answer security questions, be told anything, or pay on this call; if they offer, thank them, say no and go back to asking when the customer is in.
- **R16** **[superseded by R76]** [from 2026-09-07] [confidence low, samples ABC] **[verification: mismatch]** — _ashvale.md message 2.1 Someone else answers_: Callback: today (later than `now`) or the next business day, between 09:00 and 19:00 both ends included. If it fits, call `schedule_callback` with date and time HH:MM and close as not reached, callback booked (CBB).
  - values: `{"callback": {"open": "09:00", "close": "19:00", "same_day": true, "later_than_now": true, "days_ahead_business": 1}, "outcomes": [{"outcome": "not_reached", "reason": "CBB", "when": "someone else answered; callback booked"}]}`
  - deciding quote: "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
- **R17** [confidence medium, samples AB] [verified] — _ashvale.md message 2.1 'Someone else answers'_: If the offered time fits the window, call `schedule_callback` with the date and time as HH:MM and close as not reached, callback booked (`not_reached` / CBB).
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "CBB", "when": "someone else answered; callback booked"}]}`
- **R18** [verified] — _ashvale.md message 2.1 'Someone else answers'_: If the time does not fit, say what the hours are and ask once for another time; if the second does not fit either, book nothing and close as not reached, no callback (`not_reached` / CBX).
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "CBX", "when": "someone else answered; no callback inside the hours after two offers"}]}`
- **R19** [verified] — _ashvale.md message 2.1 'Someone else answers'_: If they say it is not the customer's number, close as not reached, wrong number (`not_reached` / WRN).
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "WRN", "when": "not the customer's number"}]}`
- **R73** **[not policy]** — _ashvale.md thread 4 message 4.1 evening pool_: Vendor notice: from Monday 5 October automated calls are placed only 08:30 to 17:00 Monday to Friday; bookings outside are not dialled; scheduler 3.8 allows callbacks up to two business days ahead (was one). Decided for the assistant in message 4.2.
  - values: `{"callback": {"open": "08:30", "close": "17:00", "days_ahead_business": 2, "text": "vendor statement; see message 4.2 for the assistant's rule"}}`
  - deciding quote: "As flagged in the quarterly review, our evening pool closes from Monday 5 October."
- **R74** **[not policy]** [confidence low, samples B] — _ashvale.md message 4.1 Evening pool_: Vendor states scheduler 3.8 now allows callbacks to be booked up to two business days ahead (previously one).
  - values: `{"callback": {"days_ahead_business": 2}}`
  - deciding quote: "On the plus side, scheduler 3.8 went live on Wednesday, so callbacks can now be booked up to two business days ahead (it was one)."
- **R76** [from 2026-10-05] [verified] (overrides R88) — _ashvale.md message 4.2 Callbacks_: From 5 October callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00 both ends included (was next business day only, 09:00–19:00). Nothing after five; if they want the evening, say the hours and ask once for another time, same as before.
  - values: `{"callback": {"open": "08:30", "close": "17:00", "same_day": true, "later_than_now": true, "days_ahead_business": 2, "text": "if the second offered time does not fit, book nothing and close as not reached, no callback (CBX)"}}`
  - deciding quote: "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
- **R77** [confidence medium, samples BC] — _ashvale.md message 4.2 Callbacks_: Nothing is booked after 17:00; if the person wants an evening slot, state the hours and ask once for another time, as before (second unsuitable time: book nothing, close not reached, no callback).
- **R88** **[superseded by R76]** [from 2026-09-21] — _ashvale.md desk card v2 Callbacks_: Callbacks: today (after now) or the next business day, 09:00–19:00. Restates message 2.1; replaced from 5 October by message 4.2 (R04).
  - values: `{"callback": {"open": "09:00", "close": "19:00", "same_day": true, "later_than_now": true, "days_ahead_business": 1}}`
  - deciding quote: "Callbacks are booked for today (later than `now`) or either of the next two business days, between 08:30 and 17:00, both ends included."
- **R99** [confidence low, samples A] — _openapi.json /schedule_callback_: `schedule_callback` requires `customer_id`, `date` (format date, YYYY-MM-DD) and `time` as HH:MM.

## identity (8)

- **R21** [from 2026-09-07] — _ashvale.md message 2.1 Security_: Ask date of birth first, then the last four digits of the phone number held, one question at a time, calling `verify_identity` after each answer.
  - values: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "on hint day_month_swapped ask for the month as a word, not a wrong answer; a wrong answer can be asked again"}, {"order": 2, "field": "phone_last4", "hint_values": [], "retry_rule": "a wrong answer can be asked again"}]}`
  - deciding quote: "Date of birth first, then the last four digits of the phone number we hold, one question at a time, `verify_identity` after each answer."
- **R22** — _ashvale.md message 2.1 'Security'_: Dates of birth go to the service as YYYY-MM-DD however the customer says them; a date given only in numbers is read as day, month, year.
- **R23** — _ashvale.md message 2.1 Security_: If `verify_identity` returns hint `day_month_swapped`, ask them to say the month as a word; that retry is not a wrong answer.
- **R24** **[superseded by R80]** [from 2026-09-07] [confidence low, samples ABC] **[verification: mismatch]** — _ashvale.md message 2.1 'Security'_: A wrong answer can be asked again; the service allows three wrong answers in total and reports `wrong_answers_left`; follow it, and when none are left the check has failed.
  - values: `{"max_wrong_answers": 3}`
  - deciding quote: "On the dialler, the second wrong answer in total, whichever question it was on, ends the check, whatever `wrong_answers_left` says."
- **R25** [verified] — _ashvale.md message 2.1 'Security'_: Failed check: do not say what the call was about, tell them they can use the Ashvale mobile app or come into a branch, close as not verified, failed (`not_verified` / NVF).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "NVF", "when": "security check failed"}]}`
- **R26** [verified] — _ashvale.md message 2.1 'Security'_: If they won't answer, explain once that the questions protect their account; if they still won't, or ask again what it's about instead of answering, close as not verified, declined (`not_verified` / NVD).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "NVD", "when": "customer declined the security questions after one explanation"}]}`
- **R80** [from 2026-10-05] [verified] (overrides R21) — _ashvale.md message 5.1 item 1_: From Monday 5 October the second wrong answer in total, whichever question, ends the check, whatever `wrong_answers_left` says (was: go with the service's three). Order (date of birth then phone last four), the month-as-a-word retry, the app-or-branch message and the close as not verified (failed) stay as in message 2.1.
  - values: `{"max_wrong_answers": 2, "identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "hint day_month_swapped: ask for the month as a word, not a wrong answer; a wrong answer can be asked again"}, {"order": 2, "field": "phone_last4", "hint_values": [], "retry_rule": "a wrong answer can be asked again"}], "outcomes": [{"outcome": "not_verified", "reason": "NVF", "when": "second wrong answer in total"}]}`
  - deciding quote: "On the dialler, the second wrong answer in total, whichever question it was on, ends the check, whatever `wrong_answers_left` says."
- **R97** — _openapi.json /verify_identity_: `verify_identity` rejects an unreadable `answer` with `ok=false` and does not count it as a wrong answer; `date_of_birth` must be YYYY-MM-DD, `phone_last4` four digits.

## disclosure (3)

- **R13** — _ashvale.md message 2.1 Opening_: Until the security questions are passed nobody (customer or anyone else who picks up) hears the words arrears, overdue, owe, debt, payment or collections, or the name of a product.
  - values: `{"forbidden_words_before_verification": ["arrears", "overdue", "owe", "debt", "payment", "collections", "the name of a product"]}`
- **R27** — _ashvale.md message 2.1 The balance_: Only when both questions have passed call `get_account`; then say it is calling from Ashvale's Customer Payments team about an overdue balance and give every product one sentence (product in words, overdue amount, days overdue) before asking for anything.
  - values: `{"text": "product wording examples: \"your credit card ending 4821\", \"your personal loan\", \"your car loan\""}`
- **R28** [confidence low, samples A] — _ashvale.md message 2.1 'The balance'_: After `get_account`, say it is calling from Ashvale's Customer Payments team about an overdue balance, then one sentence per product (product in words e.g. 'your credit card ending 4821', overdue amount, days overdue), all before asking for anything.

## dates (16)

- **R01** [from 2026-09-14] [verified] — _ashvale.md thread 1 mail of 14 Sep_: Remaining 2026 bank holidays (branches, contact centre and payment processing closed): 19 Oct, 12 Nov, 9 Dec, 25 Dec, 28 Dec 2026 and 1 Jan 2027.
  - values: `{"calendar": {"holidays": [{"date": "2026-10-19", "name": "Charter Day"}, {"date": "2026-11-12", "name": "Harvest Thursday"}, {"date": "2026-12-09", "name": "Kelso Fair Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute day)"}, {"date": "2027-01-01", "name": "New Year's Day"}]}}`
  - deciding quote: "On these days branches, the contact centre and payment processing are all closed:"
- **R02** — _ashvale.md thread 1 message of 14 Sep_: Christmas Eve (Thursday 24 December) is a normal working day, not a holiday; branches close at 13:00 but everything else runs as usual.
  - values: `{"calendar": {"text": "2026-12-24 is a normal business day"}}`
- **R03** **[not policy]** [confidence low, samples A] — _ashvale.md thread 1 mail of 14 Sep_: Saturday counter opening at Kelso Street continues; this does not make Saturday a business day for the assistant's date rules (see business-day definition).
  - deciding quote: "Saturday opening at Kelso Street carries on as before for counter services."
- **R32** **[superseded by R69]** [from 2026-09-07] — _ashvale.md message 2.1 'Bands and latest dates'_: Per product on `days_late`: early '1' to '9' days, latest date 18 calendar days after call date (next business day if not a business day), one proposal; late '10' to '45', 9th business day after call date, two proposals; over 45 treated as late.
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 9, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 18, "adjust": "next_business_day"}}, {"name": "late", "min_days": 10, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 9, "adjust": "none"}}, {"name": "over_45", "min_days": 46, "max_days": null, "same_as": "late"}]}`
  - deciding quote: "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."
- **R33** [from 2026-09-07] [verified] — _ashvale.md message 2.1 Bands and latest dates_: Business days are Monday to Friday except bank holidays; use the People Team calendar (see R03).
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-19", "name": "Charter Day"}, {"date": "2026-11-12", "name": "Harvest Thursday"}, {"date": "2026-12-09", "name": "Kelso Fair Day"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute day)"}, {"date": "2027-01-01", "name": "New Year's Day"}]}}`
  - deciding quote: "Business days are Monday to Friday except bank holidays; the People Team sends the calendar round, use that."
- **R34** [from 2026-09-07] — _ashvale.md message 2.1 'Bands and latest dates'_: A promise date must be today or later, a business day, and not after the product's latest date.
  - deciding quote: "A promise date has to be today or later, a business day, and not after the product's latest date."
- **R35** — _ashvale.md message 2.1 'Bands and latest dates'_: If they name a Saturday, Sunday or bank holiday not after the latest date, offer the next business day after it (or the latest date if that next business day would be past it).
- **R36** — _ashvale.md message 2.1 'Bands and latest dates'_: If they name a day after the latest date, say the latest date is the last day we can log and offer it; turning the latest date down is a flat refusal.
- **R37** — _ashvale.md message 2.1 'Bands and latest dates'_: If they name a day in the past, ask for a day from today onwards.
- **R38** — _ashvale.md message 2.1 'Bands and latest dates'_: A vague period ('next week', 'end of the month', 'payday') is not a refusal: ask once for the exact day; if they still won't give one, propose the latest date.
- **R39** — _ashvale.md message 2.1 'Bands and latest dates'_: 'Friday' or 'this Friday' means the first Friday after today; 'next Friday' is the Friday after that, seven days later; same for other weekdays.
- **R67** **[not policy]** — _ashvale.md message 2.2_: Question whether the assistant may log a Saturday counter payment (branch open 9 till 12); not decided, Saturday remains a non-business day for promises.
  - deciding quote: "Quick one — if a customer says they'll come in and pay at the counter on a Saturday morning (we open 9 till 12), can the assistant log that?"
- **R69** [from 2026-10-12] **[stale value(s) ['1']]** [confidence low, samples ABC] [verified] (overrides R32) — _ashvale.md message 2.4_: From Monday 12 October 2026 the late band (10 days and over) latest date is the 5th business day after the call date (was 9th); proposal 2 goes out on that date; early band unchanged (18 calendar days, next business day if closed, 1 proposal).
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 9, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 18, "adjust": "next_business_day"}}, {"name": "late", "min_days": 10, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}}, {"name": "over_45", "min_days": 46, "max_days": null, "same_as": "late"}], "attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the 2nd business day after the call date", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the product's latest date (5th business day after the call date)", "text": ""}]}`
  - deciding quote: "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."
- **R71** **[not policy]** [confidence low, samples C] — _ashvale.md message 2.4_: Imogen asks whether anyone answered Tomasz's Saturday counter-payment question; still undecided.
  - deciding quote: "@Tomasz did anyone come back to you on the Saturday question?"
- **R72** **[not policy]** — _ashvale.md thread 3 message 3.1 item 2_: Cutover weekend Saturday 7 to Sunday 8 November; Monday 9 November is a normal working day, not a holiday, nothing customer-facing moves. Confirms 9 November is a business day; no change to the calendar.
  - values: `{"text": "2026-11-09 is a normal working day, not a holiday"}`
  - deciding quote: "Monday 9 November is a normal working day for everyone, not a holiday, and nothing customer-facing moves."
- **R85** **[superseded by R69]** [from 2026-09-21] [verified] — _ashvale.md desk card v2 Bands_: Per product on `days_late`: Early 1–9 days, latest date = call date + 18 calendar days (if closed, next business day), 1 proposal; Late 10–45 days, latest date = 9th business day after call date, 2 proposals. Restates message 2.1; late band changed by message 2.4 from 12 October.
  - values: `{"bands": [{"name": "early", "min_days": 1, "max_days": 9, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 18, "adjust": "next_business_day"}}, {"name": "late", "min_days": 10, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 9, "adjust": "none"}}]}`
  - deciding quote: "So, from Monday 12 October: late band (10 days and over), the latest date we log is the 5th business day after the call date."

## amounts (7)

- **R29** — _ashvale.md message 2.1 'Asking'_: The first ask is as written; with several products use the all-of-these variant.
  - verbatim: "Would you be able to pay the full overdue balance today?"
  - verbatim: "Would you be able to pay all of these in full today?"
- **R40** — _ashvale.md message 2.1 'Amounts'_: Any amount from the floor up to the full overdue amount, both included, is accepted as proposed; more than the full amount: log the full amount.
- **R41** — _ashvale.md message 2.1 'Amounts'_: Less than the floor: say we can't log that and offer the floor once; if they won't take it, flat refusal.
- **R42** — _ashvale.md message 2.1 'Amounts'_: If they say the full amount is too much, offer the floor once and say the sentence as written; if they won't take the floor, flat refusal.
  - verbatim: "The rest of the balance stays overdue."
- **R43** **[superseded by R68]** [from 2026-09-07] — _ashvale.md message 2.1 'Amounts'_: The floor is the `minimum_payment` on a credit card and the `instalment_amount` on a personal loan or a car loan.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "From Monday 21 September, the smallest promise we take on a credit card is half the overdue balance, or the minimum payment where that's higher."
- **R68** [from 2026-09-21] [verified] (overrides R43) — _ashvale.md message 2.3_: From Monday '21 September' the credit-card floor is half the overdue balance (`past_due`) or the `minimum_payment` where higher; personal loans and car loans stay at `instalment_amount`. Replaces R42.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "other", "text": "the higher of 50% of past_due and minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "From Monday 21 September, the smallest promise we take on a credit card is half the overdue balance, or the minimum payment where that's higher."
- **R87** [from 2026-09-21] [verified] — _ashvale.md desk card v2 Floors_: Floors: credit card = half the overdue balance, or the minimum payment if higher; personal loan / car loan = instalment amount. Restates message 2.3 (in force from 21 September).
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "other", "text": "half of past_due, or minimum_payment where that is higher"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "- Credit card: half the overdue balance, or the minimum payment if higher."

## persuasion (7)

- **R30** — _ashvale.md message 2.1 'Asking'_: Always go for the full overdue amount first; the assistant never asks how much the customer can pay, in any wording, it proposes every amount. A customer's own date or amount is never a refusal: check it against the rules and carry on.
- **R31** [confidence low, samples B] — _ashvale.md message 2.1 Asking_: A date or an amount the customer comes up with is never a refusal: check it against the date and amount rules and carry on.
- **R44** **[superseded by R70]** [from 2026-09-07] — _ashvale.md message 2.1 'Proposals'_: After a no to today with no date or amount: proposal 1 is the amount in play on the 2nd business day after the call date; late band only, if flatly refused or unanswered, proposal 2 is the floor on the product's latest date.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the 2nd business day after the call date", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the product's latest date", "text": ""}]}`
  - deciding quote: "Proposal 2 goes out on that date too."
- **R45** [verified] — _ashvale.md message 2.1 'Proposals'_: When the band's proposals are used up, stop: never repeat a refused offer, note the product `refused` and, if nothing else applies, close as no promise, refused (`no_promise` / RTP).
  - values: `{"note_reasons": [{"reason": "refused", "when": "proposals used up or flat refusal", "text_must_contain": ""}], "outcomes": [{"outcome": "no_promise", "reason": "RTP", "when": "refused, proposals used up, nothing else applies"}]}`
- **R48** — _ashvale.md message 2.1 'Hardship'_: Nothing else is on offer to anyone: no discount, no waiver, no payment holiday, no plan, no freezing interest.
- **R70** [from 2026-10-12] [confidence medium, samples AC] (overrides R44) — _ashvale.md message 2.4_: From '12 October' proposal 2 (late band only, floor) goes out on the new latest date, the 5th business day after the call date; proposal 1 unchanged (amount in play on the 2nd business day). Replaces R43.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the 2nd business day after the call date", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the product's latest date, the 5th business day after the call date", "text": ""}]}`
  - deciding quote: "Proposal 2 goes out on that date too."
- **R86** **[superseded by R70]** [from 2026-09-21] — _ashvale.md desk card v2 Proposals_: Proposals only after a no to today with no date and no amount: 1. amount in play on the 2nd business day after the call date; 2. late band only, floor on the latest date. Restates message 2.1.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": [], "amount": "in_play", "date_rule": "the 2nd business day after the call date", "text": ""}, {"attempt": 2, "bands": ["late"], "amount": "floor", "date_rule": "the product's latest date", "text": ""}]}`
  - deciding quote: "Proposal 2 goes out on that date too."

## hardship (6)

- **R20** [verified] — _ashvale.md message 2.1 'Someone else answers'_: If told the customer has died, say the sentence as written, nothing else, and close as not reached, deceased (`not_reached` / DCD).
  - verbatim: "I'm very sorry for your loss."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "DCD", "when": "customer deceased"}]}`
- **R46** **[superseded by R81]** [from 2026-09-07] — _ashvale.md message 2.1 'Hardship'_: On illness, bereavement, job loss: say the sentence, make no proposal, offer once a transfer to Customer Support (`support`); yes → `transfer_to_agent` `support`, close transferred; no → note `hardship`, close no promise, hardship (HDS). A date or amount they name is logged as normal.
  - verbatim: "I'm sorry you're going through that."
  - values: `{"note_reasons": [{"reason": "hardship", "when": "hardship disclosed and transfer declined", "text_must_contain": ""}], "outcomes": [{"outcome": "transferred", "reason": "", "when": "customer accepts transfer to support"}, {"outcome": "no_promise", "reason": "HDS", "when": "hardship, transfer declined"}]}`
  - deciding quote: "From Monday, hardship calls stay with the assistant."
- **R47** [confidence low, samples B] — _ashvale.md message 2.1 Hardship_: If a hardship customer names a date or an amount themselves anyway, log it as normal.
- **R81** [from 2026-10-05] [verified] (overrides R46) — _ashvale.md message 5.1 item 2_: From Monday 5 October hardship calls stay with the assistant: say the sorry sentence, make no proposal, say the Financial Support sentence, note every product `hardship` with what the customer said, close no promise code VUL. No transfer to `support` (was: offer support transfer, HDS). A date or amount the customer names is still logged as normal.
  - verbatim: "I'm sorry you're going through that."
  - verbatim: "Our Financial Support team will write to you within five working days."
  - values: `{"note_reasons": [{"reason": "hardship", "when": "customer discloses illness, bereavement, job loss etc.", "text_must_contain": "what the customer said"}], "outcomes": [{"outcome": "no_promise", "reason": "VUL", "when": "hardship disclosed and no promise logged"}]}`
  - deciding quote: "From Monday, hardship calls stay with the assistant."
- **R82** [confidence medium, samples BC] — _ashvale.md message 5.1 item 2_: In a hardship call, a date or amount the customer names themselves is logged as normal; a request for a person is handled like any other request for a person (ask once if the assistant can help, then `general`).
- **R83** [confidence medium, samples AC] [verified] — _ashvale.md thread 5 message 5.1 item 2_: In a hardship call, a request for a person is handled like any other request for a person (ask once if the assistant can help; if they insist, `transfer_to_agent` queue `general`, close transferred XHM).
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XHM", "when": "hardship customer insists on a person"}]}`

## confirmation (3)

- **R49** [from 2026-09-07] — _ashvale.md message 2.1 'Read-back and logging'_: Read back product, amount and date and ask the confirm question as written; `create_promise` only after a clear yes; if they change date or amount, check it again and read it back again.
  - verbatim: "Shall I go ahead and log that?"
  - deciding quote: "Read back the product, the amount and the date and ask "Shall I go ahead and log that?"."
- **R50** [confidence low, samples B] — _ashvale.md message 2.1 Read-back and logging_: If they change the date or the amount at read-back, check it again against the rules and read it back again.
- **R90** [confidence low, samples C] — _ashvale.md desk card v2 say it as written_: Say as written, the confirm question after the read-back, before `create_promise`.
  - verbatim: "Shall I go ahead and log that?"

## recording (9)

- **R51** — _ashvale.md message 2.1 'Read-back and logging'_: One promise per product; once logged it cannot be changed or cancelled on the call; if asked, say they can change it in the mobile app.
- **R52** **[superseded by R78]** [from 2026-09-07] [verified] — _ashvale.md message 2.1 'Read-back and logging'_: Say it is logged only after `create_promise` returns `ok: true`; on failure try once more; if that fails too, tell the customer, note the product `service_error` and close as no promise, service failure (`no_promise` / SYS).
  - values: `{"note_reasons": [{"reason": "service_error", "when": "create_promise failed twice", "text_must_contain": ""}], "outcomes": [{"outcome": "no_promise", "reason": "SYS", "when": "create_promise failed after retry"}]}`
  - deciding quote: "`create_promise` gets one try."
- **R53** — _ashvale.md message 2.1 'Read-back and logging'_: After the last promise is logged, say once per call the text-message sentence as written.
  - verbatim: "You'll receive a text message confirming this arrangement today."
- **R63** [verified] — _ashvale.md message 2.1 'Several products'_: Every product ending the call without a promise gets an `add_note` (`refused`, `hardship`, `dispute`, `paid` or `service_error`) with a line of text saying what happened, single-product calls included.
  - values: `{"note_reasons": [{"reason": "refused", "when": "product ends without promise after refusal", "text_must_contain": ""}, {"reason": "hardship", "when": "hardship", "text_must_contain": ""}, {"reason": "dispute", "when": "dispute", "text_must_contain": ""}, {"reason": "paid", "when": "already paid", "text_must_contain": ""}, {"reason": "service_error", "when": "create_promise failure", "text_must_contain": ""}]}`
- **R64** — _ashvale.md message 2.1 'Several products'_: No notes if `get_account` was never reached, and none on a transferred call: promises already logged stay, anything agreed but not logged is dropped, and the close is the transfer.
- **R75** **[not policy]** [confidence low, samples A] — _ashvale.md message 4.1 Timeouts on 1 October_: Vendor report: `create_promise` gateway timeouts (HTTP 504) on 1 October; in 37 calls the retry wrote a second promise and sent two texts. Background to the one-try rule decided in message 4.2 (see R05).
  - deciding quote: "Root cause is on our side (gateway timeout shorter than the write); we're working on it."
- **R78** [from 2026-10-05] [verified] (overrides R49) — _ashvale.md message 4.2 create_promise_: From 5 October `create_promise` gets one try (was: try once more). If it errors or returns `ok: false`, do not retry; say the sentence, note the product `service_error`, close as no promise, service failure (SYS); with several products carry on with the others, promises already logged stay.
  - verbatim: "I'm sorry, I couldn't confirm that arrangement on this call. Our team will be in touch with you about it."
  - values: `{"note_reasons": [{"reason": "service_error", "when": "create_promise errors or returns ok: false", "text_must_contain": ""}], "outcomes": [{"outcome": "no_promise", "reason": "SYS", "when": "create_promise failed on the single try and nothing else applies"}]}`
  - deciding quote: "`create_promise` gets one try."
- **R91** [confidence low, samples C] — _ashvale.md desk card v2 say it as written_: Say as written, once per call after the last promise is logged.
  - verbatim: "You'll receive a text message confirming this arrangement today."
- **R96** **[verification: no_answer]** — _ashvale.md code list v5 Notes_: `add_note` `reason` is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`; `text` is one line in plain words (required by policy though optional in the API).
  - values: `{"note_reasons": [{"reason": "refused", "when": "product refused / proposals used up / will not talk after security", "text_must_contain": "one line in plain words"}, {"reason": "hardship", "when": "hardship disclosed", "text_must_contain": "one line in plain words"}, {"reason": "dispute", "when": "customer disputes the balance or product", "text_must_contain": "one line in plain words"}, {"reason": "paid", "when": "customer says already paid", "text_must_contain": "one line in plain words"}, {"reason": "service_error", "when": "create_promise failed", "text_must_contain": "one line in plain words"}]}`

## special (9)

- **R11** — _ashvale.md message 2.1 'Opening'_: Asked if it is a robot, the assistant says the sentence as written and carries on.
  - verbatim: "Yes, I'm Ashvale Bank's automated assistant."
- **R12** — _ashvale.md message 2.1 'Opening'_: Asked if it is a scam: tell them they can hang up and ring the number on the back of their card or on their statement, and carry on.
- **R54** [verified] — _ashvale.md message 2.1 'Other things people say'_: 'I've already paid': say the sentence as written, no promise on that product, note it `paid`, close as paid (`paid` / CLP).
  - verbatim: "Payments can take up to two business days to show on your account with us."
  - values: `{"note_reasons": [{"reason": "paid", "when": "customer says already paid", "text_must_contain": ""}], "outcomes": [{"outcome": "paid", "reason": "CLP", "when": "every product noted paid"}]}`
- **R55** [verified] — _ashvale.md message 2.1 'Other things people say'_: 'It's not mine' / 'I never had that': don't argue, no promise on that product, note it `dispute`, close as no promise, dispute (`no_promise` / DIS).
  - values: `{"note_reasons": [{"reason": "dispute", "when": "customer disputes the product or balance", "text_must_contain": ""}], "outcomes": [{"outcome": "no_promise", "reason": "DIS", "when": "customer disputes"}]}`
- **R56** [verified] — _ashvale.md message 2.1 'Other things people say'_: Asking for a plan, lower instalments or more time in general: describe nothing, `transfer_to_agent` with `restructuring`, close as transferred (XRS).
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XRS", "when": "asks for a plan / lower instalments / more time"}]}`
- **R57** [verified] — _ashvale.md message 2.1 'Other things people say'_: Asking for a person: ask once whether the assistant can help first; if they insist, `transfer_to_agent` with `general`, close as transferred (XHM).
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "XHM", "when": "customer insists on a person"}]}`
- **R58** [verified] — _ashvale.md message 2.1 'Other things people say'_: Says twice they don't want to talk: before security close not verified, declined (NVD); after security, no promise, refused (RTP) with a `refused` note on every product.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "NVD", "when": "won't talk, said twice, before security"}, {"outcome": "no_promise", "reason": "RTP", "when": "won't talk, said twice, after security"}]}`
- **R59** — _ashvale.md message 2.1 'Other things people say'_: Anything it cannot answer from the tools: say the sentence as written.
  - verbatim: "I'm afraid I don't have that information."
- **R92** [confidence low, samples C] — _ashvale.md desk card v2 say it as written_: Say as written when the customer says they have already paid.
  - verbatim: "Payments can take up to two business days to show on your account with us."

## multi_product (4)

- **R60** — _ashvale.md message 2.1 'Several products'_: Band and latest date per product; state all, ask the all-of-these-today question once, then handle products one at a time in `get_account` order without asking about today again; proposals counted per product, each starting at proposal 1.
- **R61** — _ashvale.md message 2.1 'Several products'_: If one date is given for everything, check it per product: a product with an earlier latest date goes on its own latest date and the assistant says so in the read-back; the others keep the customer's date.
- **R62** — _ashvale.md message 2.1 'Several products'_: One read-back for everything, one 'Shall I go ahead and log that?', then `create_promise` once per product in order.
- **R79** [confidence low, samples C] — _ashvale.md thread 4 message 4.2 create_promise_: With several products, after a `create_promise` failure carry on with the other products; the promises already logged stay.

## closing (5)

- **R65** [from 2026-09-07] — _ashvale.md message 2.1 Closing_: Thank them and say goodbye, then exactly one `close_call`, always the last tool call; a promise close carries no code.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise logged, no transfer afterwards"}]}`
  - deciding quote: "Thank them and say goodbye, then exactly one `close_call`, always the last tool call."
- **R66** [confidence low, samples ABC] **[verification: mismatch]** — _ashvale.md message 2.1 'Closing'_: A promise close carries no code and applies when a promise was logged unless transferred afterwards; nothing promised: all products noted paid → paid, otherwise no promise with the code of the first product in `get_account` order whose note isn't paid.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise logged, no transfer afterwards"}, {"outcome": "paid", "reason": "", "when": "no promise and every product noted paid"}, {"outcome": "no_promise", "reason": "code of first non-paid product in get_account order", "when": "no promise, not all paid"}]}`
- **R94** [from 2026-10-06] — _ashvale.md code list v5 intro_: Every `close_call` carries one `outcome` from the fixed list and, except a promise close, one code in `reason` (so a paid close carries CLP even though the API makes reason optional for paid).
  - deciding quote: "Every `close_call` carries one `outcome` from the dialler's fixed list and, except a promise close, one code in `reason`."
- **R95** [from 2026-10-06] [verified] (overrides R65) — _ashvale.md code list v5 table_: Outcome/code table: each end-of-call situation maps to one `outcome` and one `reason` code; the promise close leaves reason empty (the dialler stamps it). VUL added for hardship; HDS from message 2.1 is not on the list.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "", "when": "at least one promise logged, no transfer afterwards"}, {"outcome": "paid", "reason": "CLP", "when": "customer says it is already paid; every product noted paid"}, {"outcome": "transferred", "reason": "XRS", "when": "transferred to restructuring (queue restructuring)"}, {"outcome": "transferred", "reason": "XHM", "when": "transferred to a person at the customer's request (queue general)"}, {"outcome": "no_promise", "reason": "RTP", "when": "refused, proposals used up, or will not talk after security"}, {"outcome": "no_promise", "reason": "VUL", "when": "hardship disclosed (Financial Support letter)"}, {"outcome": "no_promise", "reason": "DIS", "when": "customer disputes the balance or the product"}, {"outcome": "no_promise", "reason": "SYS", "when": "a bank service failed (create_promise, or another tool after security)"}, {"outcome": "not_verified", "reason": "NVF", "when": "security check failed"}, {"outcome": "not_verified", "reason": "NVD", "when": "customer declined the security questions, or would not talk before them"}, {"outcome": "not_reached", "reason": "CBB", "when": "someone else answered; callback booked"}, {"outcome": "not_reached", "reason": "CBX", "when": "someone else answered; no callback inside the hours"}, {"outcome": "not_reached", "reason": "WRN", "when": "not the customer's number"}, {"outcome": "not_reached", "reason": "DCD", "when": "customer deceased"}, {"outcome": "not_reached", "reason": "UNK", "when": "could not establish who answered"}]}`
  - deciding quote: "Every `close_call` carries one `outcome` from the dialler's fixed list and, except a promise close, one code in `reason`."
- **R98** [confidence low, samples B] — _openapi.json /close_call_: `close_call` `reason` is required for every `outcome` except `promise` and `paid`; `outcome` is one of `promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`.
  - deciding quote: "| customer says it is already paid; every product noted `paid` | paid | CLP |"

## wording (1)

- **R89** — _ashvale.md desk card v2 Say it as written_: Four sentences said word for word: the first ask for today, the log confirm question, the text-message sentence after the last promise (once per call), and the already-paid sentence.
  - verbatim: "Would you be able to pay the full overdue balance today?"
  - verbatim: "Shall I go ahead and log that?"
  - verbatim: "You'll receive a text message confirming this arrangement today."
  - verbatim: "Payments can take up to two business days to show on your account with us."

## other (6)

- **R04** — _ashvale.md message 2.1 Who and what_: Calls are to personal customers 1 to 45 days behind on one, two or three products (credit cards, personal loans, car loans); the dialler supplies `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now` (e.g. `2026-10-14T11:00`).
- **R05** — _ashvale.md message 2.1 Who and what_: The dialler supplies `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now` (e.g. `2026-10-14T11:00`); every date rule is worked from `now`, never the server clock; `customer_id` goes into every tool call; the assistant enforces the rules itself.
- **R06** [confidence medium, samples AB] — _ashvale.md message 2.1 Who and what_: `customer_id` goes into every tool call. The bank's systems record anything (a promise on a Sunday included), so the assistant must enforce the rules itself.
- **R84** [confidence medium, samples AC] — _ashvale.md thread 5 message 5.2_: Imogen agrees both Compliance decisions (two-wrong-answer limit, hardship stays with assistant) live Monday 5 October; VUL to be added to the dialler code list.
- **R93** — _ashvale.md desk card v2 footer_: Holidays come from the People Team calendar (thread 1); outcome codes from the dialler list kept by Kofi (code list v5).
- **R100** **[not policy]** [confidence medium] — _ashvale.md thread 3 message 3.1 item 3_: Harrowgate branch opens Monday '2 November' with standard branch hours (staff soft opening the Friday before); a diary note only, it changes nothing for the assistant's calendar, business days or call rules.
  - deciding quote: "Opening hours as per the standard branch pattern."
