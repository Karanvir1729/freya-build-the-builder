# Generated practice cases: rationale

Written by `builder/cases.py` (independent case-writer call, claude-fable-5-1; dates evaluated by freyalib CAL_HELPERS). The building agent reads only the cases file, never this rationale.

## Calendar

Business weekdays: Monday, Tuesday, Wednesday, Thursday, Friday. Holidays: none.

- holidays not found in the brief and dropped: ['2026-10-19', '2026-11-12', '2026-12-09', '2026-12-25', '2026-12-28', '2027-01-01']

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
2026-10-30 Fri +12
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +13
2026-11-03 Tue +14
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
2026-10-30 Fri +10
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +11
2026-11-03 Tue +12
2026-11-04 Wed +13
2026-11-05 Thu +14
```

Business-day ladder from `now` = 2026-10-16T16:30:

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
2026-10-30 Fri +10
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +11
2026-11-03 Tue +12
2026-11-04 Wed +13
2026-11-05 Thu +14
```

## Outcome rows covered

- [x] `promise` / `-`
- [x] `paid` / `CLP`
- [x] `transferred` / `XRS`
- [x] `transferred` / `XHM`
- [x] `no_promise` / `RTP`
- [x] `no_promise` / `VUL`
- [x] `no_promise` / `DIS`
- [x] `no_promise` / `SYS`
- [x] `not_verified` / `NVF`
- [x] `not_verified` / `NVD`
- [x] `not_reached` / `CBB`
- [x] `not_reached` / `CBX`
- [x] `not_reached` / `WRN`
- [x] `not_reached` / `DCD`
- [x] `not_reached` / `UNK`

## Cases

### GEN-C-01 Unclear who answered after two asks (a question counts as the second ask) -> UNK (opening, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Opening, ashvale.md message 2.1 pre-security disclosure ban, Dialler outcome codes table (not_reached / UNK)
- Expected: `not_reached` / `UNK`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 2.1 Opening: only yes / speaking / that's me / own name confirms; 'who's calling?' and 'what's it about?' do not. 'If they ask something first, answer it and then ask again, and that ask is the second one' -> the ask after 'Who's calling?' is ask 2. Still unclear after ask 2 -> close as not reached (could not tell who answered) = not_reached / UNK. No get_account reached -> no notes.
- Evaluated: -
- Confidence: Message 2.1 fixes the two-ask limit and that an answered question counts as the second ask; the code table gives UNK.

### GEN-C-02 Husband offers to pay, then gives Friday 08:30 (2nd business day, start of new window) -> CBB (third_party, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Someone else answers, ashvale.md message 4.2 callback window (today or next two business days, 08:30-17:00 both ends included), ashvale.md message 2.1 pre-security disclosure ban, Dialler outcome codes table (not_reached / CBB)
- Expected: `not_reached` / `CBB`; promises []; notes []; callbacks [{"date": "2026-10-16", "time": "08:30"}]; transfers []
- Derivation: Message 2.1: relative cannot pay / be told anything; thank, say no, ask again when the customer is in. Message 4.2 (5 Oct, replaces the 09:00-19:00 next-business-day rule): callbacks today or either of the next two business days, 08:30-17:00 both ends included. Call Wed 14 Oct -> next two business days Thu 15, Fri 16; Friday 16 Oct 08:30 fits (second business day, lower bound included) -> schedule_callback(addbd(today,2), '08:30'), close not_reached / CBB.
- Evaluated: script [[weekday_after(today, 'Friday')]] = 2026-10-16; callback date: addbd(today, 2) = 2026-10-16
- Confidence: Message 4.2 is the latest decision and states both ends included and two business days ahead; the date and time are fixed by the script.

### GEN-C-03 Friday call: flatmate offers 19:00 then Charter Day Monday, both outside the window -> CBX (third_party, PUB-07, now 2026-10-16T11:00, confidence high)

- Rules: ashvale.md message 2.1 Someone else answers, ashvale.md message 4.2 callback window, ashvale.md Thread 1 holidays (Monday 19 October Charter Day), Dialler outcome codes table (not_reached / CBX)
- Expected: `not_reached` / `CBX`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 4.2: callbacks today (after now) or either of the next two business days, 08:30-17:00 inclusive; evening -> say the hours and ask once for another time. Call Fri 16 Oct 11:00: 19:00 today is after 17:00 -> does not fit. Next two business days are Tue 20 and Wed 21 Oct because Mon 19 Oct is Charter Day (Thread 1) -> Monday 10:00 does not fit. Second offer fails -> book nothing, close not_reached / CBX.
- Evaluated: script [[d('2026-10-19')]] = 2026-10-19
- Confidence: Both offered slots fall outside the message 4.2 window by the Thread 1 calendar; the brief says the second miss closes the call with no booking.

