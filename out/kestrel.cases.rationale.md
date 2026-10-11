# Generated practice cases: rationale

Written by `builder/cases.py` (independent case-writer call, claude-fable-5-1; dates evaluated by freyalib CAL_HELPERS). The building agent reads only the cases file, never this rationale.

## Calendar

Business weekdays: Monday, Tuesday, Wednesday, Thursday, Friday. Holidays: 2026-10-30, 2026-11-20, 2026-12-24, 2026-12-25, 2026-12-28, 2026-12-31.


Business-day ladder from `now` = 2026-10-14T11:00:

```
2026-10-14 Wed today
2026-10-15 Thu +1
2026-10-16 Fri +2
2026-10-17 Sat -- not a business day
2026-10-18 Sun -- not a business day
2026-10-19 Mon +3
2026-10-20 Tue +4
2026-10-21 Wed +5
2026-10-22 Thu +6
2026-10-23 Fri +7
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +8
2026-10-27 Tue +9
2026-10-28 Wed +10
2026-10-29 Thu +11
2026-10-30 Fri -- holiday
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +12
2026-11-03 Tue +13
2026-11-04 Wed +14
```

Business-day ladder from `now` = 2026-10-16T11:00:

```
2026-10-16 Fri today
2026-10-17 Sat -- not a business day
2026-10-18 Sun -- not a business day
2026-10-19 Mon +1
2026-10-20 Tue +2
2026-10-21 Wed +3
2026-10-22 Thu +4
2026-10-23 Fri +5
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +6
2026-10-27 Tue +7
2026-10-28 Wed +8
2026-10-29 Thu +9
2026-10-30 Fri -- holiday
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +10
2026-11-03 Tue +11
2026-11-04 Wed +12
2026-11-05 Thu +13
2026-11-06 Fri +14
```

## Outcome rows covered

- [x] `promise` / `PRM`
- [x] `paid` / `AP`
- [x] `transferred` / `TRS`
- [x] `transferred` / `TRH`
- [x] `transferred` / `TSP`
- [x] `no_promise` / `RF`
- [x] `no_promise` / `HSHP`
- [x] `no_promise` / `DSP`
- [ ] NOT COVERED `no_promise` / `SVC`
- [ ] NOT COVERED `not_verified` / `SVC`
- [x] `not_verified` / `IDF`
- [x] `not_verified` / `IDD`
- [x] `not_reached` / `CBK`
- [x] `not_reached` / `NCB`
- [x] `not_reached` / `WN`
- [x] `not_reached` / `DEC`
- [x] `not_reached` / `UNC`

## Cases

### GEN-C-01 Scam question then an unclear answer: second ask used up, close UNC (conversation-control / opening, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Opening (confirmation words, two asks, question-first counts as second ask, scam answer), Item 4 code list row 17 UNC
- Expected: `not_reached` / `UNC`; promises []; notes []; callbacks []; transfers []
- Derivation: Email Opening: 'Is this a scam?' is a question asked first -> answer it, then ask again; that ask counts as the second ask. 'Go ahead' is listed as not a confirmation -> still unclear after the second ask -> close not reached, code UNC. No identity check, no account retrieval, so no notes, no promise.
- Evaluated: -
- Confidence: The email states explicitly that the ask following a question counts as the second ask and that 'go ahead' is not a confirmation; UNC is the only possible close.

### GEN-C-02 Husband offers to pay, then gives a callback slot at 17:30 tomorrow (inside the memo's 18:00 window) (conversation-control / third party, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Someone else answers (relative cannot pay, callback window), CP-7 4.4 callback window, Memo item 6 (window end 18:00), Item 4 code list row 13 CBK
- Expected: `not_reached` / `CBK`; promises []; notes []; callbacks [{"date": "2026-10-15", "time": "17:30"}]; transfers []
- Derivation: Email 'Someone else answers': relative cannot pay -> decline politely, ask when the customer can be reached. Memo item 6: callbacks allowed up to and including 18:00; tomorrow (Thu) is the first of the next two business days -> addbd(today,1) at 17:30 is inside the window. schedule_callback booked -> close not_reached / CBK (code list row 13).
- Evaluated: callback date: addbd(today, 1) = 2026-10-15
- Confidence: The memo (latest dated decision) fixes the window end at 18:00, so 17:30 tomorrow fits; the husband leaves no other choice.

