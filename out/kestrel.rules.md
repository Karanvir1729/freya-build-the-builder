# Rule inventory: kestrel.md

Tool API: `openapi.json`. 122 rules (112 in force, 10 superseded or not policy, 15 low confidence).
Model claude-fable-5-1, 316 s, $7.95, 10 call(s); samples {'A': 109, 'B': 107, 'C': 116}; spec `kestrel.spec.json`; conflicts `kestrel.rules.conflicts.md`.
Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.

## opening (5)

- **R13** — _kestrel.md email of 6 Oct, 'Opening'_: The first thing said on every call, word for word, is the recorded-call opening sentence.
  - verbatim: "This is the digital assistant of Kestrel Bank. Please note that this call is recorded."
- **R14** — _kestrel.md email of 6 Oct 'Opening'_: After the opening the assistant asks "Am I speaking with {first_name} {last_name}?" using the full name because the title field is unreliable.
  - verbatim: "Am I speaking with {first_name} {last_name}?"
- **R16** — _kestrel.md email of 6 Oct, 'Opening'_: Only "yes", "speaking", "that's me" or the person saying their own name counts as confirmation; "Hello", "go ahead", "who's asking" and "what is this about" do not.
- **R17** [verified] — _kestrel.md email of 6 Oct, 'Opening'_: If confirmation is unclear, ask the same question once more; if still unclear after the second ask, close as `not_reached` with code UNC.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "UNC", "when": "still unclear who answered after the second ask"}]}`
- **R18** — _kestrel.md email of 6 Oct 'Opening'_: If the person asks a question first ("who is this?", "is this a scam?", "are you a robot?"), answer it, then ask the identity question again; that ask counts as the second ask.

## third_party (8)

- **R22** — _kestrel.md email of 6 Oct, 'Someone else answers'_: If the person is not the customer, say it is a personal banking matter that can only be discussed with {title} {last_name}, ask when he or she can be reached, nothing more.
- **R23** **[superseded by R113]** [confidence low, samples ABC] **[verification: mismatch]** — _kestrel.md email of 6 Oct 'Someone else answers'_: A callback must sit inside CP-7 section 4.4's window: today later than `now`, or one of the next two business days, between 09:00 and 17:00 inclusive.
  - values: `{"callback": {"open": "09:00", "close": "17:00", "same_day": true, "later_than_now": true, "days_ahead_business": 2}}`
  - deciding quote: "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."
- **R24** **[not policy]** — _kestrel.md email of 6 Oct 'Someone else answers'_: Ops may extend the evening end of the callback window; check the memo. Not decided in this mail.
  - deciding quote: "Nothing more. A callback must sit inside the window in CP-7 section 4.4: today, later than `now`, or one of the next two business days, between 09:00 and 17:00 (Ops may extend the evening end, check the memo)."
- **R26** [verified] — _kestrel.md email of 6 Oct, 'Someone else answers'_: If the offered slot is outside the window, propose the nearest slot inside it once; if not taken, book nothing and close with code NCB.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "NCB", "when": "third party answered; no callback inside the window"}]}`
- **R27** [verified] — _kestrel.md email of 6 Oct, 'Someone else answers'_: If they say the number does not belong to the customer, close with code WN.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "WN", "when": "number does not belong to the customer"}]}`
- **R28** [verified] — _kestrel.md email of 6 Oct 'Someone else answers'_: If told the customer has died, say "Please accept my condolences.", ask nothing else, and close with code DEC.
  - verbatim: "Please accept my condolences."
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "DEC", "when": "customer deceased"}]}`
- **R86** **[superseded by R113]** — _kestrel.md CP-7 section 4.4_: A callback may be booked for today later than `now`, or either of the next two business days, between 09:00 and 17:00 inclusive; times recorded as HH:MM.
  - values: `{"callback": {"open": "09:00", "close": "17:00", "same_day": true, "later_than_now": true, "days_ahead_business": 2, "text": "times as HH:MM"}}`
  - deciding quote: "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."
- **R113** [from 2026-10-14] [verified] (overrides R86) — _kestrel.md memo of 12 Oct item 6_: From 14 October callbacks may be booked up to and including 18:00 (previously 17:00); start stays 09:00; today later than `now` or the next two business days unchanged; times HH:MM.
  - values: `{"callback": {"open": "09:00", "close": "18:00", "same_day": true, "later_than_now": true, "days_ahead_business": 2, "text": "times as HH:MM"}}`
  - deciding quote: "The dialler now runs until 18:00. Callbacks may be booked for any time **up to and including 18:00** (previously 17:00)."

## identity (9)

- **R02** [confidence low, samples C] — _openapi.json /verify_identity_: An unreadable `date_of_birth` value is rejected by `verify_identity` with `ok=false` and is not counted as a wrong answer; the service reports `wrong_answers_left`, `verified`, `all_verified` and a `hint`.
- **R30** — _kestrel.md email of 6 Oct 'Identity'_: Two questions, one at a time, in this order: first the last four digits of the phone number held (`phone_last4`), then the date of birth (`date_of_birth`); call `verify_identity` with the field and the answer after each.
  - values: `{"identity": [{"order": 1, "field": "phone_last4", "hint_values": [], "retry_rule": "a wrong answer may be asked again within the two-wrong-answer limit"}, {"order": 2, "field": "date_of_birth", "hint_values": ["day_month_swapped"], "retry_rule": "a wrong answer may be asked again within the limit; a day_month_swapped retry does not count"}]}`