### GEN-C-04 Stranger says it is the wrong number -> WRN (third_party, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Someone else answers (wrong number), Dialler outcome codes table (not_reached / WRN)
- Expected: `not_reached` / `WRN`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 2.1: 'If they say it isn't the customer's number, close as not reached, wrong number.' Code table: not_reached / WRN. No get_account -> no notes.
- Evaluated: -
- Confidence: Single explicit rule with a single code.

### GEN-C-05 Daughter says the customer has died -> condolence sentence only, DCD (third_party, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Someone else answers (deceased), Dialler outcome codes table (not_reached / DCD)
- Expected: `not_reached` / `DCD`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 2.1: 'If they say the customer has died: "I'm very sorry for your loss.", nothing else, close as not reached, deceased.' Code table: not_reached / DCD.
- Evaluated: -
- Confidence: Explicit sentence and code; no customer choice.

### GEN-C-06 One wrong DOB then one wrong phone: second wrong answer in total ends the check -> NVF (identity, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 5.1 item 1 (second wrong answer in total ends the check, whatever wrong_answers_left says), ashvale.md message 2.1 Security (order, failed-check message), Dialler outcome codes table (not_verified / NVF)
- Expected: `not_verified` / `NVF`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 2.1: DOB first then phone last4, verify_identity after each answer; wrong DOB (1991) -> may be asked again -> correct. Message 5.1 item 1 (live 5 Oct, latest decision): 'the second wrong answer in total, whichever question it was on, ends the check, whatever wrong_answers_left says' -> wrong phone 8864 is wrong answer #2 -> check failed. Failed check (2.1): no subject disclosed, app-or-branch message, close not verified (failed) = not_verified / NVF. No get_account -> no notes.
- Evaluated: -
- Confidence: Message 5.1 explicitly overrides the three-wrong-answer allowance with a two-wrong limit across questions.

### GEN-C-07 Customer deflects the DOB question twice asking what it is about -> NVD (identity, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Security (won't answer: explain once; asks again what it's about -> declined), ashvale.md message 2.1 pre-security disclosure ban, Dialler outcome codes table (not_verified / NVD)
- Expected: `not_verified` / `NVD`; promises []; notes []; callbacks []; transfers []
- Derivation: Message 2.1 Security: 'If they won't answer, explain once that the questions are there to protect their account; if they still won't, or they ask again what it's about instead of answering, close as not verified (declined).' Code table: not_verified / NVD. Nothing disclosed before security passes. No get_account -> no notes.
- Evaluated: -
- Confidence: The brief gives one explanation then a declined close; the script repeats the deflection so no other path exists.

### GEN-C-08 Numeric DOB with day/month swapped hint, then 'already paid' on all three products -> paid CLP (special_topic, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Security (numeric date = day month year; day_month_swapped retry is not a wrong answer), ashvale.md message 2.1 Other things people say (already paid), ashvale.md message 2.1 Several products / Closing (every product noted paid -> paid), Dialler outcome codes table (paid / CLP)
- Expected: `paid` / `CLP`; promises []; notes [{"product_id": "p1", "reason": "paid"}, {"product_id": "p2", "reason": "paid"}, {"product_id": "p3", "reason": "paid"}]; callbacks []; transfers []
- Derivation: Message 2.1 Security: a date given only in numbers is day, month, year -> '06 03 1987' is sent as 1987-03-06 -> service hint day_month_swapped -> ask for the month as a word, retry not a wrong answer -> 1987-06-03 passes; phone 2288 passes. get_account, state all three products, ask the all-of-these-today question once. 'I've already paid': say the payments sentence, no promise on that product, note it paid -> all three noted paid. Closing: 'every product noted paid means close as paid' -> paid / CLP.
- Evaluated: -
- Confidence: The paid branch and close are explicit; even if the service counted the numeric date as one wrong answer, the check still passes (one wrong only) and the ledger is unchanged.