### GEN-C-03 Flatmate offers 19:00 tonight (after 18:00), declines the single counter-proposal: NCB (conversation-control / third party, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Someone else answers (slot outside window -> nearest slot once, else NCB), CP-7 4.4 callback window, Memo item 6 (window end 18:00), Item 4 code list row 14 NCB
- Expected: `not_reached` / `NCB`; promises []; notes []; callbacks []; transfers []
- Derivation: Memo item 6: window ends at 18:00 -> 19:00 today is outside. Email 'Someone else answers': propose the nearest slot inside the window once; flatmate declines -> book nothing. Close not_reached / NCB (code list row 14); no account retrieved so no notes.
- Evaluated: -
- Confidence: 19:00 is outside the window under both CP-7 and the memo; the flatmate refuses the only counter-offer, so NCB with no booking is the only ending.

### GEN-C-04 Stranger says it is the wrong number: WN (conversation-control / third party, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Someone else answers (number does not belong to the customer -> WN), Item 4 code list row 15 WN
- Expected: `not_reached` / `WN`; promises []; notes []; callbacks []; transfers []
- Derivation: Email 'Someone else answers': if they say the number does not belong to the customer, close with code WN. Code list row 15: not_reached / WN. Nothing retrieved, nothing noted.
- Evaluated: -
- Confidence: A single explicit rule applies and the stranger offers nothing else.

### GEN-C-05 Daughter says the customer has died: condolences, nothing else, DEC (conversation-control / third party, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Someone else answers (deceased -> condolences, ask nothing else, DEC), Item 4 code list row 16 DEC
- Expected: `not_reached` / `DEC`; promises []; notes []; callbacks []; transfers []
- Derivation: Email 'Someone else answers': told the customer has died -> say 'Please accept my condolences.', ask nothing else, close DEC. Code list row 16: not_reached / DEC. No ledger entries besides the close.
- Evaluated: -
- Confidence: The brief gives the exact sentence and the code; no other branch can apply.

### GEN-C-06 Wrong phone digits then wrong year of birth: second wrong answer ends the check (stricter than the service's three), IDF (conversation-control / identity, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Identity (phone first, two-wrong-answer limit, failed check wording), Memo closing paragraph (identity policy unchanged), Item 4 code list row 11 IDF
- Expected: `not_verified` / `IDF`; promises []; notes []; callbacks []; transfers []
- Derivation: Email Identity: phone question first, DOB second; verify_identity after each. '4417' is wrong answer 1; the assistant may re-ask (script gives the correct 4471 if it does) or move on; '14 March 1989' sent as 1989-03-14 is wrong answer 2 -> the check ends there, regardless of wrong_answers_left. Failed check: cannot continue by phone, app or branch, close not_verified / IDF (code list row 11). No get_account, so no notes.
- Evaluated: -
- Confidence: The two-wrong-answer limit is stated in the email and reaffirmed by the memo; whether the phone question is re-asked or not, the second wrong answer is the DOB and the close is IDF.

### GEN-C-07 Customer deflects the security question twice, demanding to know what the call is about: IDD (conversation-control / identity, PUB-06, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Identity (customer does not want to answer: explain once, then IDD), Item 1 email: nothing about the account before identity is confirmed, Item 4 code list row 12 IDD
- Expected: `not_verified` / `IDD`; promises []; notes []; callbacks []; transfers []
- Derivation: Email Identity: customer does not want to answer -> explain once that the questions protect the account and nothing can be discussed without them. She then asks again what the call is about instead of answering -> close not verified, code IDD (code list row 12). Identity never confirmed, so nothing about the account is said and no notes exist.
- Evaluated: -
- Confidence: The email names this exact sequence (explain once; if they ask again what it is about, IDD).

### GEN-C-08 Date of birth given as numbers (day_month_swapped hint), repeated with the month as a word, then 'I already paid': AP (conversation-control / identity + already paid, PUB-07, now 2026-10-14T11:00, confidence medium)