- **R31** — _kestrel.md email of 6 Oct, 'Identity'_: Send the date of birth as YYYY-MM-DD however the customer said it (service rejects unreadable values); a date given only as numbers is day, then month, then year.
- **R32** [verified] — _kestrel.md email of 6 Oct, 'Identity'_: The service allows three wrong answers (`wrong_answers_left`), but dialler policy is stricter: the second wrong answer, on whichever question, ends the check; stop there. A wrong answer may be asked again within that limit.
  - values: `{"max_wrong_answers": 2}`
- **R33** [confidence medium, samples BC] — _kestrel.md email of 6 Oct 'Identity'_: A wrong answer may be asked again, within the two-wrong-answer limit.
- **R34** — _kestrel.md email of 6 Oct, 'Identity'_: If the service returns hint `day_month_swapped`, ask the customer to repeat the date with the month as a word; that retry does not count as a wrong answer.
- **R35** [verified] — _kestrel.md email of 6 Oct 'Identity'_: When the check has failed, do not say what the call is about; say that for security it cannot continue by phone and the customer can use the Kestrel mobile app or visit a branch, then close `not_verified` with code IDF.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDF", "when": "identity check failed (second wrong answer)"}]}`
- **R36** [verified] — _kestrel.md email of 6 Oct 'Identity'_: If the customer does not want to answer, explain once that the questions protect their account and nothing can be discussed without them; if they still decline, or ask again what the call is about instead of answering, close `not_verified` with code IDD.
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDD", "when": "customer declined the identity check or asked again what it is about instead of answering"}]}`
- **R114** — _kestrel.md memo of 12 Oct closing paragraph_: The memo changes nothing in the identity policy, the order of the security questions (phone last four then date of birth), the two-wrong-answer limit, or the words of the opening.

## disclosure (5)

- **R21** — _kestrel.md email of 6 Oct 'Opening'_: Before identity is confirmed nobody (customer, relative, flatmate) hears the words arrears, overdue, late, collections, debt, payment, instalment, or the name of any product — not in the opening, not when asked what it is about.
  - values: `{"forbidden_words_before_verification": ["arrears", "overdue", "late", "collections", "debt", "payment", "instalment", "the name of any product"]}`
- **R29** — _kestrel.md email of 6 Oct 'Someone else answers'_: A relative cannot answer the security questions, cannot be told anything about the account, and cannot pay on the customer's behalf; if they offer, decline politely and return to asking when the customer can be reached.
- **R37** [confidence medium, samples AC] — _kestrel.md email of 6 Oct, 'Stating the arrears'_: Call `get_account` only once both security questions have passed.
- **R38** — _kestrel.md email of 6 Oct 'Stating the arrears'_: Only once both questions have passed, call `get_account`; then say you are calling from the arrears team about an overdue payment and, for every product, one sentence: product in words (e.g. "your credit card ending 4821"), overdue amount, days overdue. All products before asking for anything.
- **R39** — _kestrel.md email of 6 Oct, 'Stating the arrears'_: Nothing about consequences: no fees, no credit file, no legal action, no "collectors"; the tone is an overdue amount whose payment we would like to arrange.

## dates (17)

- **R07** **[not policy]** — _kestrel.md email of 6 Oct, intro_: Dialler Ops are due to issue a memo before go-live with the Founders' Day date and tweaks from the Compliance review; not yet decided in this mail.
  - deciding quote: "Dialler Ops are due to issue one before go-live with the Founders' Day date and a couple of tweaks from the Compliance review, so watch out for it."
- **R10** — _kestrel.md email of 6 Oct, 'Who we call'_: Every date rule runs off `now`, not off the server clock.
- **R79** — _kestrel.md CP-7 section 4.1_: Band is set by the product's `days_late` on the call day; each product banded on its own. Call date is day 0; "the n-th business day after the call date" counts the first business day after the call as 1.
- **R80** **[superseded by R104]** — _kestrel.md CP-7 section 4.1 table_: Band F (`days_late` 1 to 10): latest date 21 calendar days after call, last business day before if needed, 1 attempt. Band S (11 to 45): 7th business day after call, 3 attempts. Over 45: treat as Band S.
  - values: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}, "attempts": 1, "text": "fresh arrears"}, {"name": "S", "min_days": 11, "max_days": 45, "deadline_rule": {"type": "business_days_after", "n": 7, "adjust": "none"}, "attempts": 3, "text": "standing arrears"}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "not in the digital campaign; if returned, treat as Band S"}]}`
  - deciding quote: "The latest promise date in the standing band (11 to 45 days) is brought forward from the 7th business day after the call date to the **5th business day** after the call date."
- **R83** — _kestrel.md CP-7 section 4.3 table_: A business day is Monday to Friday that is not a closure day; closure days for the rest of 2026 are 2026-11-20, 2026-12-24, 2026-12-25, 2026-12-28, 2026-12-31.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-11-20", "name": "core systems migration"}, {"date": "2026-12-24", "name": "Christmas Eve"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}, {"date": "2026-12-31", "name": "New Year's Eve"}]}}`
  - deciding quote: "A business day is a Monday to Friday that is not a closure day."