### GEN-C-09 Scam question at opening, then card disputed and loan 'already paid': close code from the first non-paid product -> DIS (special_topic, PUB-13, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Opening (asked if it's a scam), ashvale.md message 2.1 Other things people say (dispute; already paid), ashvale.md message 2.1 Closing (code for the first product in get_account order whose note isn't paid), Dialler outcome codes table (no_promise / DIS)
- Expected: `no_promise` / `DIS`; promises []; notes [{"product_id": "p1", "reason": "dispute"}, {"product_id": "p2", "reason": "paid"}]; callbacks []; transfers []
- Derivation: Message 2.1 Opening: scam question -> hang-up-and-ring advice, carry on; the re-ask gets 'speaking' -> confirmed. Security passes, get_account, both products stated. 'It's not mine': don't argue, no promise on p1, note dispute. p2 'already paid': payments sentence, note paid. Closing: not every product is noted paid, so no_promise with the code of the first product in get_account order whose note isn't paid = p1 dispute -> DIS.
- Evaluated: -
- Confidence: The closing rule in message 2.1 fixes the code order explicitly; the script gives no alternative path.

### GEN-C-11 Hardship disclosed, then customer insists on a person -> general transfer XHM (not support), no notes (special_topic, PUB-03, now 2026-10-14T11:00, confidence medium)

- Rules: ashvale.md message 5.1 item 2 (hardship stays with the assistant; a request for a person is a request for a person like any other), ashvale.md message 2.1 Other things people say (asking for a person: ask once, then general), ashvale.md message 2.1 Several products (no notes at all on a transferred call), Dialler outcome codes table (transferred / XHM)
- Expected: `transferred` / `XHM`; promises []; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: Message 5.1 item 2 (live 5 Oct, latest): hardship stays with the assistant, 'I'm sorry you're going through that.', no proposal; 'If they ask for a person, that is a request for a person like any other.' Message 2.1: asking for a person -> ask once whether the assistant can help first; if they insist, transfer_to_agent general, close as transferred -> code table transferred / XHM. Message 2.1: no notes at all on a transferred call, so no hardship note is expected.
- Evaluated: -
- Confidence: The queue and code are fixed by 5.1 and the code table; the doubt is whether an assistant that writes the hardship note before the person request is caught by 'none at all on a call that's transferred' - the brief says no notes on a transferred call, so none are expected.

### GEN-C-12 Bereavement hardship on two products, no transfer offer, customer declines any transfer -> VUL with hardship notes on both (special_topic, PUB-13, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 5.1 item 2 (hardship: two fixed sentences, no proposal, note every product hardship, close VUL), ashvale.md message 2.1 Hardship (nothing else on offer; date or amount named by the customer is logged as normal), Dialler outcome codes table (no_promise / VUL)
- Expected: `no_promise` / `VUL`; promises []; notes [{"product_id": "p1", "reason": "hardship"}, {"product_id": "p2", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Message 5.1 item 2 (1 Oct, live 5 Oct) replaces the support-transfer offer of 2.1: say 'I'm sorry you're going through that.', no proposal, 'Our Financial Support team will write to you within five working days.', note every product hardship, close no promise with code VUL. Customer names no date or amount, so nothing is logged. Code table v5: no_promise / VUL (HDS no longer exists).
- Evaluated: -
- Confidence: Message 5.1 is the latest dated decision on hardship and fixes sentences, notes and code; the script removes every ledger-changing choice.

### GEN-P-01 Early band: no to today, no date, accepts proposal 1 (full amount on 2nd business day) (promise, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Opening, ashvale.md message 2.1 Asking, ashvale.md message 2.1 Bands and latest dates (early band), ashvale.md message 2.1 Proposals, ashvale.md message 2.1 Read-back and logging, ashvale.md Dialler outcome codes table (promise)
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 540.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: p1 personal loan, days_late 5 -> early band (message 2.1), latest = call date + 18 calendar days, next business day if closed. Customer says no to today with no date/amount -> proposal 1: amount in play = full 540 on the 2nd business day after the call date (addbd(today,2)). Customer accepts, read-back, clear yes -> create_promise p1 540. Promise logged -> close promise, no reason (codes table). No note (product has a promise).
- Evaluated: deadline p1: next_bd(today + days(18)) = 2026-11-02; amount p1: product('p1')['past_due'] = 540; promise date p1: addbd(today, 2) = 2026-10-16
- Confidence: Message 2.1 fixes proposal 1 (full amount, 2nd business day) and the promise close; the customer has no ledger-changing choice.

### GEN-P-02 Customer names more than owed on a Saturday whose next business day is Charter Day: full amount on the Tuesday (promise, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Amounts (more than the full amount), ashvale.md message 2.1 Bands and latest dates (weekend/holiday moved to next business day), ashvale.md Thread 1 holidays (Charter Day 19 Oct), ashvale.md message 2.1 Read-back and logging
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 420.0, "date": "2026-10-19"}]; notes []; callbacks []; transfers []
- Derivation: p1 credit card ending 4821, days_late 6 -> early band, latest = next_bd(today+18d) = 2 Nov. Amount 500 > past_due 420 -> log the full amount 420 (message 2.1 Amounts). Date 17 Oct is a Saturday not after the latest date -> offer the next business day after it; 19 Oct is Charter Day (Thread 1) so that is Tue 20 Oct = next_bd_after(d('2026-10-17')). Customer accepts -> create_promise p1 420 on that day -> close promise.
- Evaluated: script [[d('2026-10-17')]] = 2026-10-17; deadline p1: next_bd(today + days(18)) = 2026-11-02; amount p1: product('p1')['past_due'] = 420; promise date p1: next_bd_after(d('2026-10-17')) = 2026-10-19
- Confidence: Both rules are explicit (over-amount -> full amount; weekend -> next business day after it, business days exclude bank holidays); the customer accepts the first alternative offered.