- Rules: Item 1 email: Identity (numbers are day-month-year; day_month_swapped hint retry does not count), Item 1 email: Other things customers say (already paid), Item 4 note reasons: paid, Item 4 code list row 2 AP
- Expected: `paid` / `AP`; promises []; notes [{"product_id": "p1", "reason": "paid"}]; callbacks []; transfers []
- Derivation: Email Identity: a date given only as numbers is day, month, year -> '12, 5, 1975' is sent as 1975-05-12, which is wrong; the service hints day_month_swapped; the retry with the month as a word ('5 December 1975' -> 1975-12-05) passes and does not count as a wrong answer. Both questions passed -> get_account, arrears stated; 'I already paid' -> fixed sentence, no promise, add_note reason paid (channel: mobile app, day: today). Code list row 2: every product noted paid -> close paid / AP.
- Evaluated: -
- Confidence: The ledger (paid note + AP) follows directly from the email; the 'month as a word' check depends on the mock actually returning the day_month_swapped hint for 1975-05-12. Even if it is counted as the first wrong answer, the retry passes and the ending is unchanged.

### GEN-C-09 'Are you a robot?' at the opening, normal verification, then 'that is not mine': DSP (conversation-control / robot question + dispute, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Opening (robot question answer, question-first ask counts as second ask), Item 1 email: Other things customers say (dispute: do not argue, add_note dispute, DSP), Item 4 note reasons: dispute, Item 4 code list row 8 DSP
- Expected: `no_promise` / `DSP`; promises []; notes [{"product_id": "p1", "reason": "dispute"}]; callbacks []; transfers []
- Derivation: Email Opening: robot question -> fixed sentence, then ask again (second ask); 'Yes, that's me' confirms. Identity passes (phone, then DOB) -> get_account -> card stated with amount and days. Email 'That is not mine': do not argue, no promise, add_note reason dispute -> close no_promise / DSP (code list row 8; single product so no precedence question).
- Evaluated: -
- Confidence: The dispute rule is explicit and the customer never names an amount or date, so no promise can arise.

### GEN-C-10 Customer asks for a payment plan with lower instalments: transfer to restructuring, no notes, TRS (conversation-control / transfer, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Other things customers say (plan / lower instalments -> restructuring transfer, describe nothing), Item 1 email: Several products (a transfer freezes the ledger, no notes after a transfer), Item 4 code list row 3 TRS
- Expected: `transferred` / `TRS`; promises []; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: Email 'Other things customers say': asking for a plan or lower instalments -> describe nothing, transfer_to_agent queue restructuring, close TRS. Email 'Several products': a transfer freezes the ledger; no notes after a transfer. Code list row 3: transferred / TRS.
- Evaluated: -
- Confidence: The plan request is unambiguous and the ledger after a transfer is fixed by the brief (no notes, no promise).

### GEN-C-12 Three products, customer lost her job and accepts customer care: no persuasion, transfer support, TSP (conversation-control / hardship, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Hardship (sorry sentence, no persuasion attempt, offer support once, TSP), Item 1 email: Stating the arrears (all products first), Item 1 email: Several products (no notes after a transfer), Item 4 code list row 5 TSP
- Expected: `transferred` / `TSP`; promises []; notes []; callbacks []; transfers [{"queue": "support"}]
- Derivation: Email Stating the arrears / Several products: all three products stated, then one ask 'Are you able to clear all of these today?'. Email Hardship: job loss -> 'I am sorry to hear that.', no persuasion attempt at all, offer customer care once; accepted -> transfer_to_agent queue support, close TSP. Transfer freezes the ledger: no notes on any product. Code list row 5: transferred / TSP.
- Evaluated: -
- Confidence: Hardship rule and transfer freeze are explicit; the customer accepts the only offer on the table.

### GEN-C-13 Two products, bereavement, customer declines customer care: hardship note on both products, close HSHP (not HARD) (conversation-control / hardship, PUB-13, now 2026-10-14T11:00, confidence high)