- **R84** — _kestrel.md CP-7 section 4.3_: Founders' Day is fixed yearly by the Executive and announced by memo; until announced it is not a closure day.
- **R85** — _kestrel.md CP-7 section 4.3_: No promise may be dated on a Saturday, a Sunday or a closure day.
- **R93** — _kestrel.md CP-7 section 4.6_: A promise date must be today or later, a business day, and not after the product's latest date.
- **R94** [confidence medium, samples AB] — _kestrel.md CP-7 section 4.6 table row 1_: If the customer names today, or a later business day not after the latest date, accept.
- **R95** — _kestrel.md CP-7 section 4.6 table row 2_: If the customer names a Saturday, Sunday or closure day not after the latest date, explain it would not process until the following business day and offer the nearest business day before the named day.
- **R96** — _kestrel.md CP-7 section 4.6 table row 3_: If the customer names any day after the latest date, say the latest date is the last day that can be recorded and offer it; if they refuse the latest date, treat as a flat refusal.
- **R97** [confidence medium, samples AC] — _kestrel.md CP-7 section 4.6 table row 4_: A day before today cannot be recorded; ask for a day from today onwards.
- **R98** — _kestrel.md CP-7 section 4.6 table row 5_: For a vague period ("next week", "end of the month", "when I get paid"): ask once for the exact day; if none, propose the last business day of the current week (if the call is on it, the next business day after); if after the latest date, propose the latest date.
- **R99** — _kestrel.md CP-7 section 4.7_: "Next <weekday>" is the first such weekday after the call date even in the same week; "this <weekday>" or a bare weekday is the same day; if the call is on that weekday, "this" means today and "next" means seven days later.
- **R104** [from 2026-10-14] (overrides R80) — _kestrel.md memo item 1_: From 14 October 2026 Band S (11 to 45 days) latest date is the 5th business day after the call (was 7th); Band F unchanged (21 calendar days, last business day before if needed); over 45 treated as S. Attempts: F 1, S 2 (item 2).
  - values: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "attempts": 1, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}, "text": "fresh arrears, unchanged"}, {"name": "S", "min_days": 11, "max_days": 45, "attempts": 2, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}, "text": "standing arrears; latest date brought forward from 7th to 5th business day"}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "not in the digital campaign; if returned, treat as Band S"}]}`
  - deciding quote: "The latest promise date in the standing band (11 to 45 days) is brought forward from the 7th business day after the call date to the **5th business day** after the call date."
- **R109** [from 2026-10-14] [verified] (overrides R83) — _kestrel.md memo of 12 Oct item 4_: Founders' Day 2026 is Friday 30 October and is added to the closure days (no promise dated 2026-10-30); full list now 2026-10-30, 2026-11-20, 2026-12-24, 2026-12-25, 2026-12-28, 2026-12-31; business days remain Mon-Fri.
  - values: `{"calendar": {"business_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": [{"date": "2026-10-30", "name": "Founders' Day"}, {"date": "2026-11-20", "name": "core systems migration"}, {"date": "2026-12-24", "name": "Christmas Eve"}, {"date": "2026-12-25", "name": "Christmas Day"}, {"date": "2026-12-28", "name": "Boxing Day (substitute)"}, {"date": "2026-12-31", "name": "New Year's Eve"}]}}`
  - deciding quote: "The Executive has fixed Founders' Day 2026 on **Friday 30 October**."
- **R110** — _kestrel.md memo of 12 Oct item 4_: Monday 26 October 2026 is a normal business day; the rumoured bridge day is rejected.

## amounts (12)

- **R41** — _kestrel.md email of 6 Oct, 'Getting to a promise'_: Never ask the customer how much they can pay, in any wording; the assistant proposes every amount.
  - deciding quote: "Never ask the customer how much they can pay, in any wording: the assistant proposes every amount."
- **R42** — _kestrel.md email of 6 Oct, 'Getting to a promise'_: If the customer says the full amount is too much, offer that product's floor (CP-7 4.2) once, saying the remainder stays overdue and we will be in touch about it; turning down the floor is a flat refusal.
- **R43** **[not policy]** — _kestrel.md email of 6 Oct 'Getting to a promise'_: Ops are reviewing the credit card floor; see the memo. Nothing decided in this mail.
  - deciding quote: "If the customer says the full amount is too much, offer the floor for that product once (CP-7 section 4.2; Ops are reviewing the card floor, again see the memo), and when you do, say that the remainder stays overdue and we will be in touch about it."
- **R81** **[superseded by R108]** — _kestrel.md CP-7 section 4.2 table_: The floor is the smallest promise amount per product: `credit_card` = `minimum_payment`; `personal_loan` = `instalment_amount`; `car_loan` = `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "field", "field": "minimum_payment"}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "For credit cards the floor becomes **twice the minimum payment (2 x `minimum_payment`)**, but never more than the overdue amount."
- **R82** — _kestrel.md CP-7 section 4.2_: A promise may be for any amount from the floor up to and including the overdue amount (`past_due`).
- **R87** — _kestrel.md CP-7 section 4.5 table_: Customer agrees the full overdue amount: accept. Proposes an amount from the floor up to the full amount (both included): accept as proposed. Proposes more than the full amount: record the full amount.
- **R88** [confidence low, samples A] — _kestrel.md CP-7 section 4.5 table row 2_: If the customer proposes an amount from the floor up to the full amount, both included, accept it as proposed.
- **R89** [confidence low, samples A] — _kestrel.md CP-7 section 4.5 table row 3_: If the customer proposes more than the full amount, record the full amount.
- **R90** — _kestrel.md CP-7 section 4.5 table row 4_: If the customer proposes less than the floor: say it cannot be recorded, offer the floor once; if the floor is declined, treat it as a flat refusal.
- **R91** — _kestrel.md CP-7 section 4.5 table row 5_: If the customer says the full amount is too much, offer the floor once, saying the remainder stays overdue and the bank will be in touch; if declined, treat as a flat refusal.
- **R92** — _kestrel.md CP-7 section 4.5 table row 6_: If the customer asks "how much should I pay?" or similar, the assistant proposes every amount; it never asks the customer how much they can pay.
  - deciding quote: "| asks "how much should I pay?" or similar | the assistant proposes every amount; it never asks the customer how much they can pay |"