### GEN-P-03 Late band: refuses today, proposal 1 and proposal 2 (floor on the 5th business day) -> refused, RTP (promise, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.4 (late band latest date = 5th business day, proposal 2 on it), ashvale.md message 2.1 Proposals, ashvale.md message 2.1 Asking (never ask how much), ashvale.md message 2.1 Several products / notes (refused note), ashvale.md Dialler outcome codes table (no_promise RTP)
- Expected: `no_promise` / `RTP`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks []; transfers []
- Derivation: p1 personal loan, days_late 11 -> late band; message 2.4 (7 Oct, in force from 12 Oct) sets the latest date to the 5th business day after the call date = addbd(today,5) and proposal 2 on it. No to today without date/amount -> proposal 1: 310.50 on addbd(today,2); flat refusal -> proposal 2: floor (instalment 103.50) on addbd(today,5); refused -> proposals used up -> note p1 refused, close no_promise RTP.
- Evaluated: deadline p1: addbd(today, 5) = 2026-10-21
- Confidence: Two proposals in the late band and the refused close are fixed by messages 2.1 and 2.4; the customer refuses everything.

### GEN-P-04 Credit card: full amount too much -> floor is half the balance; 'next Friday' is after the late-band latest date -> latest date offered (promise, PUB-06, now 2026-10-14T11:00, confidence medium)

- Rules: ashvale.md message 2.3 (credit card floor = half the overdue balance or minimum payment if higher), ashvale.md message 2.1 Amounts (full amount too much -> floor once, 'The rest of the balance stays overdue.'), ashvale.md message 2.1 Bands and latest dates ('next Friday' definition; day after the latest date), ashvale.md message 2.4 (late band latest = 5th business day)
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 1062.55, "date": "2026-10-21"}]; notes []; callbacks []; transfers []
- Derivation: p1 credit card ending 1903, days_late 12 -> late band, latest = addbd(today,5) (message 2.4). Floor per message 2.3 = max(half of 2125.10 = 1062.55, minimum 637.50) = 1062.55. 'Full amount too much' -> floor offered once with the required sentence; amount in play becomes the floor. 'Next Friday' = Friday after the first Friday after today = 23 Oct, after the latest date -> assistant offers the latest date; customer accepts -> create_promise p1 1062.55 on addbd(today,5) -> close promise.
- Evaluated: deadline p1: addbd(today, 5) = 2026-10-21; amount p1: max(0.5 * product('p1')['past_due'], product('p1')['minimum_payment']) = 1062.55; promise date p1: addbd(today, 5) = 2026-10-21
- Confidence: The ledger values follow from messages 2.3, 2.4 and 2.1, but the persona must give the 'next Friday' line only after the floor is offered and then accept the latest date; the 'next Friday' rule and the floor arithmetic are explicit.

