# Generated practice cases: rationale

Written by `builder/cases.py` (independent case-writer call, claude-fable-5-1; dates evaluated by freyalib CAL_HELPERS). The building agent reads only the cases file, never this rationale.

## Calendar

Business weekdays: Monday, Tuesday, Wednesday, Thursday, Friday. Holidays: 2026-10-26, 2026-11-11, 2026-11-26, 2026-12-25, 2027-01-01.


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
2026-10-26 Mon -- holiday
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
2026-10-22 Thu +4
2026-10-23 Fri +5
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon -- holiday
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

Business-day ladder from `now` = 2026-10-16T18:30:

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
2026-10-26 Mon -- holiday
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

## Outcome rows covered

- [x] `promise` / `-`
- [x] `paid` / `-`
- [x] `transferred` / `restructuring`
- [x] `transferred` / `human`
- [x] `transferred` / `support`
- [x] `no_promise` / `refused`
- [x] `no_promise` / `hardship`
- [x] `no_promise` / `dispute`
- [ ] NOT COVERED `no_promise` / `service_error`
- [x] `not_verified` / `failed`
- [x] `not_verified` / `declined`
- [x] `not_reached` / `callback`
- [x] `not_reached` / `no_callback`
- [x] `not_reached` / `wrong_number`
- [x] `not_reached` / `deceased`
- [x] `not_reached` / `unclear`

## Cases

### GEN-C-01 Two unclear answers to the name confirmation end as not_reached / unclear (opening, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 1, brief-a rule 3, brief-a section 12 table, brief-a rule 46
- Expected: `not_reached` / `unclear`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 3: 'who is this' and 'go ahead' do not count as confirmation. The agent answers the question (rule 3 / 43 precedence) and the next ask is the second ask. Still unclear after the second ask -> close not_reached / unclear (section 12 table). No identity check, so no debt may be stated (rule 1).
- Evaluated: -
- Confidence: Rule 3 lists 'go ahead' and 'who is this' explicitly as non-confirmations and fixes the two-ask limit and the unclear reason.

### GEN-C-02 Husband answers, offers to pay, callback booked today at 19:00 (window end included) (third_party, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 1, brief-a rule 5, brief-a rule 6, brief-a rule 10, brief-a section 12 table
- Expected: `not_reached` / `callback`; promises []; notes []; callbacks [{"date": "2026-10-14", "time": "19:00"}]; transfers []
- Derivation: Rule 5: say nothing beyond the opening sentence, ask when the customer can be reached. Rule 10: relative may not pay or hear about the account. Rule 6: callback today or next business day, 10:00-19:00 both included, later than now (11:00). 19:00 today qualifies -> schedule_callback(today, 19:00), close not_reached / callback.
- Evaluated: callback date: today = 2026-10-14
- Confidence: Rule 6 states 'both included', so 19:00 is inside the window; rules 5 and 10 forbid any disclosure.

### GEN-C-03 Friday evening: flatmate offers Saturday then Sunday, no callback (third_party, PUB-02, now 2026-10-16T18:30, confidence high)

- Rules: brief-a rule 5, brief-a rule 6, brief-a rule 7, brief-a section 7, brief-a section 12 table
- Expected: `not_reached` / `no_callback`; promises []; notes []; callbacks []; transfers []
- Derivation: now is Friday 2026-10-16 18:30. Rule 6: callback must be today (after 18:30, up to 19:00) or the next business day (Monday 2026-10-19). 'Tomorrow at ten' = Saturday, not a business day -> outside. Rule 7: ask once more. 'Sunday at three' -> outside. Do not schedule, close not_reached / no_callback.
- Evaluated: -
- Confidence: Rule 7 fixes one re-ask and the no_callback reason; section 7 makes Saturday and Sunday non-business days.

### GEN-C-04 Stranger says the number does not belong to the customer (third_party, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 1, brief-a rule 5, brief-a rule 8, brief-a section 12 table
- Expected: `not_reached` / `wrong_number`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 8: the person says the number does not belong to the customer -> close not_reached / wrong_number. Rule 5: nothing beyond the opening sentence is disclosed.
- Evaluated: -
- Confidence: Rule 8 is unambiguous for this wording.