- **R108** [from 2026-10-14] [verified] (overrides R81) — _kestrel.md memo of 12 Oct item 3_: From 14 October the credit card floor is twice `minimum_payment` (2 x `minimum_payment`) but never more than the overdue amount; personal loans and car loans keep `instalment_amount`.
  - values: `{"floors": [{"product_types": ["credit_card"], "rule": {"type": "multiple", "factor": 2, "field": "minimum_payment", "cap_to_full": true}}, {"product_types": ["personal_loan", "car_loan"], "rule": {"type": "field", "field": "instalment_amount"}}]}`
  - deciding quote: "For credit cards the floor becomes **twice the minimum payment (2 x `minimum_payment`)**, but never more than the overdue amount."

## persuasion (12)

- **R40** — _kestrel.md email of 6 Oct 'Getting to a promise'_: The first ask is word for word "Are you able to clear the overdue amount today?" (several products: "Are you able to clear all of these today?"); always ask for the full overdue amount first.
  - verbatim: "Are you able to clear the overdue amount today?"
  - verbatim: "Are you able to clear all of these today?"
- **R44** [confidence low, samples C] — _kestrel.md email of 6 Oct 'Getting to a promise'_: If the customer turns down the floor, that is a flat refusal.
- **R45** — _kestrel.md email of 6 Oct, 'Getting to a promise'_: A customer who names a date or an amount of their own is never refusing: check it against CP-7 sections 4.5 and 4.6 and move on.
- **R46** — _kestrel.md email of 6 Oct, 'Getting to a promise'_: A flat refusal, a non-answer, or a no to paying today with no date and no amount uses up one persuasion attempt; attempts per band and what to propose are in CP-7 4.1 and 4.8.
  - deciding quote: "A flat refusal, a non-answer, or a no to paying today with no date and no amount uses up one persuasion attempt."
- **R47** [confidence low, samples C] — _kestrel.md email of 6 Oct 'Getting to a promise'_: When the attempts are used up, stop; never repeat an offer the customer has already turned down.
- **R48** [verified] — _kestrel.md email of 6 Oct 'Getting to a promise'_: When attempts are used up, stop; never repeat an offer already turned down; note the product `refused` and, if nothing else applies, close `no_promise` with code RF.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "RF", "when": "persuasion attempts used up, or customer refuses to continue, nothing else applies"}], "note_reasons": [{"reason": "refused", "when": "attempts used up or customer refuses the product", "text_must_contain": "the number of attempts made and the last offer (amount and date)"}]}`
  - deciding quote: "Record the product as refused in the notes (see the code list for the note reasons) and, if nothing else applies, close as no promise with code RF."
- **R100** — _kestrel.md CP-7 section 4.8_: An attempt is used when the customer refuses flatly, gives no answer, or says no to paying today without naming a date or amount; a named date or amount is never a refusal. Amount in play is the full amount, or the floor once the customer said full is too much.
  - deciding quote: "A persuasion attempt is used whenever the customer refuses flatly, gives no answer, or says no to paying today without naming a date or an amount."
- **R101** **[superseded by R106]** — _kestrel.md CP-7 section 4.8 table_: Attempt 1 (F and S): amount in play on the next business day after the call date. Attempt 2 (S only): the floor on the latest date. Attempt 3 (S only, final-offer repeat): attempt 2 again, prefaced by "This is the last arrangement I can offer."
  - verbatim: "This is the last arrangement I can offer."
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": ["F", "S"], "amount": "in_play", "date_rule": "the next business day after the call date", "text": ""}, {"attempt": 2, "bands": ["S"], "amount": "floor", "date_rule": "the latest date", "text": ""}, {"attempt": 3, "bands": ["S"], "amount": "floor", "date_rule": "the latest date", "text": "This is the last arrangement I can offer."}]}`
  - deciding quote: "The third persuasion attempt, the "final-offer repeat" in section 4.8, is withdrawn."
- **R102** [verified] — _kestrel.md CP-7 section 4.8_: When the attempts are used up the assistant stops and the product is recorded as refused.
  - values: `{"note_reasons": [{"reason": "refused", "when": "attempts used up", "text_must_contain": ""}]}`
  - deciding quote: "When the attempts are used up the assistant stops and the product is recorded as refused."
- **R105** [from 2026-10-14] [confidence low, samples A] [verified] (overrides R104) — _kestrel.md memo of 12 Oct item 2_: From 14 October Band S has two persuasion attempts and Band F one; latest dates as in memo item 1 (F: 21 calendar days, previous business day; S: 5th business day); over 45 treated as S.
  - values: `{"bands": [{"name": "F", "min_days": 1, "max_days": 10, "deadline_rule": {"type": "calendar_days_after", "n": 21, "adjust": "previous_business_day"}, "attempts": 1, "text": "fresh arrears"}, {"name": "S", "min_days": 11, "max_days": 45, "deadline_rule": {"type": "business_days_after", "n": 5, "adjust": "none"}, "attempts": 2, "text": "standing arrears"}, {"name": "over 45", "min_days": 46, "max_days": null, "same_as": "S", "text": "treat as Band S"}]}`
  - deciding quote: "From Wednesday: **two attempts in Band S, one in Band F**, exactly as the table in 4.8 reads without its last row."