### GEN-P-05 Loan: amount below the floor on a past date -> floor offered once, day from today onwards asked; 'this Thursday' accepted (promise, PUB-05, now 2026-10-14T11:00, confidence medium)

- Rules: ashvale.md message 2.1 Amounts (less than the floor -> can't log, offer the floor once), ashvale.md message 2.1 Bands and latest dates (a day in the past; 'this <weekday>' = first one after today), ashvale.md message 2.3 (loan floor = instalment amount), ashvale.md message 2.1 Read-back and logging
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 260.0, "date": "2026-10-15"}]; notes []; callbacks []; transfers []
- Derivation: p1 personal loan, days_late 21 -> late band, latest = addbd(today,5). Floor = instalment 260 (message 2.3). 200 < floor -> 'can't log that', offer the floor once; customer takes it -> amount 260. Named date 12 Oct is before today -> ask for a day from today onwards; 'this Thursday' = first Thursday after today = weekday_after(today,'Thursday'), a business day not after the latest date -> create_promise p1 260 on it -> close promise.
- Evaluated: script [[d('2026-10-12')]] = 2026-10-12; deadline p1: addbd(today, 5) = 2026-10-21; amount p1: product('p1')['instalment_amount'] = 260; promise date p1: weekday_after(today, 'Thursday') = 2026-10-15
- Confidence: Both rules are explicit, but the assistant may handle the amount and the date in either order and the persona has to follow the matching branch of the script.

### GEN-P-06 Vague period ('end of the month') -> latest date proposed (18 days lands on a Sunday); create_promise fails once -> one try only, SYS (promise, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: ashvale.md message 2.1 Bands and latest dates (vague period: ask once, then propose the latest date; early band latest moved to next business day), ashvale.md message 4.2 (create_promise gets one try; failure sentence; service_error note; no promise, service failure), ashvale.md Dialler outcome codes table (no_promise SYS)
- Expected: `no_promise` / `SYS`; promises []; notes [{"product_id": "p1", "reason": "service_error"}]; callbacks []; transfers []
- Derivation: p1 credit card ending 7740, days_late 8 -> early band; latest = today+18 days = Sunday 1 Nov -> next business day Mon 2 Nov = next_bd(today+days(18)). 'End of the month' is a vague period -> ask once for the exact day; still none -> propose the latest date with the amount in play (full 365). Customer accepts; create_promise fails (mock fault) -> message 4.2: one try only, failure sentence, note p1 service_error, close no_promise SYS.
- Evaluated: deadline p1: next_bd(today + days(18)) = 2026-11-02
- Confidence: Message 4.2 (5 Oct) replaces the retry rule of 2.1; the vague-period rule and the early-band latest date are explicit; the ledger has no promise.

### GEN-P-07 Three products: promise on the card changed at the read-back to Charter Day (moved to Tuesday), loan disputed, car loan refused (promise, PUB-12, now 2026-10-14T11:00, confidence medium)

- Rules: ashvale.md message 2.1 Several products (all stated, one all-of-these question, one at a time, one read-back, create_promise per product), ashvale.md message 2.1 Read-back and logging (change at the read-back -> check again, read back again), ashvale.md message 2.1 Bands and latest dates (bank holiday -> next business day after it), ashvale.md message 2.1 Other things people say (not mine -> dispute note), ashvale.md message 2.1 Proposals (early band: one proposal, then refused), ashvale.md message 2.1 Closing (promise logged -> promise close)
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 510.0, "date": "2026-10-20"}]; notes [{"product_id": "p2", "reason": "dispute"}, {"product_id": "p3", "reason": "refused"}]; callbacks []; transfers []
- Derivation: p1 card days_late 16 and p2 loan 16 -> late band, latest addbd(today,5); p3 car loan 7 -> early band, latest next_bd(today+18d). No to all-today -> per product from proposal 1: p1 proposal 1 = 510 on addbd(today,2) accepted; p2 'not mine' -> dispute note, no promise; p3 proposal 1 refused, early band has one proposal -> refused note. At the read-back the customer changes p1 to 19 Oct = Charter Day, not after the latest date -> next business day after it = 20 Oct; re-read-back, yes -> create_promise p1 510 on next_bd_after(d('2026-10-19')). A promise was logged -> close promise, no reason.
- Evaluated: script [[d('2026-10-19')]] = 2026-10-19; deadline p1: addbd(today, 5) = 2026-10-21; deadline p2: addbd(today, 5) = 2026-10-21; deadline p3: next_bd(today + days(18)) = 2026-11-02; amount p1: product('p1')['past_due'] = 510; promise date p1: next_bd_after(d('2026-10-19')) = 2026-10-20
- Confidence: Every value is fixed by message 2.1 (dispute note, one early-band proposal, holiday moved to the next business day, promise close), but the persona must follow a long multi-product script and react to the read-back correctly.