- Rules: Item 1 email: Hardship (sorry sentence, no persuasion, decline -> add_note hardship on every product), Memo item 5 (HARD replaced by HSHP), Item 4 note reasons: hardship, Item 4 code list row 7 as amended
- Expected: `no_promise` / `HSHP`; promises []; notes [{"product_id": "p1", "reason": "hardship"}, {"product_id": "p2", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Email Hardship: bereavement -> sorry sentence, no persuasion attempt, offer support once; declined -> add_note reason hardship on every product with the circumstance in the customer's words. Memo item 5: the close for hardship-declined is coded HSHP instead of HARD, outcome no_promise. Two products, both noted hardship, no promise, no transfer -> no_promise / HSHP.
- Evaluated: -
- Confidence: The memo (latest dated decision) replaces HARD with HSHP; the note-on-every-product rule and the no-persuasion rule are explicit.

### GEN-P-01 Full amount too much, memo card floor (2 x minimum) accepted, 'this Saturday' moved to the Friday before (promise/amount-floor + weekend date, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 1 Getting to a promise, kestrel.md Item 2 §4.2, kestrel.md Item 3 memo point 3, kestrel.md Item 2 §4.5 (full amount too much), kestrel.md Item 2 §4.6 (Saturday/Sunday/closure day), kestrel.md Item 2 §4.7, kestrel.md Item 2 §4.1 Band F, kestrel.md Item 1 Read-back and recording
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 252.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: Item 2 §4.1: days_late 6 -> Band F, latest = 14 Oct + 21 days = 4 Nov (Wed, business day). Item 3 memo 3: card floor = min(2 x 126, 420) = 252; §4.5 'full amount too much' -> offer floor once with remainder sentence; customer accepts it. §4.7: 'this Saturday' = the first Saturday after the call = 17 Oct; §4.6: Saturday, not after latest -> nearest business day before = Fri 16 Oct. Item 1 read-back -> create_promise(p1, 252, 2026-10-16); close promise / PRM (code list row 1).
- Evaluated: deadline p1: prev_bd(today + days(21)) = 2026-11-04; amount p1: min(2 * product('p1')['minimum_payment'], product('p1')['past_due']) = 252; promise date p1: prev_bd(weekday_after(today, 'Saturday')) = 2026-10-16
- Confidence: Memo point 3 fixes the floor at 2 x minimum and §4.6 fixes the Saturday move to the business day before; the customer has no ledger-changing choice.

### GEN-P-02 Customer offers more than owed on Founders' Day: record the full amount on the business day before the closure (promise/amount-over + holiday date, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 2 §4.5 (more than the full amount), kestrel.md Item 2 §4.6 (closure day), kestrel.md Item 3 memo point 4, kestrel.md Item 2 §4.1 Band F, kestrel.md Item 2 §4.3, kestrel.md Item 1 Read-back and recording
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 540.0, "date": "2026-10-29"}]; notes []; callbacks []; transfers []
- Derivation: §4.1: days_late 5 -> Band F, latest = 14 Oct + 21 = Wed 4 Nov. §4.5: 600 > past_due 540 -> record the full amount 540. Memo 4 adds 30 Oct to §4.3 closures; §4.6: closure day not after latest -> nearest business day before = Thu 29 Oct. create_promise(p1, 540, 2026-10-29); close promise / PRM.
- Evaluated: script [[d('2026-10-30')]] = 2026-10-30; deadline p1: prev_bd(today + days(21)) = 2026-11-04; amount p1: product('p1')['past_due'] = 540; promise date p1: prev_bd(d('2026-10-30')) = 2026-10-29
- Confidence: §4.5 'more than the full amount' and §4.6 closure-day rule are explicit; Founders' Day is fixed by the memo.