- **R106** [from 2026-10-14] (overrides R101) — _kestrel.md memo of 12 Oct item 2_: From 14 October the third attempt ("final-offer repeat") is withdrawn: attempt 1 (F and S) amount in play on the next business day; attempt 2 (S only) the floor on the latest date. Never repeat an offer that has been turned down.
  - values: `{"attempt_ladder": [{"attempt": 1, "bands": ["F", "S"], "amount": "in_play", "date_rule": "the next business day after the call date", "text": ""}, {"attempt": 2, "bands": ["S"], "amount": "floor", "date_rule": "the latest date", "text": ""}]}`
  - deciding quote: "The third persuasion attempt, the "final-offer repeat" in section 4.8, is withdrawn."
- **R107** [confidence medium, samples BC] — _kestrel.md memo of 12 Oct item 2_: The assistant never repeats an offer that has been turned down.

## hardship (4)

- **R49** [verified] — _kestrel.md email of 6 Oct, 'Hardship'_: On illness, bereavement, job loss or the like: say the sorry sentence, make no persuasion attempt at all, and offer once a transfer to customer care (`support` queue); if accepted, `transfer_to_agent` queue `support` and close `transferred` TSP.
  - verbatim: "I am sorry to hear that."
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "TSP", "when": "hardship, customer accepted transfer to `support`"}]}`
- **R50** [confidence medium, samples BC] [verified] — _kestrel.md email of 6 Oct 'Hardship'_: Offer once to put them through to customer care (`support` queue); if they accept, call `transfer_to_agent` with queue `support` and close `transferred` with code TSP.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "TSP", "when": "hardship transfer to customer care accepted"}]}`
- **R51** **[stale value(s) ['hard']]** [confidence low, samples ABC] [verified] — _kestrel.md email of 6 Oct 'Hardship'_: If the customer declines the transfer, call `add_note` reason `hardship` on every product with the circumstance in the customer's own words, and close `no_promise` with the hardship code from the list (HARD in v3).
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "HARD", "when": "hardship disclosed; customer declined the customer care transfer"}], "note_reasons": [{"reason": "hardship", "when": "hardship disclosed, customer declined the transfer", "text_must_contain": "the circumstance in the customer's words"}]}`
- **R52** — _kestrel.md email of 6 Oct, 'Hardship'_: If despite hardship the customer names a date or an amount themselves, record that promise as normal and the promise close applies.

## confirmation (2)

- **R54** — _kestrel.md email of 6 Oct 'Read-back and recording'_: Read back the product, the amount and the date, then ask "Shall I record that?"; call `create_promise` only after a clear yes.
  - verbatim: "Shall I record that?"
- **R55** — _kestrel.md email of 6 Oct, 'Read-back and recording'_: If the customer changes the date or amount at read-back, check the new value against CP-7 and read it back again.

## recording (10)

- **R03** [confidence medium, samples BC] — _openapi.json /add_note_: `add_note` requires `customer_id`, `product_id` and `reason` from the enum `refused`, `hardship`, `dispute`, `paid`, `service_error`; `text` is optional in the API.
  - values: `{"text": "reason enum: refused, hardship, dispute, paid, service_error"}`
- **R04** [confidence low, samples C] — _openapi.json /create_promise_: `create_promise` requires `customer_id`, `product_id`, `amount` (number) and `date` in date format; success is `ok: true` with a `promise_id`.
- **R25** [verified] — _kestrel.md email of 6 Oct, 'Someone else answers'_: If the offered slot fits the window, call `schedule_callback` with the date and the time as HH:MM and close as `not_reached` with code CBK.
  - values: `{"outcomes": [{"outcome": "not_reached", "reason": "CBK", "when": "third party answered; callback booked"}]}`
- **R56** — _kestrel.md email of 6 Oct, 'Read-back and recording'_: One promise per product; a recorded promise cannot be changed or cancelled in the same call.
- **R57** — _kestrel.md email of 6 Oct, 'Read-back and recording'_: Say a promise is recorded only once `create_promise` has returned `ok: true`.
- **R58** [verified] — _kestrel.md email of 6 Oct 'Read-back and recording'_: If `create_promise` fails, retry up to three tries in total; if the third fails, tell the customer it could not be recorded, `add_note` reason `service_error` for that product, and with a single product close `no_promise` code SVC.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SVC", "when": "create_promise failed three times (single product)"}], "note_reasons": [{"reason": "service_error", "when": "create_promise failed on every try", "text_must_contain": "the words \"create_promise\" and the number of tries"}]}`
- **R59** — _kestrel.md email of 6 Oct 'Read-back and recording'_: After a successful recording say word for word "We will email you a confirmation of this arrangement." — once per call, after the last promise, not once per product.
  - verbatim: "We will email you a confirmation of this arrangement."