### GEN-P-08 Hardship (job loss) under the Compliance rule: no proposal, no transfer, Financial Support letter; customer still names floor amount and a date on the card (promise, PUB-13, now 2026-10-14T11:00, confidence medium)

- Rules: ashvale.md message 5.1 Hardship (in force from 5 Oct: no proposal, letter sentence, hardship notes, VUL, named date/amount logged as normal), ashvale.md message 5.2, ashvale.md message 2.3 (credit card floor = half the overdue balance), ashvale.md message 2.1 Closing (promise logged -> promise close), ashvale.md message 2.1 Several products (notes on products without a promise)
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 150.0, "date": "2026-10-16"}]; notes [{"product_id": "p2", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Message 5.1 (1 Oct, live 5 Oct, confirmed 5.2) replaces the hardship handling of 2.1: sorry sentence, no proposal, letter sentence, no transfer, hardship notes, VUL; a date or amount the customer names is still logged as normal. p1 card days_late 4 -> early band, floor = max(150, 90) = 150; 150 on Fri 16 Oct is at the floor, a business day, not after the latest date -> create_promise p1 150 on d('2026-10-16'). p2: no date/amount -> ends without a promise -> note hardship. A promise was logged -> close promise (2.1 Closing: 'A promise logged on the call means a promise close').
- Evaluated: script [[d('2026-10-16')]] = 2026-10-16; deadline p1: next_bd(today + days(18)) = 2026-11-02; deadline p2: addbd(today, 5) = 2026-10-21; amount p1: 150 = 150; promise date p1: d('2026-10-16') = 2026-10-16
- Confidence: Message 5.1 says 'notes every product as hardship' while 2.1 restricts notes to products ending without a promise; the expected ledger follows 2.1's definition (note on p2 only). The promise close is fixed by 2.1 Closing.

### GEN-P-09 Friday call before Charter Day: proposal 1 on the 2nd business day (Wednesday) logged, then a payment-plan request -> restructuring transfer, promise stays (promise, PUB-04, now 2026-10-16T16:30, confidence high)

- Rules: ashvale.md message 2.1 Proposals (2nd business day after the call date), ashvale.md Thread 1 holidays (Charter Day 19 Oct), ashvale.md message 2.4 (late band latest = 5th business day), ashvale.md message 2.1 Other things people say (asking for a plan -> restructuring transfer, describe nothing), ashvale.md message 2.1 Several products / Closing (transferred call: no notes, logged promises stay, close is the transfer), ashvale.md Dialler outcome codes table (transferred XRS)
- Expected: `transferred` / `XRS`; promises [{"product_id": "p1", "amount": 1250.0, "date": "2026-10-20"}]; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: now is Friday 16 Oct 16:30. p1 car loan days_late 14 -> late band, latest = addbd(today,5) = 26 Oct (message 2.4). No to today without date/amount -> proposal 1: 1250 on the 2nd business day after the call date = addbd(today,2) = Wed 21 Oct (Sat, Sun and Charter Day skipped). Accepted and logged -> promise stays. Request for a plan -> describe nothing, transfer_to_agent restructuring; call transferred after the promise -> close transferred XRS (2.1 Closing); no notes on a transferred call.
- Evaluated: deadline p1: addbd(today, 5) = 2026-10-23; amount p1: product('p1')['past_due'] = 1250; promise date p1: addbd(today, 2) = 2026-10-20
- Confidence: Message 2.1 states that a transfer after a logged promise makes the close the transfer and that transferred calls carry no notes while logged promises stay; the 2nd-business-day arithmetic is fixed by the People Team calendar.

## Valid but trimmed (cap of 20 cases)

- GEN-C-10 Robot question at opening, then a payment-plan request -> restructuring transfer, XRS, no notes
- GEN-C-13 After security, customer says twice they don't want to talk -> refused note on all three products, RTP
- GEN-C-14 create_promise fails on the single allowed try -> no retry, service_error note, SYS

