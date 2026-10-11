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

Business-day ladder from `now` = 2026-10-21T17:30:

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

Business-day ladder from `now` = 2026-11-05T11:00:

```
2026-11-05 Thu today
2026-11-06 Fri +1
2026-11-07 Sat -- not a business day
2026-11-08 Sun -- not a business day
2026-11-09 Mon +2
2026-11-10 Tue +3
2026-11-11 Wed +4
2026-11-12 Thu +5
2026-11-13 Fri +6
2026-11-14 Sat -- not a business day
2026-11-15 Sun -- not a business day
2026-11-16 Mon +7
2026-11-17 Tue +8
2026-11-18 Wed +9
2026-11-19 Thu +10
2026-11-20 Fri +11
2026-11-21 Sat -- not a business day
2026-11-22 Sun -- not a business day
2026-11-23 Mon +12
2026-11-24 Tue -- holiday
2026-11-25 Wed +13
2026-11-26 Thu +14
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

### GEN-C-01 Sister offers to pay, then turns down the in-window slot: no callback, NOCON (third_party, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Someone else picks up, AHS-5 5.6a, Doc4 NOCON row
- Expected: `not_reached` / `NOCON`; promises []; notes []; callbacks []; transfers []
- Derivation: Doc1 third party + AHS-5 5.6a: window = next_bd_after(today) (Thu 15 Oct) or the business day after that (Fri 16 Oct), 10:00-16:00. Monday 19 Oct is outside it, so the assistant proposes the same time on the first day in the window, once. The sister refuses, so nothing is booked -> not_reached NOCON ('someone else answered and no callback booked'). A relative cannot arrange anything, so there are no promises or notes (get_account is never reached).
- Evaluated: -
- Confidence: Doc1 and AHS-5 5.6a both say: propose once, book nothing if refused. The NOCON row covers 'no callback booked'. No ambiguity.

### GEN-C-02 Wife asks for 'tomorrow' on the eve of St Corran's Day: callback moved to the Friday, TPCB (third_party, PUB-07, now 2026-10-21T17:30, confidence high)

- Rules: Doc1 Someone else picks up, AHS-5 5.6a, AHS-5 5.1, Doc4 TPCB row
- Expected: `not_reached` / `TPCB`; promises []; notes []; callbacks [{"date": "2026-10-23", "time": "14:00"}]; transfers []
- Derivation: AHS-5 5.1: 2026-10-22 is a closure day. 5.6a: the window is next_bd_after(today) = Fri 23 Oct, or the business day after that (Mon 26 Oct), 10:00-16:00. 'Tomorrow' (22 Oct) does not fit, so the assistant proposes the same time (14:00) on the first business day in the window = next_bd_after(today). The wife accepts -> book it -> TPCB.
- Evaluated: callback date: next_bd_after(today) = 2026-10-23
- Confidence: 5.6a fixes the replacement slot (same time, first business day in the window). The closure day is listed in AHS-5 and the minutes do not change it.

### GEN-C-03 Date of birth wrong twice: check ends after the first question, IDNO (identity, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions, Doc3 item 6, Doc4 IDNO row
- Expected: `not_verified` / `IDNO`; promises []; notes []; callbacks []; transfers []
- Derivation: Doc1 security questions (confirmed by Doc3 item 6): each question may be answered wrongly once; a second wrong answer to the same question ends the check. 1990-10-09 is wrong twice (the real date is 1990-09-09, and a day-month swap of the answer does not match it) -> check ends -> not_verified IDNO. Nothing is recorded.
- Evaluated: -
- Confidence: The per-question rule is explicit and the minutes reaffirm it. The service's limit of three is deliberately looser.

### GEN-C-04 Refuses the date of birth, then asks what it is about: IDREF (identity, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions, Doc1 What nobody hears before the security questions, Doc4 IDREF row
- Expected: `not_verified` / `IDREF`; promises []; notes []; callbacks []; transfers []
- Derivation: Doc1: if the customer will not answer, say once that the questions protect his personal details; if instead of answering he asks again what it is about, close as not verified (declined) -> IDREF row ('customer would not answer the security questions').
- Evaluated: -
- Confidence: Doc1 names the deflection case explicitly, and the code card has a dedicated IDREF row.

### GEN-C-05 Unclear 'Hello?' first, then confirmed; customer has already paid: CLMPD (special_topic, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Opening, Doc1 Things customers say: already paid, Doc1 Notes, Doc4 CLMPD row
- Expected: `paid` / `CLMPD`; promises []; notes [{"product_id": "p1", "reason": "paid"}]; callbacks []; transfers []
- Derivation: Doc1 opening: 'Hello?' does not count, so the assistant asks again; 'Yes, speaking' counts. Already paid -> the set sentence, no arrangement, add_note paid (how and when). This is the only product and it is claimed paid -> CLMPD. No second look is offered (it is not a turned-down product).
- Evaluated: -
- Confidence: Each step is spelled out in Doc1 and the code card.

### GEN-C-06 Loan turned down after 2 attempts, card disputed, second look declined: DSPT outranks TDN (special_topic, PUB-13, now 2026-10-14T11:00, confidence high)

- Rules: AHS-5 5.9, AHS-5 5.5, Doc3 item 3, Doc1 Second look, Doc1 Things customers say: dispute, Doc4 several-products precedence, Doc4 DSPT row
- Expected: `no_promise` / `DSPT`; promises []; notes [{"product_id": "p2", "reason": "refused"}, {"product_id": "p1", "reason": "dispute"}]; callbacks []; transfers []
- Derivation: 5.9: p2 (20 days late) comes before p1 (4 days late). p2 is in the Middle band, so its last date is addbd(today,4) (Doc3 item 3). Ladder: attempt 1 = full 900 on that date; attempt 2 = floor 300 on min(addbd(today,2), last date). Two flat no's -> turned down -> refused note. p1 is disputed -> dispute note. The second look is declined. Nothing is recorded -> precedence SYSF > HDNX > DSPT > TDN2L > TDN -> DSPT.
- Evaluated: deadline p2: addbd(today, 4) = 2026-10-20
- Confidence: The code card's precedence list is explicit, and the persona declines the second look, so the TDN2L/DSPT interplay does not arise.

### GEN-C-07 Robot question first, then asks for a payment plan: transfer to restructuring, XRST (special_topic, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Opening (robot), Doc1 Things customers say: plan, Doc1 Notes (transfer freezes), Doc4 XRST row
- Expected: `transferred` / `XRST`; promises []; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: Doc1: a robot question gets the set answer and the call carries on; answering a question first makes the following ask the second one. A request for a plan or lower monthly amounts -> transfer_to_agent restructuring, which freezes everything (no notes) -> transferred XRST.
- Evaluated: -
- Confidence: Explicit rules in Doc1 and the code card.

### GEN-C-08 One wrong answer per question still passes; card promise recorded, then insists on a person: XGEN with the promise kept (special_topic, PUB-12, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions, AHS-5 5.9, AHS-5 5.2, Doc3 item 3, Doc1 Read-back, Doc1 Wants a person, Doc4 XGEN row
- Expected: `transferred` / `XGEN`; promises [{"product_id": "p1", "amount": 510.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: Identity: one wrong answer per question, each followed by a right repeat = pass (Doc1, Doc3 item 6). 5.9: p1 and p2 (16 days) keep the listed order, then p3. p1 is in the Middle band, so its last date is addbd(today,4) = Tue 20 Oct (Doc3). 'This Friday' (5.2) = weekday_in_week(today,'Friday') = 16 Oct, which is inside the window -> full past_due (510) is recorded. The person request is asked once and refused -> transfer general. The transfer freezes the call (the promise stays, no notes) -> XGEN.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 510; promise date p1: weekday_in_week(today, 'Friday') = 2026-10-16
- Confidence: The code card restricts promise rows to 'no transfer after it', so the general transfer gives XGEN. The dates follow the 5.2 and Doc3 rules.

### GEN-C-09 Job loss, accepts Customer Care: transfer to support, XCARE (special_topic, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Things customers say: hardship, Doc4 XCARE row
- Expected: `transferred` / `XCARE`; promises []; notes []; callbacks []; transfers [{"queue": "support"}]
- Derivation: Doc1 hardship: say the sorry line, make no attempt, offer Customer Care, then transfer_to_agent support. The transfer freezes the call (no notes) -> transferred XCARE.
- Evaluated: -
- Confidence: Explicit rules in Doc1 and the code card.

### GEN-C-10 Day/month swapped date of birth, then bereavement with Customer Care declined: hardship notes on all three products, HDNX (special_topic, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Security questions (day_month_swapped), Doc1 Things customers say: hardship, Doc1 Notes, AHS-5 5.9, Doc4 HDNX row
- Expected: `no_promise` / `HDNX`; promises []; notes [{"product_id": "p1", "reason": "hardship"}, {"product_id": "p2", "reason": "hardship"}, {"product_id": "p3", "reason": "hardship"}]; callbacks []; transfers []
- Derivation: Doc1: numeric dates are read day first -> 1987-03-06 -> the service returns the day_month_swapped hint -> ask again with the month as a word (not a wrong answer) -> 1987-06-03 passes. Hardship -> sorry line, no attempt, Customer Care offered and declined -> hardship note on every product -> HDNX.
- Evaluated: -
- Confidence: Both branches are written explicitly in Doc1, and the code card has a dedicated HDNX row.

### GEN-C-11 'Who's calling?' before confirming; after the security questions does not want to talk twice: refused note, no second look, TDN (special_topic, PUB-06, now 2026-10-14T11:00, confidence medium)

- Rules: Doc1 Opening, Doc1 Things customers say: does not want to talk, Doc1 Second look (exclusion), Doc4 TDN row
- Expected: `no_promise` / `TDN`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks []; transfers []
- Derivation: Doc1 opening: a question asked first is answered, and the next ask is the second one; 'Yes, speaking' counts. Doc1 'does not want to talk': say the moment line once; when it is repeated after the security questions, close with no arrangement, a refused note on every open product and no second look -> TDN ('customer would not continue after the security questions').
- Evaluated: -
- Confidence: An agent might read 'I don't want to talk about this' as a flat refusal (a ladder attempt) under 5.5. Doc1's dedicated 'does not want to talk' rule is the specific one, but the line between the two is a reading call.

### GEN-P-01 Middle band loan, every attempt refused, second look booked after one out-of-hours time (persuasion ladder, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: Doc3 item 3, AHS-5 5.3, AHS-5 5.4, AHS-5 5.5, AHS-5 5.7, Doc1 Second look, Doc4 notes, Doc4 TDN2L
- Expected: `no_promise` / `TDN2L`; promises []; notes [{"product_id": "p1", "reason": "refused"}]; callbacks [{"date": "2026-10-19", "time": "17:30"}]; transfers []
- Derivation: days_late 11 = Middle; minutes item 3: full last date = addbd(today,4); 2 attempts (5.5). Attempt 1 full 310.5 on addbd(today,4); attempt 2 floor instalment 103.5 on part last date min(addbd(today,2), addbd(today,4)). Both refused -> turned down, refused note. Second look 5.7: addbd(today,3), 19:00 out of hours, second answer 17:30 fits -> TDN2L.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; callback date: addbd(today, 3) = 2026-10-19
- Confidence: Minutes item 3 fixes the Middle last date; the ladder and the second-look hours are explicit; the persona only refuses.

### GEN-P-02 Card offer above old minimum but below new half-balance floor, then 'next Monday' beyond the part-payment last date (amount below floor + date after part-payment last date, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: Doc3 item 2, AHS-5 5.4, AHS-5 5.2, AHS-5 5.6, Doc4 PARTPTP
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 90.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: Minutes item 2: card floor = ceil(180/2 to multiple of 5) = 90; 60 < floor -> offer floor once (5.4), accepted -> part payment. 'Next Monday' (5.2) = Monday of following week = addbd(today,3) which is later than part last date min(addbd(today,2), Early last date) -> offer that date (5.6), accepted. PARTPTP.
- Evaluated: deadline p1: min(addbd(today, 2), next_bd(today + days(14))) = 2026-10-16; amount p1: min(product('p1')['past_due'], ceil(product('p1')['past_due'] / 2 / 5) * 5) = 90; promise date p1: min(addbd(today, 2), next_bd(today + days(14))) = 2026-10-16
- Confidence: Minutes card floor and part-payment last date are explicit; the persona's answers leave no ledger choice.

### GEN-P-03 Early card full payment, customer changes the date at read-back to St Corran's Day (read-back correction across a closure day, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Read-back, AHS-5 5.1, AHS-5 5.3, AHS-5 5.6, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 420.0, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: days_late 6 = Early; last date next_bd(today+14) = 28 Oct. 21 Oct valid, but changed at read-back to 22 Oct = closure day (5.1) within last date -> offer first business day after it, 23 Oct (5.6), accepted. Full past_due 420 -> FULLPTP.
- Evaluated: script [[d('2026-10-21')]] = 2026-10-21; script [[d('2026-10-22')]] = 2026-10-22; deadline p1: next_bd(today + days(14)) = 2026-10-28; amount p1: product('p1')['past_due'] = 420; promise date p1: next_bd_after(d('2026-10-22')) = 2026-10-23
- Confidence: Closure day and read-back rules are explicit; the persona accepts the single offer.

### GEN-P-04 Middle card accepts attempt 1; first create_promise fails, retry succeeds (promise service failure, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: Doc1 Read-back, AHS-5 5.8, Doc3 item 3, AHS-5 5.5, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 365.0, "date": "2026-10-20"}]; notes []; callbacks []; transfers []
- Derivation: days_late 8 = Middle; minutes item 3 last date addbd(today,4). Plain 'no' -> attempt 1: full 365 on addbd(today,4), accepted. Fault: first create_promise fails -> one retry (Doc1, 5.8) succeeds -> FULLPTP, no service_error note.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 365; promise date p1: addbd(today, 4) = 2026-10-20
- Confidence: Retry rule is explicit and the fault is fixed at one failure.

### GEN-P-05 Late loan: past date, then 'payday' with no exact day; agent proposes the band's last date (date before today + vague period, PUB-09, now 2026-10-14T11:00, confidence medium)

- Rules: AHS-5 5.6, AHS-5 5.3, AHS-5 5.5, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 2100.0, "date": "2026-10-19"}]; notes []; callbacks []; transfers []
- Derivation: days_late 28 = Late; last date addbd(today,3). Past date -> cannot record, ask again (5.6). 'Payday' vague -> ask once, none -> propose the last date that applies (5.6) = addbd(today,3) for full 2100; accepted -> FULLPTP.
- Evaluated: script [[d('2026-10-12')]] = 2026-10-12; deadline p1: addbd(today, 3) = 2026-10-19; amount p1: product('p1')['past_due'] = 2100; promise date p1: addbd(today, 3) = 2026-10-19
- Confidence: 5.6 says propose 'the last date that applies'; an agent might instead fall back to Late attempt 1 (next business day). The date offered and an amount-less vague answer leave a slight reading doubt.

### GEN-P-06 Three products: more than owed on a Saturday, 'too much' on the loan, Early car loan refused, second look (multi-product mix, PUB-12, now 2026-10-14T11:00, confidence medium)

- Rules: AHS-5 5.9, AHS-5 5.4, AHS-5 5.6, AHS-5 5.5, Doc3 item 3, Doc1 Second look, Doc4 PARTPTP, Doc4 notes
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 510.0, "date": "2026-10-19"}, {"product_id": "p2", "amount": 440.0, "date": "2026-10-14"}]; notes [{"product_id": "p3", "reason": "refused"}]; callbacks [{"date": "2026-10-19", "time": "15:00"}]; transfers []
- Derivation: 5.9 order: p1,p2 (16 days, listed order) then p3 (7). p1 Middle: 600 > past_due -> record 510; Saturday (5.2 current week) is weekend -> next business day, within addbd(today,4). p2 'too much' -> floor 440, today -> part. p3 Early: 1 attempt, full 140 on next_bd(today+14) refused -> refused note. Second look addbd(today,3) 15:00. A part promise exists -> PARTPTP.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; deadline p2: min(addbd(today, 2), addbd(today, 4)) = 2026-10-16; deadline p3: next_bd(today + days(14)) = 2026-10-28; amount p1: product('p1')['past_due'] = 510; promise date p1: next_bd(weekday_on_or_after(today, 'Saturday')) = 2026-10-19; amount p2: product('p2')['instalment_amount'] = 440; promise date p2: today = 2026-10-14; callback date: addbd(today, 3) = 2026-10-19
- Confidence: The code card's promise rows cover a call that also has a turned-down product only implicitly ("at least one arrangement recorded"), and the second look being offered alongside promises relies on the per-product trigger.

### GEN-P-07 Job loss, declines Customer Care, then offers the instalment on Friday (hardship then own offer, PUB-04, now 2026-10-14T11:00, confidence medium)

- Rules: Doc1 Things customers say (hardship), AHS-5 5.4, AHS-5 5.2, AHS-5 5.6, Doc4 PARTPTP
- Expected: `promise` / `PARTPTP`; promises [{"product_id": "p1", "amount": 400.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: Hardship -> no attempts, offer support; declined. Customer then offers 400 Friday -> 'normal arrangement' (Doc1). 400 = instalment floor < past_due 1250 -> part payment; Friday (5.2) = this week = addbd(today,2) = part last date -> accept. PARTPTP; product has an arrangement so no note.
- Evaluated: deadline p1: min(addbd(today, 2), addbd(today, 4)) = 2026-10-16; amount p1: product('p1')['instalment_amount'] = 400; promise date p1: weekday_on_or_after(today, 'Friday') = 2026-10-16
- Confidence: Doc1 says a declined transfer leads to hardship notes, but also that a self-offered amount is a normal arrangement; whether a hardship note is still added is not stated explicitly (the notes rule only covers products without an arrangement).

### GEN-P-08 Card promised 'this Friday', then a plan request on the loan freezes the rest (transfer after recorded promise, PUB-11, now 2026-10-14T11:00, confidence high)

- Rules: AHS-5 5.9, AHS-5 5.2, Doc1 Things customers say (plan), Doc1 Notes, Doc4 XRST
- Expected: `transferred` / `XRST`; promises [{"product_id": "p1", "amount": 220.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: 5.9 order: p1, p2 (9 days, listed order), p3 (3). p1 Middle, 'this Friday' = Friday of current week (5.2), within addbd(today,4) -> full 220 recorded. p2 plan request -> transfer restructuring; transfer freezes, no notes -> transferred XRST.
- Evaluated: deadline p1: addbd(today, 4) = 2026-10-20; amount p1: product('p1')['past_due'] = 220; promise date p1: weekday_in_week(today, 'Friday') = 2026-10-16
- Confidence: Transfer freeze and the XRST code are explicit; the promise is recorded before the transfer.

### GEN-P-09 Late loan on the day before the moved cut-over: 'tomorrow' is a closure day (calendar edge, moved closure day, PUB-05, now 2026-11-05T11:00, confidence high)

- Rules: Doc3 item 4, AHS-5 5.1, AHS-5 5.2, AHS-5 5.3, AHS-5 5.6, Doc4 FULLPTP
- Expected: `promise` / `FULLPTP`; promises [{"product_id": "p1", "amount": 780.0, "date": "2026-11-09"}]; notes []; callbacks []; transfers []
- Derivation: Minutes item 4: 6 Nov 2026 is a closure day (13 Nov no longer). days_late 21 = Late; last date addbd(today,3) skips 6 Nov. 'Tomorrow' (5.2) = today+1 = closure day within last date -> offer first business day after it (5.6), accepted -> full 780, FULLPTP.
- Evaluated: deadline p1: addbd(today, 3) = 2026-11-10; amount p1: product('p1')['past_due'] = 780; promise date p1: next_bd_after(today + days(1)) = 2026-11-09
- Confidence: The minutes explicitly move the cut-over; 'tomorrow' is defined as the calendar day after the call.

## Valid but trimmed (cap of 20 cases)

- GEN-C-12 Scam question, then the ladder runs out; second look across St Corran's Day, evening time out of hours then 17:00: TDN2L