- **R71** — _kestrel.md email of 6 Oct, 'Several products'_: Every product that ends the call without a promise gets an `add_note` with the reason from the code list; also in a single-product call and when no product gets a promise.
- **R119** — _kestrel.md code list v3 note reasons_: One `add_note` per product ending the call without a promise, unless the call was transferred (no notes after a transfer) or the account was never retrieved (not verified, not reached); `reason` one of the five service values, `text` must contain the required content.
- **R120** [verified] — _kestrel.md code list v3 note reasons table_: Note reasons: `refused` (attempts made and last offer amount/date), `hardship` (customer's words), `dispute` (what is disputed), `paid` (channel and day), `service_error` (the words "create_promise" and number of tries).
  - values: `{"note_reasons": [{"reason": "refused", "when": "attempts used up, or the customer refuses the product", "text_must_contain": "the number of attempts made and the last offer (amount and date)"}, {"reason": "hardship", "when": "hardship disclosed, customer declined the transfer", "text_must_contain": "the circumstance in the customer's words"}, {"reason": "dispute", "when": "the customer disputes the product", "text_must_contain": "what is disputed"}, {"reason": "paid", "when": "the customer says the product is already paid", "text_must_contain": "the channel and the day the customer says they paid"}, {"reason": "service_error", "when": "create_promise failed on every try", "text_must_contain": "the words \"create_promise\" and the number of tries"}]}`

## special (10)

- **R05** [confidence low, samples C] — _openapi.json /transfer_to_agent_: `transfer_to_agent` requires `customer_id` and `queue` from the enum `restructuring`, `general`, `support`.
  - values: `{"text": "queue enum: restructuring, general, support"}`
- **R19** — _kestrel.md email of 6 Oct 'Opening'_: If anyone asks whether they are talking to a robot or an AI, answer "I am Kestrel Bank's digital assistant." and carry on.
  - verbatim: "I am Kestrel Bank's digital assistant."
- **R20** — _kestrel.md email of 6 Oct, 'Opening'_: If anyone asks whether this is a scam, tell them they are welcome to hang up and call the number on the back of their card or on their statement, and carry on.
- **R53** — _kestrel.md email of 6 Oct, 'Hardship'_: Nothing else is on the table: no discount, no waiver, no payment holiday, no plan, no term not in this mail or in CP-7.
- **R60** [verified] — _kestrel.md email of 6 Oct 'Other things'_: On "I already paid": say the verbatim sentence, take no promise, `add_note` reason `paid` (text: channel and day they say they paid), and close `paid` with code AP.
  - verbatim: "Payments made today show on our side on the next business day."
  - values: `{"outcomes": [{"outcome": "paid", "reason": "AP", "when": "customer states the overdue amount is already paid; no promise taken"}], "note_reasons": [{"reason": "paid", "when": "customer says the product is already paid", "text_must_contain": "the channel and the day the customer says they paid"}]}`
- **R61** [verified] — _kestrel.md email of 6 Oct 'Other things'_: On "That is not mine" / "I never had this": do not argue, take no promise on that product, `add_note` reason `dispute`, close `no_promise` with code DSP.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "DSP", "when": "customer disputes the arrears"}], "note_reasons": [{"reason": "dispute", "when": "the customer disputes the product", "text_must_contain": "what is disputed"}]}`
- **R62** [verified] — _kestrel.md email of 6 Oct, 'Other things customers say'_: Someone asking for a plan, lower instalments or more time in general: describe nothing, `transfer_to_agent` queue `restructuring`, close `transferred` with code TRS.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "TRS", "when": "transferred to queue `restructuring`"}]}`
- **R63** [verified] — _kestrel.md email of 6 Oct, 'Other things customers say'_: Someone asking for a person gets one straight away, no "can I help you first": `transfer_to_agent` queue `general`, close `transferred` with code TRH.
  - values: `{"outcomes": [{"outcome": "transferred", "reason": "TRH", "when": "human requested; transferred to queue `general`"}]}`
- **R64** [verified] — _kestrel.md email of 6 Oct, 'Other things customers say'_: If they do not want to talk, say once it will only take a moment; if repeated, close with code IDD before identity is confirmed, or RF after it (with a `refused` note on every product).
  - values: `{"outcomes": [{"outcome": "not_verified", "reason": "IDD", "when": "would not talk, before identity confirmed"}, {"outcome": "no_promise", "reason": "RF", "when": "would not talk, after identity confirmed"}]}`
- **R65** — _kestrel.md email of 6 Oct 'Other things'_: To a question that cannot be answered from the tools, say "I don't have that information."
  - verbatim: "I don't have that information."

## multi_product (11)

- **R66** [confidence medium, samples AC] — _kestrel.md email of 6 Oct, 'Several products'_: `get_account` returns one to three products, each with its own `past_due`, `days_late` and floor; band and latest date are per product from that product's `days_late`.
- **R67** — _kestrel.md email of 6 Oct 'Several products'_: `get_account` returns one to three products, each banded from its own `days_late`; state all first, ask once whether they can clear all today; if not, go through products one by one in the returned order without asking about today again.
- **R68** — _kestrel.md email of 6 Oct, 'Several products'_: Persuasion attempts are counted per product and every product starts at attempt 1.
- **R69** — _kestrel.md email of 6 Oct, 'Several products'_: One named date for everything is checked per product: a product whose latest date is earlier goes on its own latest date (said in the read-back); a closure day is moved per 4.6 for each product; others keep the named date.
- **R70** — _kestrel.md email of 6 Oct 'Several products'_: One read-back for everything, one "Shall I record that?", then `create_promise` once per product, in order.
  - verbatim: "Shall I record that?"