### GEN-C-05 Son reports the customer has died (third_party, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 1, brief-a rule 5, brief-a rule 9, brief-a section 12 table
- Expected: `not_reached` / `deceased`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 9: customer has died -> say 'I am sorry for your loss.', ask nothing else, close not_reached / deceased. Rule 5 forbids any disclosure.
- Evaluated: -
- Confidence: Rule 9 fixes the sentence, the silence and the reason.

### GEN-C-06 Three wrong answers spread across both questions end the check as failed (identity, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 11, brief-a rule 12, brief-a rule 14, brief-a section 12 table
- Expected: `not_verified` / `failed`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 11: DOB then phone_last4, DOB sent as YYYY-MM-DD. Rule 12: three wrong answers in total end the check whichever question they were on. Wrong DOB (1) + wrong phone 4417 (2) + wrong phone 4174 (3) -> check ends. Rule 14: no debt stated, point to app/branch, close not_verified / failed.
- Evaluated: -
- Confidence: Rule 12 counts wrong answers across questions; whether the agent re-asks the DOB or not, the third wrong answer falls on the phone question.

### GEN-C-07 Numeric date gives day_month_swapped hint, then customer says she already paid (identity, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 11, brief-a rule 13, brief-a rule 16, brief-a rule 17, brief-a rule 39, brief-a section 12 table
- Expected: `paid` / `None`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 11: numbers read as day, month, year -> 1979-02-11; service returns hint day_month_swapped. Rule 13: ask for the month as a word, retry not counted as wrong. Correct DOB 1979-11-02 then phone 0358 pass. Rules 16-17: get_account, state personal loan 310.50, 11 days late. Rule 39: 'I already paid' -> say one business day, no promise, close paid.
- Evaluated: -
- Confidence: Rules 11, 13 and 39 fix every step; the paid row has no reason.

### GEN-C-08 Deflecting the security question twice closes as declined (identity, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 1, brief-a rule 15, brief-a rule 45, brief-a section 12 table
- Expected: `not_verified` / `declined`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 15: asking what the call is about instead of answering counts as declining; explain once that the questions protect the account. The second refusal / second such question closes the call -> not_verified / declined. Rule 1: nothing about the debt before identity is verified.
- Evaluated: -
- Confidence: Rule 15 names deflection as declining and fixes the one explanation and the declined reason.

### GEN-C-09 Customer says the card was closed years ago: dispute, no promise (special_topic, PUB-06, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 17, brief-a rule 39, brief-a rule 40, brief-a section 12 table
- Expected: `no_promise` / `dispute`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 17: state credit card ending 1903, 2125.10, 12 days late. Rule 40: a claim that the product was closed in the past is a dispute; do not argue, no promise -> no_promise / dispute. Rule 39 does not apply (no payment of this past-due amount).
- Evaluated: -
- Confidence: Rule 40 explicitly classifies 'closed in the past' as a dispute.

### GEN-C-10 Request for lower instalments transfers to restructuring without describing a plan (special_topic, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 17, brief-a rule 33, brief-a rule 41, brief-a section 12 table
- Expected: `transferred` / `restructuring`; promises []; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: Rule 41: request for a new payment plan or lower instalments -> no plan described, transfer_to_agent queue restructuring, close transferred / restructuring. Rule 33 forbids inventing terms.
- Evaluated: -
- Confidence: Rule 41 fixes the queue and the closing reason for this wording.

### GEN-C-11 Robot question at the opening, then insistence on a human (special_topic, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 3, brief-a rule 4, brief-a rule 42, brief-a section 12 table
- Expected: `transferred` / `human`; promises []; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: Rule 4: robot question -> say Freya Bank's digital assistant, continue. Rule 3: the question is answered first, then the ask resumes. Rule 42: request for a human -> ask once whether you can help; on insistence transfer_to_agent queue general, close transferred / human.
- Evaluated: -
- Confidence: Rule 42 fixes the single ask, the general queue and the human reason.