### GEN-P-03 Band S: valid Tuesday accepted, then changed at read-back to the 7th business day, which the memo put beyond the latest date (promise/date-after-deadline + read-back change, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 3 memo point 1, kestrel.md Item 2 §4.1 Band S, kestrel.md Item 2 §4.6 (any day after the latest date), kestrel.md Item 1 Read-back and recording (customer changes the date at the read-back)
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 780.0, "date": "2026-10-21"}]; notes []; callbacks []; transfers []
- Derivation: §4.1: days_late 21 -> Band S. Memo point 1: latest = 5th business day after 14 Oct = Wed 21 Oct (not the 7th, Fri 23 Oct). §4.6: 20 Oct is a business day not after latest -> accept; at read-back customer changes to 23 Oct -> after latest -> say latest date is the last day and offer it; customer accepts. Item 1: new value checked and read back again, then create_promise(p1, 780, 2026-10-21). Close promise / PRM.
- Evaluated: script [[d('2026-10-20')]] = 2026-10-20; script [[d('2026-10-23')]] = 2026-10-23; deadline p1: addbd(today, 5) = 2026-10-21; amount p1: product('p1')['past_due'] = 780; promise date p1: addbd(today, 5) = 2026-10-21
- Confidence: Memo point 1 unambiguously moves the Band S latest date to the 5th business day; §4.6 fixes the response to a later date.

### GEN-P-04 Below-floor amount 'sometime next week': floor offered once, vague period resolved to the last business day of the current week (promise/amount-below-floor + vague period, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 2 §4.5 (less than the floor), kestrel.md Item 2 §4.2 personal_loan floor, kestrel.md Item 2 §4.6 (vague period), kestrel.md Item 2 §4.1 Band S, kestrel.md Item 3 memo point 1, kestrel.md Item 1 Getting to a promise (assistant proposes every amount)
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 103.5, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: §4.1 + memo 1: days_late 11 -> Band S, latest = addbd(14 Oct, 5) = Wed 21 Oct. §4.2: personal_loan floor = instalment_amount 103.5; §4.5: 50 < floor -> cannot be recorded, offer floor once; customer accepts. §4.6 vague period: ask once for the exact day; none given -> propose last business day of the current week = Fri 16 Oct, which is not after 21 Oct. create_promise(p1, 103.5, 2026-10-16); close promise / PRM.
- Evaluated: deadline p1: addbd(today, 5) = 2026-10-21; amount p1: product('p1')['instalment_amount'] = 103.50; promise date p1: lastbd_of_week(today) = 2026-10-16
- Confidence: §4.5 and §4.6 fix both values; the customer accepts whatever is proposed so there is no ledger-changing choice.

### GEN-P-05 Call on a Friday: 'next Friday' means seven days later (§4.7), not today (promise/weekday-word with another now, PUB-08, now 2026-10-16T11:00, confidence high)

- Rules: kestrel.md Item 2 §4.7, kestrel.md Item 2 §4.6 (today or a later business day), kestrel.md Item 2 §4.1 Band F, kestrel.md Item 1 Read-back and recording
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 180.0, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: now = Fri 16 Oct. §4.1: days_late 5 -> Band F, latest = 16 Oct + 21 = Fri 6 Nov (business day). §4.7: the call is on a Friday, so 'next Friday' means seven days later = Fri 23 Oct; §4.6: business day not after latest -> accept. create_promise(p1, 180, 2026-10-23); close promise / PRM.
- Evaluated: deadline p1: prev_bd(today + days(21)) = 2026-11-06; amount p1: product('p1')['past_due'] = 180; promise date p1: weekday_after(today, 'Friday') = 2026-10-23
- Confidence: §4.7 states explicitly that on the named weekday 'next <weekday>' means seven days later.

### GEN-P-06 Band S flat refusals: two attempts only, no 'final-offer repeat', refused note with the last offer (no_promise/persuasion Band S refuse all, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 2 §4.8, kestrel.md Item 3 memo point 2, kestrel.md Item 3 memo point 1, kestrel.md Item 2 §4.1 Band S, kestrel.md Item 1 Getting to a promise, kestrel.md Item 4 note reasons (refused), kestrel.md Item 4 code list row 6
- Expected: `no_promise` / `RF`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks []; transfers []
- Derivation: §4.1 + memo 1: days_late 28 -> Band S, latest = addbd(14 Oct, 5) = Wed 21 Oct; memo 2: two attempts in Band S. §4.8: attempt 1 = full 2100 on the next business day (Thu 15 Oct); attempt 2 = floor 700 (instalment_amount) on 21 Oct; the final-offer repeat is withdrawn. Both refused -> stop; Item 4: note refused with attempts made and last offer. Code list row 6: close no_promise / RF.
- Evaluated: deadline p1: addbd(today, 5) = 2026-10-21
- Confidence: Whether the initial 'no' or the refusal of the first proposal is counted as attempt 1, the last offer (700 on 21 Oct), the note and the close are the same; memo point 2 fixes the attempt limit at two.