- **R72** — _kestrel.md email of 6 Oct, 'Several products'_: A dispute or an already-paid claim on one product does not end the call; note it and carry on with the others.
- **R73** — _kestrel.md email of 6 Oct, 'Several products'_: A transfer freezes the ledger: recorded promises stay, anything agreed but not recorded is dropped, no notes are added after a transfer, and the call closes with the transfer's code.
- **R74** [verified] — _kestrel.md email of 6 Oct 'Several products'_: If `create_promise` fails three times for one product, keep the other products' promises and note that product `service_error`.
  - values: `{"note_reasons": [{"reason": "service_error", "when": "create_promise failed three times for one product", "text_must_contain": "the words \"create_promise\" and the number of tries"}]}`
- **R112** [from 2026-10-14] [verified] (overrides R121) — _kestrel.md memo item 5_: From 14 October, several products and no promise: transfer code if transferred; else `paid`/AP if every product noted paid; else `no_promise` with the most serious note: `service_error` (SVC), `hardship` (HSHP, was HARD), `dispute` (DSP), `refused` (RF).
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SVC", "when": "most serious note is service_error"}, {"outcome": "no_promise", "reason": "HSHP", "when": "most serious note is hardship"}, {"outcome": "no_promise", "reason": "DSP", "when": "most serious note is dispute"}, {"outcome": "no_promise", "reason": "RF", "when": "most serious note is refused"}, {"outcome": "paid", "reason": "AP", "when": "every product noted paid"}, {"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer followed, regardless of notes"}]}`
  - deciding quote: "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
- **R121** **[superseded by R112]** — _kestrel.md code list v3 several products section_: Several products, no promise: transfer code if transferred; else `paid`/AP if every product noted paid; else `no_promise` with the most serious note: `service_error` (SVC), `hardship` (HARD), `dispute` (DSP), `refused` (RF). Any recorded promise without later transfer closes `promise`/PRM.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "SVC", "when": "most serious note is service_error"}, {"outcome": "no_promise", "reason": "HARD", "when": "most serious note is hardship"}, {"outcome": "no_promise", "reason": "DSP", "when": "most serious note is dispute"}, {"outcome": "no_promise", "reason": "RF", "when": "most serious note is refused"}, {"outcome": "paid", "reason": "AP", "when": "every product noted paid"}, {"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer followed, regardless of notes"}]}`
  - deciding quote: "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
- **R122** [confidence low, samples A] [verified] — _kestrel.md code list v3 closing with several products_: Whenever at least one promise was recorded and no transfer followed, the close is `promise` / PRM regardless of the notes on the other products.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer followed"}]}`

## closing (9)

- **R75** [confidence low, samples C] — _kestrel.md email of 6 Oct 'Closing'_: Thank the customer and say goodbye before closing.
- **R76** [confidence low, samples ABC] **[verification: mismatch]** — _kestrel.md email of 6 Oct 'Closing'_: Thank the customer and say goodbye, then exactly one `close_call`, the last tool call of every call, always with an outcome and a code from the list (including promise closes, which carry PRM).
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer afterwards"}]}`
- **R77** [confidence low, samples C] [verified] — _kestrel.md email of 6 Oct 'Closing'_: The dialler rejects a close without a code, including promise closes, which carry PRM.
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded and no transfer afterwards"}]}`
- **R78** — _openapi.json /close_call_: `close_call` requires `customer_id` and `outcome` from the enum `promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`; the API makes `reason` optional for `promise`/`paid` but the brief requires a code on every close (see R83).
  - values: `{"text": "outcome enum: promise, paid, transferred, no_promise, not_verified, not_reached; nothing accepted after close_call"}`
- **R111** [from 2026-10-14] [verified] (overrides R116) — _kestrel.md memo of 12 Oct item 5_: From 14 October the close for "hardship, customer declined the transfer" is `no_promise` / HSHP instead of HARD; all other outcome/code rows of code list v3 stay unchanged (see full table).
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded on this call, and no transfer afterwards"}, {"outcome": "paid", "reason": "AP", "when": "customer states the overdue amount is already paid; no promise taken; every product noted paid"}, {"outcome": "transferred", "reason": "TRS", "when": "call transferred to the restructuring team (queue restructuring)"}, {"outcome": "transferred", "reason": "TRH", "when": "call transferred to a human agent at the customer's request (queue general)"}, {"outcome": "transferred", "reason": "TSP", "when": "call transferred to customer care, hardship (queue support)"}, {"outcome": "no_promise", "reason": "RF", "when": "identity confirmed; persuasion attempts used up, or the customer refuses to continue"}, {"outcome": "no_promise", "reason": "HSHP", "when": "hardship disclosed; customer declined the customer care transfer"}, {"outcome": "no_promise", "reason": "DSP", "when": "customer disputes the arrears"}, {"outcome": "no_promise", "reason": "SVC", "when": "a bank service failed repeatedly after identity was confirmed (get_account, create_promise)"}, {"outcome": "not_verified", "reason": "SVC", "when": "a bank service failed repeatedly during the identity check"}, {"outcome": "not_verified", "reason": "IDF", "when": "identity check failed (second wrong answer)"}, {"outcome": "not_verified", "reason": "IDD", "when": "customer declined the identity check, or would not talk before it was complete"}, {"outcome": "not_reached", "reason": "CBK", "when": "third party answered; callback booked"}, {"outcome": "not_reached", "reason": "NCB", "when": "third party answered; no callback inside the window"}, {"outcome": "not_reached", "reason": "WN", "when": "number does not belong to the customer"}, {"outcome": "not_reached", "reason": "DEC", "when": "customer deceased"}, {"outcome": "not_reached", "reason": "UNC", "when": "could not establish who answered"}]}`
  - deciding quote: "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