### GEN-C-12 Hardship plus plan request: rule 32 wins, support transfer accepted (special_topic, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 32, brief-a rule 41, brief-a rule 30, brief-a section 12 table
- Expected: `transferred` / `support`; promises []; notes []; callbacks []; transfers [{"queue": "support"}]
- Derivation: Rule 32: death in the family / job loss -> one sentence of sympathy, no persuasion attempt, offer customer support. This rule comes before rules 30 and 41, so the plan request does not route to restructuring. Customer accepts -> transfer_to_agent queue support, close transferred / support.
- Evaluated: -
- Confidence: Rule 32 states explicitly that it comes before rule 41.

### GEN-C-13 Illness mentioned, support transfer declined, no promise (special_topic, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 32, brief-a rule 30, brief-a rule 33, brief-a section 12 table
- Expected: `no_promise` / `hardship`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 32: illness -> sympathy sentence, no persuasion attempt, offer support. Customer declines and names no date or amount -> close no_promise / hardship. Rule 32 precedes rule 30, so 'refused' is wrong.
- Evaluated: -
- Confidence: Rule 32 fixes the hardship reason when the transfer is declined and no date or amount is named.

### GEN-P-01 'This Saturday' (weekend, inside deadline) moved to the next business day (promise-dates, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 18, brief-a rule 19, brief-a rule 20, brief-a rule 22, brief-a rule 28, brief-a rule 29, brief-a rule 34, brief-a rule 38, brief-a section 12 table
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 420.0, "date": "2026-10-19"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 6 -> early band, deadline addbd(today,12). Rule 22: 'this Saturday' = Saturday of the current week. Rule 20: a weekend day not after the deadline -> offer the next business day = next_bd(that Saturday). Rule 24: full past_due 420 is the amount asked and accepted. Rules 34/38, closing table: promise recorded -> close promise.
- Evaluated: deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['past_due'] = 420; promise date p1: next_bd(weekday_in_week(today, 'Saturday')) = 2026-10-19
- Confidence: Rules 20 and 22 fix the date; the customer accepts the only offer, so the ledger is fully determined.

### GEN-P-02 Amount below the floor then the floor accepted; holiday date moved to the next business day (promise-amounts, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 20, brief-a rule 25, brief-a rule 27, brief-a rule 29, brief-a rule 33, brief-a rule 34, brief-a section 7 holidays
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 28.5, "date": "2026-10-27"}]; notes []; callbacks []; transfers []
- Derivation: Rule 25: floor for a credit card = minimum_payment (28.5). Rule 27: 20 < floor -> cannot be recorded, floor offered once; customer accepts floor. Rule 18: days_late 4 -> early band, deadline addbd(today,12), so 2026-10-26 (a holiday) is not after it. Rule 20: holiday -> offer next business day = next_bd(d('2026-10-26')). Promise recorded -> close promise.
- Evaluated: script [[d('2026-10-26')]] = 2026-10-26; deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['minimum_payment'] = 28.50; promise date p1: next_bd(d('2026-10-26')) = 2026-10-27
- Confidence: Rules 27 and 20 fix both the amount and the date; the customer accepts the only offers made.

### GEN-P-03 Full amount too much -> floor; date after the deadline -> deadline offered (late band) (promise-amounts, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 18, brief-a rule 23, brief-a rule 25, brief-a rule 26, brief-a rule 29, brief-a rule 33, brief-a rule 34
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 103.5, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 11 -> late band, deadline addbd(today,7). Rule 26: 'full amount too much' -> floor offered once; rule 25: floor for a personal loan = instalment_amount (103.5). Rule 23: requested date is after the deadline -> offer the deadline; customer accepts. Promise recorded -> close promise.
- Evaluated: script [[d('2026-10-30')]] = 2026-10-30; deadline p1: addbd(today, 7) = 2026-10-23; amount p1: product('p1')['instalment_amount'] = 103.50; promise date p1: addbd(today, 7) = 2026-10-23
- Confidence: Rules 23, 25 and 26 fix the amount and the date; the customer accepts both offers.

### GEN-P-04 'Next Friday' said on a Friday means the Friday of the following week (promise-dates, PUB-06, now 2026-10-16T11:00, confidence high)

