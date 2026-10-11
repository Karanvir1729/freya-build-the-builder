# Generated practice cases: rationale

Written by `builder/cases.py` (independent case-writer call, claude-opus-5-5; dates evaluated by freyalib CAL_HELPERS). The building agent reads only the cases file, never this rationale.

## Calendar

Business weekdays: Monday, Tuesday, Wednesday, Thursday, Friday. Holidays: 2026-10-22, 2026-11-24, 2026-12-25, 2026-12-28.

- holidays not found in the brief and dropped: ['2026-11-06']

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
2026-10-22 Thu -- holiday
2026-10-23 Fri +6
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +7
2026-10-27 Tue +8
2026-10-28 Wed +9
2026-10-29 Thu +10
2026-10-30 Fri +11
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
2026-10-22 Thu -- holiday
2026-10-23 Fri +4
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +5
2026-10-27 Tue +6
2026-10-28 Wed +7
2026-10-29 Thu +8
2026-10-30 Fri +9
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +10
2026-11-03 Tue +11
2026-11-04 Wed +12
2026-11-05 Thu +13
2026-11-06 Fri +14
```

Business-day ladder from `now` = 2026-10-20T11:00:

```
2026-10-20 Tue today
2026-10-21 Wed +1
2026-10-22 Thu -- holiday
2026-10-23 Fri +2
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +3
2026-10-27 Tue +4
2026-10-28 Wed +5
2026-10-29 Thu +6
2026-10-30 Fri +7
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +8
2026-11-03 Tue +9
2026-11-04 Wed +10
2026-11-05 Thu +11
2026-11-06 Fri +12
2026-11-07 Sat -- not a business day
2026-11-08 Sun -- not a business day
2026-11-09 Mon +13
2026-11-10 Tue +14
```

Business-day ladder from `now` = 2026-10-21T11:00:

```
2026-10-21 Wed today
2026-10-22 Thu -- holiday
2026-10-23 Fri +1
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon +2
2026-10-27 Tue +3
2026-10-28 Wed +4
2026-10-29 Thu +5
2026-10-30 Fri +6
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +7
2026-11-03 Tue +8
2026-11-04 Wed +9
2026-11-05 Thu +10
2026-11-06 Fri +11
2026-11-07 Sat -- not a business day
2026-11-08 Sun -- not a business day
2026-11-09 Mon +12
2026-11-10 Tue +13
2026-11-11 Wed +14
```

## Outcome rows covered

- [x] `promise` / `FULLPTP`
- [x] `promise` / `PARTPTP`
- [x] `paid` / `CLMPD`
- [x] `transferred` / `XRST`
- [x] `transferred` / `XGEN`
- [x] `transferred` / `XCARE`
- [x] `no_promise` / `TDN`
- [x] `no_promise` / `TDN2L`
- [x] `no_promise` / `HDNX`
- [x] `no_promise` / `DSPT`
- [ ] NOT COVERED `no_promise` / `SYSF`
- [x] `not_verified` / `IDNO`
- [x] `not_verified` / `IDREF`
- [x] `not_reached` / `TPCB`
- [x] `not_reached` / `NOCON`

## Cases

### GEN-C-01 Unclear first answer, then the customer declines the security questions and asks what it is about (opening_identity, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Opening, Doc1 What nobody hears before the security questions, Doc1 Security questions (refusal), Doc4 IDREF row
- Expected: `not_verified` / `IDREF`; promises []; notes []; callbacks []; transfers []
- Derivation: Doc1 Opening: 'Hello?' is not a confirmation, so the agent asks again; 'Yes, speaking' confirms. Doc1 Security questions: on the refusal the agent explains once; when the customer asks again what it is about, the call closes as not verified (declined), which is the IDREF row. No get_account, so no notes.
- Evaluated: -
- Confidence: Doc1 says asking what the call is about instead of answering closes as declined (IDREF). No ledger choice is left.

### GEN-C-02 Flatmate on a Friday names a Saturday slot and turns down the proposed Monday slot (third_party, PUB-08, now 2026-10-16T11:00, confidence high)

- Rules: Doc1 Someone else picks up, AHS-5 5.6a, Doc4 NOCON row
- Expected: `not_reached` / `NOCON`; promises []; notes []; callbacks []; transfers []
- Derivation: AHS-5 5.6a: the window is the next business day after a Friday (Monday) or the one after that. Tomorrow (Saturday) is outside the window, so the agent proposes the same time on the first business day in the window: next_bd_after(today) at 15:00, once. The flatmate turns it down, so nothing is booked and the call closes not reached / NOCON.
- Evaluated: -
- Confidence: Doc1 says that if the proposal is turned down, nothing is booked. The ledger is fixed.

### GEN-C-03 Mother offers to pay; asks for a callback tomorrow, which is a closure day; accepts the next valid slot (third_party, PUB-01, now 2026-10-21T11:00, confidence high)

- Rules: Doc1 Someone else picks up, AHS-5 5.6a, AHS-5 5.1, Doc4 TPCB row
- Expected: `not_reached` / `TPCB`; promises []; notes []; callbacks [{"date": "2026-10-23", "time": "14:00"}]; transfers []
- Derivation: Doc1: a relative cannot arrange anything, so the agent declines. AHS-5 5.1/minutes: 2026-10-22 is a closure day, so tomorrow is outside the 5.6a window. The agent proposes the same time on the first business day in the window, next_bd_after(today), at 14:00. She accepts, so schedule_callback is booked and the call closes not_reached / TPCB.
- Evaluated: callback date: next_bd_after(today) = 2026-10-23
- Confidence: 5.6a gives a single proposal (the same time on the first business day in the window), and the relative accepts it.

### GEN-C-04 Date of birth wrong twice: the per-question limit ends the check before the service limit (identity, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions, Doc3 item 6, Doc4 IDNO row
- Expected: `not_verified` / `IDNO`; promises []; notes []; callbacks []; transfers []
- Derivation: Doc1 / minutes item 6: one retry per question, so a second wrong answer to the same question ends the check even though the service would still allow one more. Close not_verified / IDNO. There is no get_account, so no notes, and create_promise is never reached (the fault does not matter).
- Evaluated: -
- Confidence: The per-question rule is explicit and was confirmed in the minutes.

### GEN-C-05 Numeric date of birth triggers the day_month_swapped hint, then the customer disputes the loan (identity_then_dispute, PUB-07, now 2026-10-14T11:00, confidence medium)

- Rules: Doc1 Security questions (day_month_swapped), Doc1 Things customers say: not mine, Doc1 Notes, Doc4 DSPT row
- Expected: `no_promise` / `DSPT`; promises []; notes [{"product_id": "p1", "reason": "dispute"}]; callbacks []; transfers []
- Derivation: Doc1: a numeric date is read day-month-year, giving 1975-05-12. The service hints day_month_swapped, so the agent asks again with the month as a word, and 1975-12-05 passes. 'Not mine' gives a dispute: no arrangement, one add_note dispute on p1, close no_promise / DSPT.
- Evaluated: -
- Confidence: The path depends on the mock returning the swapped hint for the day-first reading; the ledger itself is fixed by the dispute rule.

### GEN-C-06 Robot and scam questions, then both products claimed as already paid (already_paid, PUB-13, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Opening (robot, scam), AHS-5 5.9, Doc1 Things customers say: already paid, Doc4 CLMPD row
- Expected: `paid` / `CLMPD`; promises []; notes [{"product_id": "p2", "reason": "paid"}, {"product_id": "p1", "reason": "paid"}]; callbacks []; transfers []
- Derivation: Doc1 Opening: the robot and scam answers are fixed lines, and the call continues. AHS-5 5.9: p2 (20 days late) is taken before p1 (4 days). Already paid gives no arrangement and an add_note paid on each product with the method and date. Every product is claimed paid, so the outcome is paid / CLMPD.
- Evaluated: -
- Confidence: The code card says that if every product is claimed paid, the code is CLMPD.

### GEN-C-07 Card paid in full today and recorded, then the customer asks for a payment plan on the loan (transfer_restructuring, PUB-12, now 2026-10-14T11:00, confidence medium)

- Rules: AHS-5 5.9, Doc1 Read-back, Doc1 Things customers say: plan, Doc1 Notes (transfer freezes), Doc4 XRST row
- Expected: `transferred` / `XRST`; promises [{"product_id": "p1", "amount": 510.0, "date": "2026-10-14"}]; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: 5.9: p1 and p2 are both 16 days late, so the system order holds, then p3 (7 days). The full card payment today falls within the Middle band last date addbd(today,4) (minutes item 3), so a promise of past_due today is recorded. A plan request is a transfer to restructuring; a transfer freezes everything, the recorded promise stays, and there are no notes on p2/p3. Outcome transferred / XRST.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 510; promise date p1: today = 2026-10-14
- Confidence: The ledger is fixed by Doc1 (the transfer freezes the ledger, the recorded arrangement stays); the only doubt is the persona's split answer to the combined question.

### GEN-C-08 Customer wants a person and repeats it after the one check question (transfer_general, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Things customers say: wants a person, Doc4 XGEN row
- Expected: `transferred` / `XGEN`; promises []; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: Doc1: the agent asks once; on 'no' it transfers to queue general. The transfer freezes the ledger (no notes). Outcome transferred / XGEN.
- Evaluated: -
- Confidence: An explicit rule, with no choice left.

### GEN-C-09 Job loss: no attempt, put through to Customer Care (hardship_transfer, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Things customers say: hardship, Doc4 XCARE row
- Expected: `transferred` / `XCARE`; promises []; notes []; callbacks []; transfers [{"queue": "support"}]
- Derivation: Doc1 hardship: say the sympathy line, make no attempt, and transfer to support. The transfer freezes the ledger (no notes). Outcome transferred / XCARE.
- Evaluated: -
- Confidence: An explicit rule; the customer accepts the transfer.

### GEN-C-10 One wrong answer on each security question still passes; bereavement, Customer Care declined, three products (hardship_declined, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions (per question), Doc1 Things customers say: hardship, Doc1 Notes, Doc4 HDNX row
- Expected: `no_promise` / `HDNX`; promises []; notes [{"product_id": "p1", "reason": "hardship"}, {"product_id": "p2", "reason": "hardship"}, {"product_id": "p3", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Doc1: one wrong answer per question with right repeats is a pass (two wrong in total, under the service limit). Hardship with Customer Care declined: add_note hardship on every product (p1, p2, p3) with her words, no second look. Outcome no_promise / HDNX.
- Evaluated: -
- Confidence: Both rules are explicit; the persona offers nothing that would make an arrangement.

### GEN-C-11 Verified customer twice says he does not want to talk: refused note, no second look (does_not_want_to_talk, PUB-02, now 2026-10-14T11:00, confidence medium)

- Rules: Doc1 Things customers say: does not want to talk, Doc1 Second look (not for someone who does not want to talk), Doc1 Notes, Doc4 TDN row
- Expected: `no_promise` / `TDN`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks []; transfers []
- Derivation: Doc1: after the security questions, a repeated 'does not want to talk' closes with no arrangement, a refused note on every product still open (p1) and no second look. The code card row 'customer would not continue after the security questions' gives no_promise / TDN.
- Evaluated: -
- Confidence: An agent could read the first 'don't want to talk' as a ladder refusal; Doc1 treats it as its own branch. The ledger follows the explicit branch.

### GEN-P-01 Late band on a Friday: refuse both attempts, then a second-look call booked after one time outside the hours (promise, PUB-09, now 2026-10-16T11:00, confidence high)

- Rules: AHS-5 5.3, AHS-5 5.4 part-payment last date, AHS-5 5.5, AHS-5 5.7, Doc1 Second look, Doc1 Notes, Doc4 TDN2L
- Expected: `no_promise` / `TDN2L`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks [{"date": "2026-10-21", "time": "17:30"}]; transfers []
- Derivation: days_late 28 -> Late band, 2 attempts (5.3). Attempt 1: full 2100 on addbd(today,1)=Mon 19; attempt 2: floor instalment 700 on min(addbd(today,2), addbd(today,3))=Tue 20 (5.4, 5.5). Both refused -> turned down, note refused. Second look on addbd(today,3) (Wed 21), 11:00 outside 12-18 so hours said, 17:30 booked (5.7). No arrangement + second look -> no_promise TDN2L.
- Evaluated: deadline p1: addbd(today, 3) = 2026-10-21; callback date: addbd(today, 3) = 2026-10-21
- Confidence: Late-band ladder, part-payment last date and second-look window are all fixed numbers; the customer refuses every offer and gives one in-hours time on the second ask.

### GEN-P-02 Early band: 'this Saturday' moved to the next business day (promise, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: AHS-5 5.2, AHS-5 5.6 weekend row, AHS-5 5.3 Early, Doc1 Read-back, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 540.0, "date": "2026-10-19"}]; notes []; callbacks []; transfers []
- Derivation: 5.2: 'this Saturday' on Wed 14 = Sat 17 (current week, still to come). Early last date = next_bd(today+14)=Wed 28; Sat 17 is before it but a weekend -> first business day after = Mon 19 (5.6). Full 540 -> promise FULLPTP.
- Evaluated: deadline p1: next_bd(today + days(14)) = 2026-10-28; amount p1: product('p1')['past_due'] = 540; promise date p1: next_bd(weekday_in_week(today, 'Saturday')) = 2026-10-19
- Confidence: 5.2 defines 'this <weekday>' and 5.6 the weekend move explicitly; the customer accepts the only correct proposal.

### GEN-P-03 Middle band (new 4th-business-day limit): 'next Friday' beyond the last date, refused, then the floor on the part-payment last date (promise, PUB-04, now 2026-10-14T11:00, confidence medium)

- Rules: Doc3 item 3, AHS-5 5.2 next weekday, AHS-5 5.6 later-than-last-date row, AHS-5 5.5, AHS-5 5.4, Doc4 PARTPTP
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 400.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: days_late 14 -> Middle; minutes item 3: last date addbd(today,4)=Tue 20. 'Next Friday' = Fri 23 (following week, 5.2) > last date -> offer last date; refused = attempt 1 (5.6). Attempt 2: floor instalment 400 on min(addbd(today,2), last)=Fri 16 -> accepted -> PARTPTP.
- Evaluated: deadline p1: min(addbd(today, 2), addbd(today, 4)) = 2026-10-16; amount p1: product('p1')['instalment_amount'] = 400; promise date p1: min(addbd(today, 2), addbd(today, 4)) = 2026-10-16
- Confidence: 5.6 says the refused last-date offer counts as an attempt; an agent could instead re-offer attempt 1 of the ladder, but the brief forbids re-offering a turned-down offer, so attempt 2 (floor) is next.

### GEN-P-04 Card amount between the old minimum payment and the new half-of-overdue floor (amount, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: Doc3 item 2, AHS-5 5.4 less-than-floor row, AHS-5 5.4 part-payment last date, AHS-5 5.2 tomorrow, Doc4 PARTPTP
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 210.0, "date": "2026-10-15"}]; notes []; callbacks []; transfers []
- Derivation: Minutes item 2: card floor = ceil(420/2 to multiple of 5)=210 (not minimum_payment 126). 150 < floor -> offer floor once (5.4); accepted -> part payment, last date min(addbd(today,2), Early last Wed 28)=Fri 16. 'Tomorrow' = Thu 15, business day within limit -> accept. PARTPTP.
- Evaluated: deadline p1: min(addbd(today, 2), next_bd(today + days(14))) = 2026-10-16; amount p1: min(ceil(product('p1')['past_due'] / 2 / 5) * 5, product('p1')['past_due']) = 210; promise date p1: today + days(1) = 2026-10-15
- Confidence: The minutes replace the card floor explicitly from go-live (14 October); 150 is unambiguously below 210 and tomorrow is within the part-payment limit.

### GEN-P-05 Vague 'end of next week', last date proposed, first create_promise fails and the retry succeeds (service_fault, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: AHS-5 5.6 vague row, Doc3 item 3, AHS-5 5.8, Doc1 Read-back, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 365.0, "date": "2026-10-20"}]; notes []; callbacks []; transfers []
- Derivation: days_late 8 -> Middle, last date addbd(today,4)=Tue 20 (minutes item 3). Vague period -> ask once, none -> propose last date (5.6). PUB-10 fault: first create_promise fails, one retry allowed (5.8, Doc1) and succeeds -> promise FULLPTP.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 365; promise date p1: addbd(today, 4) = 2026-10-20
- Confidence: Vague-period and retry rules are explicit; the fault fails only the first call so the retry records the promise.

### GEN-P-06 Three products: card too much -> new floor on 'Friday', loan refused on both attempts, car loan full; second look still offered (multi_product, PUB-12, now 2026-10-14T11:00, confidence medium)

- Rules: AHS-5 5.9, Doc3 item 2, Doc3 item 3, AHS-5 5.4 too-much row, AHS-5 5.5, AHS-5 5.2 weekday on its own, AHS-5 5.7, Doc1 Second look, Doc4 PARTPTP
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 255.0, "date": "2026-10-16"}, {"product_id": "p3", "amount": 140.0, "date": "2026-10-28"}]; notes [{"product_id": "p2", "reason": "refused"}]; callbacks [{"date": "2026-10-19", "time": "15:00"}]; transfers []
- Derivation: 5.9: p1 and p2 both 16 days keep listed order, then p3 (7). p1 too much -> floor ceil(255)=255 (minutes 2) on 'Friday' = Fri 16 = part last date min(addbd 2, addbd 4). p2 Middle: full 1320 on addbd(today,4), then 440 on addbd(today,2), both refused -> note refused. p3 Early full 140 on next_bd(today+14)=Wed 28. Turned-down product -> second look addbd(today,3) 15:00. A part arrangement exists -> promise PARTPTP.
- Evaluated: script [[next_bd(today + days(14))]] = 2026-10-28; deadline p1: min(addbd(today, 2), addbd(today, 4)) = 2026-10-16; deadline p2: addbd(today, 4) = 2026-10-20; deadline p3: next_bd(today + days(14)) = 2026-10-28; amount p1: min(ceil(product('p1')['past_due'] / 2 / 5) * 5, product('p1')['past_due']) = 255; promise date p1: weekday_in_week(today, 'Friday') = 2026-10-16; amount p3: product('p3')['past_due'] = 140; promise date p3: next_bd(today + days(14)) = 2026-10-28; callback date: addbd(today, 3) = 2026-10-19
- Confidence: Doc1 ties the second-look offer to a turned-down product, not to a call with no promises, but an agent could read it as only for calls without arrangements; the customer accepts so the callback is in the ledger.

### GEN-P-07 Hardship, Customer Care declined, then the customer names a date and amount for the card (hardship, PUB-13, now 2026-10-14T11:00, confidence medium)

- Rules: Doc1 Things customers say (hardship), AHS-5 5.9, AHS-5 5.3 Early, Doc1 Notes, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 300.0, "date": "2026-10-23"}]; notes [{"product_id": "p2", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Hardship: no attempts, transfer offered and declined -> hardship note on products without arrangement (p2). Customer's own offer is a normal arrangement: p1 Early, last date next_bd(today+14)=Wed 28; Fri 23 is a business day within it -> 300 recorded. One full arrangement -> promise FULLPTP.
- Evaluated: script [[d('2026-10-23')]] = 2026-10-23; deadline p1: next_bd(today + days(14)) = 2026-10-28; amount p1: product('p1')['past_due'] = 300; promise date p1: d('2026-10-23') = 2026-10-23
- Confidence: Doc1 says hardship notes go on every product, then that a self-offered date is a normal arrangement; whether the card also gets a hardship note is a reading question, but the Notes rule gives notes only to products ending without an arrangement.

### GEN-P-08 Read-back correction to a day beyond the Middle last date, then a restructuring transfer after the recorded promise (combination, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Read-back, AHS-5 5.6 later-than-last-date row, Doc3 item 3, AHS-5 5.9, Doc1 restructuring, Doc1 Notes (transfer freezes), Doc4 XRST
- Expected: `transferred` / `XRST`; promises [{"product_id": "p1", "amount": 220.0, "date": "2026-10-20"}]; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: p1 and p2 both 9 days (Middle, keep order), p3 3 days last. p1 last date addbd(today,4)=Tue 20; Mon 19 named, changed at read-back to Wed 21 > last -> offer Tue 20, accepted, recorded 220. p2 asks for a plan -> transfer restructuring; transfer freezes: no notes, p1 promise stays -> transferred XRST.
- Evaluated: script [[addbd(today, 3)]] = 2026-10-19; script [[d('2026-10-21')]] = 2026-10-21; deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 220; promise date p1: addbd(today, 4) = 2026-10-20
- Confidence: Read-back change, last-date limit and transfer freeze are all explicit; the customer accepts the only offered date.

### GEN-P-09 Late band: a date before today, then St Corran's Day moved to the next business day (date, PUB-05, now 2026-10-20T11:00, confidence high)

- Rules: AHS-5 5.6 day-before-today row, AHS-5 5.6 closure-day row, AHS-5 5.1, AHS-5 5.3 Late, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 780.0, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: days_late 21 -> Late, last date addbd(today,3) from Tue 20 = Mon 26 (22 is a closure day). 19 Oct is before today -> ask again (5.6). 22 Oct closure day within limit -> first business day after = Fri 23 <= Mon 26 -> accepted. Full 780 -> FULLPTP.
- Evaluated: script [[d('2026-10-19')]] = 2026-10-19; script [[d('2026-10-22')]] = 2026-10-22; deadline p1: addbd(today, 3) = 2026-10-26; amount p1: product('p1')['past_due'] = 780; promise date p1: next_bd(d('2026-10-22')) = 2026-10-23
- Confidence: Both 5.6 rows are explicit and 22 October is a listed closure day not changed by the minutes.

## Valid but trimmed (cap of 20 cases)

- GEN-C-12 Middle-band card: ladder runs out over a closure day, new card floor, second-look time outside the hours once

