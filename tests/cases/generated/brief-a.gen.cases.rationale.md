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

Business-day ladder from `now` = 2026-10-23T11:00:

```
2026-10-23 Fri today
2026-10-24 Sat -- not a business day
2026-10-25 Sun -- not a business day
2026-10-26 Mon -- holiday
2026-10-27 Tue +1
2026-10-28 Wed +2
2026-10-29 Thu +3
2026-10-30 Fri +4
2026-10-31 Sat -- not a business day
2026-11-01 Sun -- not a business day
2026-11-02 Mon +5
2026-11-03 Tue +6
2026-11-04 Wed +7
2026-11-05 Thu +8
2026-11-06 Fri +9
2026-11-07 Sat -- not a business day
2026-11-08 Sun -- not a business day
2026-11-09 Mon +10
2026-11-10 Tue +11
2026-11-11 Wed -- holiday
2026-11-12 Thu +12
2026-11-13 Fri +13
2026-11-14 Sat -- not a business day
2026-11-15 Sun -- not a business day
2026-11-16 Mon +14
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

### GEN-C-01 Two unclear answers to 'Am I speaking with Mr Reyes?' close as unclear (opening, PUB-01, now 2026-10-14T11:00, confidence high)

- Rules: rule 1, rule 2, rule 3, rule 46, section 12 table
- Expected: `not_reached` / `unclear`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 3: 'Hello' and 'go ahead' do not count as confirmation; ask once more; still unclear after the second ask -> not_reached / unclear. Rule 1: nothing about the debt may be said because identity was never verified. No other tool is justified; rule 46 close_call last.
- Evaluated: -
- Confidence: Rule 3 lists both 'Hello' and 'go ahead' verbatim as non-confirmations and fixes the two-ask limit.

### GEN-C-02 Relative offers to pay; Monday is a holiday so first slot is outside the window, Tuesday 11:00 is booked (third_party, PUB-02, now 2026-10-23T11:00, confidence medium)

- Rules: rule 1, rule 5, rule 6, rule 7, rule 10, section 7 holidays, section 12 table
- Expected: `not_reached` / `callback`; promises []; notes []; callbacks [{"date": "2026-10-27", "time": "11:00"}]; transfers []
- Derivation: Rules 5, 10: a relative gets nothing beyond the opening sentence and may not pay or answer security questions; ask when the customer can be reached. Rule 6: window = today (Fri 2026-10-23) or the next business day; 2026-10-26 is a Freya holiday, so the next business day is next_bd_after(today) = 2026-10-27. Rule 7: Monday is outside the window -> ask once for another time; Tuesday 11:00 is inside the window and later than now -> schedule_callback(2026-10-27, 11:00), close not_reached / callback.
- Evaluated: callback date: next_bd_after(today) = 2026-10-27
- Confidence: Rule 6's 'next business day' with the 2026-10-26 holiday is unambiguous in the brief, but an agent (or a lenient reader) may treat 'Monday' as acceptable; the expected ledger follows the holiday list literally.

### GEN-C-03 Relative offers 20:00 tonight then 09:00 tomorrow: both outside the window, no callback (third_party, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: rule 5, rule 6, rule 7, section 12 table
- Expected: `not_reached` / `no_callback`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 6: callback window is 10:00-19:00 today or the next business day. Rule 7: 20:00 is outside -> ask once more; 09:00 is also outside -> do not schedule, close not_reached / no_callback.
- Evaluated: -
- Confidence: Both offered times fall clearly outside 10:00-19:00 and rule 7 fixes the single re-ask and the closing row.

### GEN-C-04 Stranger says the number does not belong to Lena Hoffmann (third_party, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: rule 1, rule 5, rule 8, section 12 table
- Expected: `not_reached` / `wrong_number`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 8: the person says the number does not belong to the customer -> not_reached / wrong_number. Rule 5 / rule 1: nothing about the reason for the call is disclosed.
- Evaluated: -
- Confidence: Rule 8 maps this statement directly to the wrong_number row.

### GEN-C-05 Relative says Tomas Novak has died (third_party, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: rule 1, rule 5, rule 9, section 12 table
- Expected: `not_reached` / `deceased`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 9: the person says the customer has died -> say 'I am sorry for your loss.', ask nothing else, close not_reached / deceased.
- Evaluated: -
- Confidence: Rule 9 gives the exact sentence and the exact closing row.

### GEN-C-06 Two wrong birth years, correct DOB, then one wrong phone digit: third wrong answer across questions fails the check (identity, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: rule 11, rule 12, rule 14, section 12 table
- Expected: `not_verified` / `failed`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 11: DOB first as YYYY-MM-DD, then phone_last4. Rule 12: wrong answers count in total across questions; 2 wrong DOB + 1 wrong phone = 3 -> check ends. Rule 14: do not state the debt, point to app or branch, close not_verified / failed.
- Evaluated: -
- Confidence: Rule 12 states the three-wrong limit is counted in total 'whichever question they were on'; the persona only needs to follow fixed answers.

### GEN-C-07 Asks what the call is about instead of answering DOB, twice: declined (identity, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: rule 1, rule 15, rule 45, section 12 table
- Expected: `not_verified` / `declined`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 15: asking what the call is about instead of answering counts as declining; explain once that the questions protect the account; the second such question closes the call -> not_verified / declined. Rule 1: before verification the reason for the call may not be revealed.
- Evaluated: -
- Confidence: Rule 15 explicitly equates the deflecting question with declining and sets the one-explanation limit.

### GEN-C-08 DOB given as 08/11/1981 triggers day_month_swapped, retry not counted; then 'I already paid' closes as paid (identity, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: rule 11, rule 13, rule 16, rule 17, rule 39, section 12 table
- Expected: `paid` / `None`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 11: digits are read day, month, year -> 1981-11-08 is sent; rule 13: hint day_month_swapped -> ask for the month as a word, retry not counted as wrong; 1981-08-11 verifies. Rules 16-17: get_account, state the debt. Rule 39: 'I already paid' -> say one business day to appear, no promise, close paid (no reason in the table).
- Evaluated: -
- Confidence: Rules 13 and 39 fix every step; the mock serves the hint per the API enum.

### GEN-C-09 Customer says the car loan was paid off and closed last year: dispute, not paid (special_topic, PUB-04, now 2026-10-14T11:00, confidence high)

- Rules: rule 17, rule 39, rule 40, section 12 table
- Expected: `no_promise` / `dispute`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 40: a claim that the product was closed or paid off in the past is a dispute; do not argue, take no promise -> no_promise / dispute. Rule 39 covers only a payment of this past-due amount, so 'paid' does not apply.
- Evaluated: -
- Confidence: Rule 40 names the 'closed or paid off in the past' claim as a dispute and excludes rule 39 explicitly.

### GEN-C-10 Request for lower instalments goes to restructuring without a persuasion attempt (special_topic, PUB-05, now 2026-10-14T11:00, confidence high)

- Rules: rule 28, rule 33, rule 41, section 12 table
- Expected: `transferred` / `restructuring`; promises []; notes []; callbacks []; transfers [{"queue": "restructuring"}]
- Derivation: Rule 41: a request for a new payment plan or lower instalments -> do not describe a plan, transfer_to_agent(restructuring), close transferred / restructuring. Rule 33: no plan terms may be offered.
- Evaluated: -
- Confidence: Rule 41 is direct and the customer's line uses the brief's own words 'new payment plan' and 'lower instalments'.

### GEN-C-12 Job loss: sympathy, no persuasion attempt, support transfer accepted (special_topic, PUB-06, now 2026-10-14T11:00, confidence high)

- Rules: rule 28, rule 30, rule 32, section 12 table
- Expected: `transferred` / `support`; promises []; notes []; callbacks []; transfers [{"queue": "support"}]
- Derivation: Rule 32: job loss -> one sentence of sympathy, no persuasion attempt, offer the customer support team; accepted -> transfer_to_agent(support), close transferred / support. Rule 32 comes before rules 30 and 41, so the refusal does not consume a persuasion attempt.
- Evaluated: -
- Confidence: Rule 32 fixes the sympathy, the no-attempt rule and the transfer queue; the customer accepts unambiguously.

### GEN-C-13 Death in the family, support declined, no date or amount named: no_promise / hardship (special_topic, PUB-03, now 2026-10-14T11:00, confidence high)

- Rules: rule 28, rule 30, rule 32, section 12 table
- Expected: `no_promise` / `hardship`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 32: a death in the family -> sympathy, no persuasion attempt, offer support; declined -> close no_promise / hardship. Rule 32 precedes rule 30, so the 'no' is not a flat refusal and the outcome is hardship rather than refused.
- Evaluated: -
- Confidence: Rule 32 gives the declined branch its own row and precedence over rule 30; the customer names no date or amount.

### GEN-P-01 Early band: attempt 1 proposed, customer counters with a Saturday, moved to Monday (promise-dates, PUB-08, now 2026-10-14T11:00, confidence high)

- Rules: rule 18, rule 19, rule 20, rule 29, rule 30, rule 34, rule 37, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 180.0, "date": "2026-10-19"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 6 -> early band, deadline addbd(today,12) = 2 Nov 2026, 1 attempt. Rule 30: a no with no date/amount is a flat refusal -> attempt 1 = full amount on lastbd_of_week(today) = Fri 16 Oct. Rule 29: the customer's Saturday 17 Oct is a date proposal, never a refusal. Rule 20: Saturday within the deadline -> offer next business day = next_bd(d('2026-10-17')) = Mon 19 Oct. Rules 34/37/38: read back, confirm, record 180 on 19 Oct; close promise with no reason.
- Evaluated: script [[d('2026-10-17')]] = 2026-10-17; script [[next_bd(d('2026-10-17'))]] = 2026-10-19; deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['past_due'] = 180; promise date p1: next_bd(d('2026-10-17')) = 2026-10-19
- Confidence: Rules 18, 20 and 30 fix the amount (full 180) and the date (next business day after the Saturday); the customer has no ledger-changing choice.

### GEN-P-02 Full amount too much: floor accepted on a holiday date, moved to next business day (promise-amounts, PUB-07, now 2026-10-14T11:00, confidence high)

- Rules: rule 18, rule 20, rule 24, rule 25, rule 26, rule 29, rule 34, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 180.0, "date": "2026-10-27"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 5 -> early band, deadline addbd(today,12) = 2 Nov 2026. Rule 24: ask full 540 first. Rules 25/26: full too much -> offer floor = instalment_amount 180 once, rest stays overdue; customer accepts. Rule 20: 26 Oct is a holiday not after the deadline -> offer next business day next_bd(d('2026-10-26')) = 27 Oct. Rules 34/38: confirm, record, text-message sentence; close promise.
- Evaluated: script [[d('2026-10-26')]] = 2026-10-26; script [[next_bd(d('2026-10-26'))]] = 2026-10-27; deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['instalment_amount'] = 180; promise date p1: next_bd(d('2026-10-26')) = 2026-10-27
- Confidence: Rules 25, 26 and 20 fix 180 and 27 October; no customer choice remains.

### GEN-P-03 Late band: date after the deadline, agent offers the deadline and customer accepts (promise-dates, PUB-02, now 2026-10-14T11:00, confidence high)

- Rules: rule 18, rule 19, rule 23, rule 24, rule 29, rule 34, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 310.5, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 11 -> late band, deadline addbd(today,7) = Fri 23 Oct 2026. Rule 29: a proposed date is never a refusal. Rule 23: 30 Oct is after the deadline -> say the latest date is the deadline and offer it; customer accepts. Rule 24: amount is the full past_due 310.5. Close promise.
- Evaluated: script [[d('2026-10-30')]] = 2026-10-30; script [[addbd(today, 7)]] = 2026-10-23; deadline p1: addbd(today, 7) = 2026-10-23; amount p1: product('p1')['past_due'] = 310.50; promise date p1: addbd(today, 7) = 2026-10-23
- Confidence: Rule 23 fixes the date as the deadline and the amount is the full past-due; the customer accepts the first offer.

### GEN-P-04 Below the floor plus a vague period: floor offered once, deadline proposed after one ask (promise-amounts, PUB-06, now 2026-10-14T11:00, confidence high)

- Rules: rule 18, rule 21, rule 25, rule 27, rule 29, rule 34, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 637.5, "date": "2026-10-23"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 12 -> late band, deadline addbd(today,7) = 23 Oct 2026. Rule 29: '500 next week' is a proposal, not a refusal. Rule 27: 500 < floor 637.5 (minimum_payment, rule 25) -> cannot be recorded, offer floor once; accepted. Rule 21: 'next week' is vague -> ask once for the exact day; none given -> propose the deadline; accepted. Close promise with minimum_payment on the deadline.
- Evaluated: script [[addbd(today, 7)]] = 2026-10-23; script [[addbd(today, 7)]] = 2026-10-23; deadline p1: addbd(today, 7) = 2026-10-23; amount p1: product('p1')['minimum_payment'] = 637.50; promise date p1: addbd(today, 7) = 2026-10-23
- Confidence: Rules 21 and 27 fix both values regardless of the order the agent handles them; the persona accepts each first offer.

### GEN-P-05 Friday call: 'next Friday' means the following week, then a read-back change to a Saturday before a holiday (promise-dates, PUB-03, now 2026-10-16T11:00, confidence high)

- Rules: rule 18, rule 19, rule 20, rule 22, rule 34, rule 35, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 95.0, "date": "2026-10-27"}]; notes []; callbacks []; transfers []
- Derivation: now = Fri 16 Oct 2026. Rule 18: days_late 4 -> early band, deadline addbd(today,12) = 4 Nov 2026. Rule 22: 'next Friday' on a Friday = Friday of the following calendar week = weekday_in_week(today+days(7),'Friday') = 23 Oct. Rule 35: change at read-back is checked under section 7: rule 20 -> Sat 24 Oct (not after deadline) moves to next_bd(d('2026-10-24')) = Tue 27 Oct because Mon 26 Oct is a holiday. Read back again, confirm, record 95 on 27 Oct; close promise.
- Evaluated: script [[weekday_in_week(today + days(7), 'Friday')]] = 2026-10-23; script [[d('2026-10-24')]] = 2026-10-24; script [[next_bd(d('2026-10-24'))]] = 2026-10-27; deadline p1: addbd(today, 12) = 2026-11-04; amount p1: product('p1')['past_due'] = 95; promise date p1: next_bd(d('2026-10-24')) = 2026-10-27
- Confidence: Rule 22 and rule 20 give one date each; the persona withholds confirmation at the first read-back as instructed, so only one promise can be recorded.

### GEN-P-06 Late band: both persuasion attempts refused, no third offer (persuasion, PUB-09, now 2026-10-14T11:00, confidence high)

- Rules: rule 18, rule 25, rule 30, rule 31, rule 33, section 12 table
- Expected: `no_promise` / `refused`; promises []; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 28 -> late band, deadline addbd(today,7) = 23 Oct 2026, 2 attempts. Rule 30: 'no' with no date/amount is a flat refusal -> attempt 1 = full 2100 on lastbd_of_week(today) = Fri 16 Oct; refused -> attempt 2 = floor instalment_amount 700 (rule 25) on the deadline 23 Oct; refused. Rule 31: attempts used up -> stop, close no_promise / refused.
- Evaluated: script [[addbd(today, 7)]] = 2026-10-23; deadline p1: addbd(today, 7) = 2026-10-23
- Confidence: Rules 30 and 31 fix both attempts and the closing; the persona refuses every offer.

### GEN-P-07 Date before today rejected, then 'this Friday' means the current week's Friday (promise-dates, PUB-01, now 2026-10-14T11:00, confidence medium)

- Rules: rule 18, rule 19, rule 22, rule 24, rule 29, rule 34, rule 38
- Expected: `promise` / `None`; promises [{"product_id": "p1", "amount": 420.0, "date": "2026-10-16"}]; notes []; callbacks []; transfers []
- Derivation: Rule 18: days_late 6 -> early band, deadline addbd(today,12) = 2 Nov 2026. Rule 19: a promise date must be today or later -> 13 Oct is not recordable. Rule 29: a proposed date is never a refusal, so no persuasion attempt. Rule 22: 'this Friday' = weekday_in_week(today,'Friday') = 16 Oct, a business day within the deadline. Rule 24: full 420. Close promise.
- Evaluated: script [[d('2026-10-13')]] = 2026-10-13; script [[weekday_in_week(today, 'Friday')]] = 2026-10-16; deadline p1: addbd(today, 12) = 2026-11-02; amount p1: product('p1')['past_due'] = 420; promise date p1: weekday_in_week(today, 'Friday') = 2026-10-16
- Confidence: Rule 19 bars a past date but the brief does not say what the agent must say or propose next; the expected ledger assumes the agent simply asks for another day and the customer then supplies 'this Friday'.

### GEN-P-08 create_promise fails once and succeeds on retry; then a human is requested after the recorded promise (service-fault, PUB-10, now 2026-10-14T11:00, confidence high)

- Rules: rule 28, rule 34, rule 36, rule 37, rule 38, rule 42, section 12 table
- Expected: `transferred` / `human`; promises [{"product_id": "p1", "amount": 365.0, "date": "2026-10-14"}]; notes []; callbacks []; transfers [{"queue": "general"}]
- Derivation: Rule 28: customer pays full 365 today; today (Wed) is a business day within deadline addbd(today,7). Rule 37: first create_promise fails (PUB-10 fault) -> try once more; second succeeds -> say recorded, rule 38 sentence. Rule 42: request for a human -> ask once, customer insists -> transfer_to_agent queue general. Section 12: a transfer after a recorded promise closes as transferred / human.
- Evaluated: deadline p1: addbd(today, 7) = 2026-10-23; amount p1: product('p1')['past_due'] = 365; promise date p1: today = 2026-10-14
- Confidence: Rule 37 fixes the retry and section 12 explicitly resolves the promise-then-transfer precedence.

## Valid but trimmed (cap of 20 cases)

- GEN-C-11 Request for a human before identity is verified: ask once, then transfer to general
- GEN-C-14 Verified customer says twice she does not want to talk: no_promise / refused
- GEN-C-15 Scam question at opening, then full amount today; first create_promise fails, retry succeeds: promise
- GEN-P-09 Hardship (job loss) with no persuasion, support declined, customer still names floor amount and a date