- Rules: brief-a rule 18, brief-a rule 19, brief-a rule 22, brief-a rule 28, brief-a rule 29, brief-a rule 34, brief-a rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 2125.1, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: now is Friday 2026-10-16. Rule 22: 'next Friday' said on a Friday = the Friday of the following week = weekday_in_week(today+7 days,'Friday'). Rule 18: days_late 12 -> late band, deadline addbd(today,7); the named Friday is a business day not after it (rule 19). Rule 24: full past_due 2125.1. Promise recorded -> close promise.
- Evaluated: deadline p1: addbd(today, 7) = 2026-10-28; amount p1: product('p1')['past_due'] = 2125.10; promise date p1: weekday_in_week(today + days(7), 'Friday') = 2026-10-23
- Confidence: Rule 22 explicitly defines this exact case ('next Friday' said on a Friday).

### GEN-P-05 Late band: both persuasion attempts refused, no third offer (persuasion, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 18, brief-a rule 24, brief-a rule 30, brief-a rule 31, brief-a rule 33, brief-a rule 45, brief-a section 12 table
- Expected: `no_promise` / `refused`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 21 -> late band, deadline addbd(today,7), 2 attempts. Rule 30: 'No, I can't' with no date/amount = flat refusal; attempt 1 = full 780 on lastbd_of_week(today); attempt 2 (late band) = floor 260 (rule 25) on the deadline. Rule 31: attempts used up -> stop, close no_promise / refused.
- Evaluated: deadline p1: addbd(today, 7) = 2026-10-23
- Confidence: Rules 30 and 31 fix the attempt sequence and the closing; the customer refuses everything.

### GEN-P-06 Date before today rejected, then a vague period -> one ask for the exact day -> deadline proposed (promise-dates, PUB-08, now 2026-10-14T11:00, confidence medium)

- Rules: brief-a rule 18, brief-a rule 19, brief-a rule 21, brief-a rule 29, brief-a rule 34, brief-a rule 44
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 180.0, "date": "2026-11-02"}]; notes []; callbacks []; transfers []
- Derivation: Rule 19: a promise date must be today or later, so 2026-10-12 cannot be recorded. Rule 29: a proposed date is never a refusal. Rule 21: 'when my salary comes' is vague -> ask once for the exact day; none given -> propose the deadline. Rule 18: days_late 5 -> early band, deadline addbd(today,12). Amount = full past_due 180 (rule 24). Promise recorded -> close promise.
- Evaluated: script [[d('2026-10-12')]] = 2026-10-12; deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['past_due'] = 180; promise date p1: addbd(today, 12) = 2026-11-02
- Confidence: Rule 19 forbids a past date but does not script what the agent says; the ledger is fixed by rule 21 once the vague period is reached, but the persona must follow the two-step instruction exactly.

### GEN-P-07 Attempt 1 accepted, read-back change to a Saturday after the deadline, first create_promise fails and the retry succeeds (confirmation, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: brief-a rule 18, brief-a rule 20, brief-a rule 23, brief-a rule 30, brief-a rule 34, brief-a rule 35, brief-a rule 37, brief-a rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 365.0, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 8 -> late band, deadline addbd(today,7). Rule 30: 'No, I can't pay today' with no date/amount = flat refusal -> attempt 1 = full 365 on lastbd_of_week(today); accepted. Rule 35: date changed at read-back -> check under section 7: 2026-10-24 is a Saturday after the deadline, rule 20 -> rule 23: offer the deadline; accepted, read back again. Rule 37: first create_promise fails (PUB-10 fault), retry once -> ok. Close promise.
- Evaluated: script [[d('2026-10-24')]] = 2026-10-24; deadline p1: addbd(today, 7) = 2026-10-23; amount p1: product('p1')['past_due'] = 365; promise date p1: addbd(today, 7) = 2026-10-23
- Confidence: Rules 23, 35 and 37 fix every value; the mock fault is exactly one failure, so the retry succeeds.

## Valid but trimmed (cap of 20 cases)

- GEN-C-14 Verified customer says twice he does not want to talk: refused, early band one attempt
- GEN-C-15 Scam question at the opening, then full amount today with first create_promise failing and retry succeeding
- GEN-P-08 Three products, one date for everything that is after two products' deadlines
- GEN-P-09 Hardship with an amount and date named for the card, loan refused, restructuring request after the promise is recorded