### GEN-P-07 First create_promise fails: retry, confirm only after ok, no service_error note (promise/service fault retry, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 1 Read-back and recording (retry up to three tries, say recorded only after ok true), kestrel.md Item 2 §4.5 (agrees to the full amount), kestrel.md Item 2 §4.6 (today), kestrel.md Item 4 code list row 1
- Expected: `promise` / `PRM`; promises [{"product_id": "p1", "amount": 365.0, "date": "2026-10-14"}]; notes []; callbacks []; transfers []
- Derivation: §4.1: days_late 8 -> Band F, latest Wed 4 Nov; §4.5/§4.6: full amount 365 today -> accept. Mock fault: first create_promise fails; Item 1: try again, up to three tries; second try succeeds. Service_error note only if the third try also fails -> no note. Close promise / PRM.
- Evaluated: deadline p1: prev_bd(today + days(21)) = 2026-11-04; amount p1: product('p1')['past_due'] = 365; promise date p1: today = 2026-10-14
- Confidence: The retry rule and the ok:true condition are explicit; the fault only affects the first try.

### GEN-P-08 Three products, one named date beyond two latest dates; promises recorded, then the customer asks for a person (multi-product/one date for everything + transfer after promises, PUB-12, now 2026-10-14T11:00, confidence high)

- Rules: kestrel.md Item 1 Several products (one date for everything), kestrel.md Item 3 memo point 1, kestrel.md Item 2 §4.1 Bands F and S, kestrel.md Item 2 §4.6, kestrel.md Item 1 Other things customers say (asking for a person), kestrel.md Item 1 Several products (a transfer freezes the ledger), kestrel.md Item 4 code list row 4 and the note 'A transfer always closes with its transfer code'
- Expected: `transferred` / `TRH`; promises [{"product_id": "p1", "amount": 510.0, "date": "2026-10-21"}, {"product_id": "p2", "amount": 1320.0, "date": "2026-10-21"}, {"product_id": "p3", "amount": 140.0, "date": "2026-10-23"}]; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: §4.1 + memo 1: p1 and p2 days_late 16 -> Band S, latest addbd(14 Oct, 5) = Wed 21 Oct; p3 days_late 7 -> Band F, latest Wed 4 Nov. Item 1 several products: one named date (Fri 23 Oct) checked per product: p1, p2 latest earlier -> their own latest date, said in the read-back; p3 keeps 23 Oct (business day, not after latest). One read-back, create_promise x3 (510, 1320, 140), confirmation sentence once. Asking for a person -> transfer_to_agent general; transfer freezes the ledger, no notes; code list: transfer code wins over PRM -> transferred / TRH.
- Evaluated: script [[d('2026-10-23')]] = 2026-10-23; deadline p1: addbd(today, 5) = 2026-10-21; deadline p2: addbd(today, 5) = 2026-10-21; deadline p3: prev_bd(today + days(21)) = 2026-11-04; amount p1: product('p1')['past_due'] = 510; promise date p1: addbd(today, 5) = 2026-10-21; amount p2: product('p2')['past_due'] = 1320; promise date p2: addbd(today, 5) = 2026-10-21; amount p3: product('p3')['past_due'] = 140; promise date p3: d('2026-10-23') = 2026-10-23
- Confidence: The per-product latest-date rule and the 'transfer always closes with its transfer code' rule are explicit; the customer accepts whatever is read back.

## Valid but trimmed (cap of 20 cases)

- GEN-C-11 Customer asks for a real person after the arrears statement: transfer to general straight away, TRH
- GEN-C-14 Three products, customer says twice he does not want to talk after identity: refused note on every product, RF
- GEN-P-09 Hardship disclosed, transfer declined, customer volunteers the card floor on a Friday; loan noted hardship