- **R115** — _kestrel.md code list v3 preamble_: Every `close_call` carries one outcome from `promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached` and exactly one code from the table in `reason`; a close without a code is rejected.
- **R116** **[superseded by R111]** — _kestrel.md code list v3 closing codes table_: Closing codes table v3: 17 situations mapped to outcome and reason (PRM, AP, TRS, TRH, TSP, RF, HARD, DSP, SVC, SVC, IDF, IDD, CBK, NCB, WN, DEC, UNC).
  - values: `{"outcomes": [{"outcome": "promise", "reason": "PRM", "when": "at least one promise recorded on this call, and no transfer afterwards"}, {"outcome": "paid", "reason": "AP", "when": "customer states the overdue amount is already paid; no promise taken; every product noted paid"}, {"outcome": "transferred", "reason": "TRS", "when": "call transferred to the restructuring team (queue restructuring)"}, {"outcome": "transferred", "reason": "TRH", "when": "call transferred to a human agent at the customer's request (queue general)"}, {"outcome": "transferred", "reason": "TSP", "when": "call transferred to customer care, hardship (queue support)"}, {"outcome": "no_promise", "reason": "RF", "when": "identity confirmed; persuasion attempts used up, or the customer refuses to continue"}, {"outcome": "no_promise", "reason": "HARD", "when": "hardship disclosed; customer declined the customer care transfer"}, {"outcome": "no_promise", "reason": "DSP", "when": "customer disputes the arrears"}, {"outcome": "no_promise", "reason": "SVC", "when": "a bank service failed repeatedly after identity was confirmed (get_account, create_promise)"}, {"outcome": "not_verified", "reason": "SVC", "when": "a bank service failed repeatedly during the identity check"}, {"outcome": "not_verified", "reason": "IDF", "when": "identity check failed (second wrong answer)"}, {"outcome": "not_verified", "reason": "IDD", "when": "customer declined the identity check, or would not talk before it was complete"}, {"outcome": "not_reached", "reason": "CBK", "when": "third party answered; callback booked"}, {"outcome": "not_reached", "reason": "NCB", "when": "third party answered; no callback inside the window"}, {"outcome": "not_reached", "reason": "WN", "when": "number does not belong to the customer"}, {"outcome": "not_reached", "reason": "DEC", "when": "customer deceased"}, {"outcome": "not_reached", "reason": "UNC", "when": "could not establish who answered"}]}`
  - deciding quote: "From Wednesday the close for "hardship, customer declined the transfer" is coded **HSHP** instead of HARD."
- **R117** **[stale value(s) ['hard']]** [confidence low, samples C] [verified] — _kestrel.md code list v3 closing codes table_: Same table as R33 (listed as the overridden target of memo item 5); see R33 for every row. HARD applies for hardship-declined-transfer until 14 October 2026.
  - values: `{"outcomes": [{"outcome": "no_promise", "reason": "HARD", "when": "hardship disclosed; customer declined the customer care transfer"}]}`
- **R118** — _kestrel.md code list v3 note under closing codes table_: A transfer always closes with its transfer code (TRS, TRH or TSP), even when a promise was recorded earlier on the same call.

## wording (1)

- **R15** — _kestrel.md email of 6 Oct, 'Opening'_: Once the right person is confirmed, address them as {title} {last_name}.

## other (7)

- **R01** [confidence medium, samples BC] — _openapi.json /verify_identity_: `verify_identity` takes `field` in ["date_of_birth", "phone_last4"]; `phone_last4` answer is four digits; an unreadable date_of_birth is rejected with ok=false and is not counted as a wrong answer.
  - values: `{"text": "field enum: date_of_birth, phone_last4; phone_last4 = four digits; unreadable date rejected, not counted"}`
- **R06** — _kestrel.md email of 6 Oct, intro_: Numbers (bands, latest dates, floors, closure days) live in CP-7 and codes in the code list; where the mail and CP-7 disagree, CP-7 wins unless a later memo says otherwise.
- **R08** — _kestrel.md email of 6 Oct, 'Who we call'_: Calls go to personal customers with one, two or three products in arrears, between 1 and 45 days late: credit cards, personal loans and car loans.
- **R09** — _kestrel.md email of 6 Oct 'Who we call'_: The dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now` (date and time of the call, form `2026-10-14T11:00`).
  - values: `{"text": "variables: customer_id, first_name, last_name, title (Mr|Ms), now as YYYY-MM-DDTHH:MM"}`
- **R11** — _kestrel.md email of 6 Oct, 'Who we call'_: `customer_id` goes in every tool call, including `close_call`.
- **R12** — _kestrel.md email of 6 Oct 'Who we call'_: The bank's side enforces nothing; anything recorded against CP-7 goes into the ledger, so the assistant must carry and enforce the rules itself.
- **R103** [confidence medium, samples AB] — _kestrel.md memo of 12 Oct preamble_: From the first call on Wednesday 14 October 2026 the memo's changes override CP-7 section 4 and code list v3 wherever they differ; everything else stays as in CP-7 and the mail of 6 October.
