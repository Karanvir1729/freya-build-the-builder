# Brief G — rationale (never read by the builder)

Sources: [M] Fenella Marsh's mail of 1 Oct; [S] AHS-5 section 5 (1 Sep); [R] review minutes of 9 Oct, in force from the first call on 14 Oct; [K] code card v2. [M] says the Standard wins where it and the mail differ. [R] is the latest dated decision and changes three things without any "supersedes" or "override" wording: R2 the card floor, R3 the Middle-band last date, R4 the cut-over closure day (13 Nov → 6 Nov). R5 and R6 decide "no change" (distractors that brush policy vocabulary). The minutes also say the Early band is not widened (another distractor).

## Rules in force from 14 Oct
- Closure days 14 Oct–30 Nov: **2026-10-22** (St Corran's Day), **2026-11-06** (cut-over, R4), **2026-11-24** (Regatta Day). 2026-11-13 is a business day again (R4).
- Weeks Mon–Sun. "Friday"/"this Friday" = next upcoming Friday (today included); "next Friday" = Friday of the following week; "tomorrow" = next calendar day.
- Bands: Early 1–7 → last date = call + 14 calendar days, rolled FORWARD to a business day; 1 attempt. Middle 8–20 → 4th business day (R3; [S] said 6th); 2 attempts. Late 21–45 → 3rd business day; 2 attempts.
- Part-payment last date: 2nd business day after the call, or the band's last date if earlier.
- Floors: card = ceil(past_due / 2 / 5) × 5, capped at past_due (R2; [S] said minimum_payment); loans = instalment_amount.
- Ladder: attempt 1 Early/Middle = full on band last date, Late = full on next business day; attempt 2 (Middle, Late) = floor on part-payment last date. Floor turned down after "too much" or after a below-floor offer → turned down at once.
- Third-party callback: next business day or the one after, never today, 10:00–16:00; nearest slot = same time on the first business day of the window, clamped to the hours.
- Second look: 3rd business day after the call, 12:00–18:00; once per call; only for turned-down products.
- Identity: DOB first, then phone_last4; one retry per question; second wrong answer to the same question ends the check.
- create_promise: two tries at most.
- Products in order of days_late descending, ties in get_account order; agree, read back and record per product.
- Close codes per [K]; nothing-recorded priority SYSF > HDNX > DSPT > TDN2L > TDN; CLMPD only when every product is claimed paid.

## Calendars used
- Call Wed 2026-10-14: business days after: 1 Thu 15 Oct, 2 Fri 16 Oct, 3 Mon 19 Oct, 4 Tue 20 Oct, 5 Wed 21 Oct, (Thu 22 closed), 6 Fri 23 Oct. Next business day 15 Oct; part-payment last date 16 Oct; Late last date 19 Oct; Middle last date 20 Oct (under [S]: 23 Oct); Early last date 14+14 = Wed 28 Oct; second look Mon 19 Oct; third-party window Thu 15 / Fri 16 Oct.
- Call Fri 2026-10-30: business days after: Mon 2, Tue 3, Wed 4, Thu 5 Nov, (Fri 6 closed), Mon 9 Nov. Early last date 30 Oct + 14 = Fri 13 Nov (a business day after R4; under [S] it was closed and the last date would roll to Mon 16 Nov).
- Call Wed 2026-10-21 15:00: tomorrow Thu 22 Oct is closed; the window is Fri 23 Oct and Mon 26 Oct.

## Cases

**G-01 (PUB-10, card 365.00, 8 days → Middle).** Offers 400 today → more than past_due → record 365.00 [S 5.4]. Today is valid. Mock fails the first create_promise → retry once [M, S 5.8] → ok. Every arrangement is full → promise / FULLPTP [K]. Verbatims: opening, read-back ending "Is that right?", "Your payment arrangement is recorded." only after ok, FULLPTP closing.

**G-02 (PUB-06, card 2125.10, 12 days → Middle).** Identity: wrong DOB once, right on repeat; wrong phone once, right on repeat → pass (per-question rule [M]); the mock has 1 wrong answer left, so nothing stops it. "Too much" → floor offered once: R2 floor = 2125.10/2 = 1062.55 → next multiple of 5 = 1065.00 (not [S]'s 637.50). It is a part payment → last date = min(2nd bd 16 Oct, Middle 20 Oct) = 16 Oct. She names Sunday 18 Oct → not a business day → first business day after = Mon 19 Oct, later than 16 Oct → last business day before the named day = Fri 16 Oct [S 5.6]. Record 1065.00 on 2026-10-16 → promise below past_due → PARTPTP.

**G-03 (PUB-01, card 420.00, 6 days → Early, call Fri 30 Oct 10:00).** Early last date = 13 Nov (a business day after R4). Vague "sometime next week" → ask once for the day [S 5.6]; "Friday next week" = Fri 6 Nov → closure day (R4) → first business day after = Mon 9 Nov ≤ 13 Nov → offer it. Full amount → FULLPTP, 420.00 on 2026-11-09. An agent using [S] would accept 6 Nov.

**G-04 (PUB-09, personal loan 2100.00, 28 days → Late).** No to today → attempt 1: full 2100.00 on next business day 15 Oct → no. Attempt 2: floor 700.00 on part-payment last date min(16 Oct, Late 19 Oct) = 16 Oct → no. Attempts used → turned down: note refused (2 attempts, last offer 700.00 on 16 Oct). Second look offered: 3rd bd = Mon 19 Oct; 14:30 is inside 12:00–18:00 → schedule_callback 2026-10-19 14:30. Nothing recorded, only a turned-down product with a booked second look → no_promise / TDN2L.

**G-05 (PUB-03, card 95.00, 4 days → Early).** No to today → attempt 1: full 95.00 on Early last date 28 Oct → no. Early has 1 attempt → turned down; the floor (50.00) is not offered. Note refused (1 attempt, 95.00 on 28 Oct). Second look offered once, declined → TDN.

**G-06 (PUB-08).** DOB wrong twice → second wrong answer to the same question → check ends, though the service still allows one more [M]. Phone digits never asked, no get_account, IDNO closing line → not_verified / IDNO.

**G-07 (PUB-02).** Asks what it is about instead of answering → explain once (no forbidden words; "personal details" not "account") → still declines → not_verified / IDREF.

**G-08 (PUB-07, partner answers, call Wed 21 Oct 15:00).** Callback never today; window = next bd Fri 23 Oct or Mon 26 Oct, 10:00–16:00 [S 5.6a]. "Tomorrow at three" = Thu 22 Oct, closed → same time on the first business day of the window: Fri 23 Oct 15:00 → accepted → schedule_callback 2026-10-23 15:00 → not_reached / TPCB.

**G-09 (PUB-05, flatmate, call 14 Oct 11:00).** "Tonight around seven" → today not allowed, 19:00 outside the hours → first business day of the window Thu 15 Oct, nearest end of the hours 16:00 → proposed once → declined → book nothing → not_reached / NOCON.

**G-10 (PUB-05, loan 780.00).** Asks for smaller monthly payments → restructuring transfer, no terms described [M] → transferred / XRST, no notes.

**G-11 (PUB-09).** Hospital → hardship: "I'm sorry to hear that.", no attempt, put through to Customer Care; he agrees → transfer support → transferred / XCARE, no notes after a transfer.

**G-12 (PUB-07, loan 540.00).** Bereavement → hardship line; refuses the transfer → note hardship (his words) on p1, no second look (hardship) → no_promise / HDNX.

**G-13 (PUB-02).** Paid on Monday at the branch → the paid line, note paid (branch, Monday) → only product claimed paid → paid / CLMPD.

**G-14 (PUB-13: p1 card 300.00 4 days Early; p2 loan 900.00 20 days Middle).** Order by days_late: p2 first, then p1 [S 5.9]. p2: "next Friday" = Fri 23 Oct > Middle last date Tue 20 Oct (R3) → offer 20 Oct → accepted → full 900.00 on 2026-10-20 (under [S] 23 Oct would be accepted). p1: 100 < floor 150.00 (R2: 300/2 = 150, already a multiple of 5; [S] floor 90 would accept 100) → offer 150 once → accepted for "this Friday" = 16 Oct ≤ part-payment last date 16 Oct → 150.00 on 2026-10-16. One arrangement below past_due → PARTPTP. Per-product read-back and recording, p2 before p1.

**G-15 (PUB-12: p1 card 510.00 16 d; p2 loan 1320.00 16 d; p3 car 140.00 7 d Early).** Order p1, p2 (tie, get_account order), p3. p1 dispute → note dispute. p2 paid yesterday by transfer → paid line, note paid. p3: no today → attempt 1 full 140.00 on Early last date 28 Oct → no → turned down (1 attempt), note refused. Second look offered (p3 turned down): Mon 19 Oct 17:00 (inside 12:00–18:00) → booked. Nothing recorded, not all paid → priority SYSF > HDNX > DSPT > TDN2L > TDN → DSPT, with DSPT's closing sentence.

**G-16 (PUB-11: p1 card 220.00 9 d; p2 loan 640.00 9 d; p3 car 75.00 3 d).** Order p1, p2 (tie), p3. p1 split "110 today and the rest at the end of the month" → one arrangement only, the first part: 110 ≥ floor 110.00 (R2: 220/2 = 110) and today ≤ 16 Oct → record 110.00 on 2026-10-14; say the rest stays overdue. p2: asks for a person → ask once whether happy to continue → "no, put me through" → transfer general. Transfer freezes: p1 stays, no notes for p2/p3 → transferred / XGEN.

## Coverage
- Every code row on the card except SYSF: the kit's mock fails create_promise at most once (PUB-10) and never fails get_account, so a two-failure close cannot be produced; it is covered by the brief text only.
- Identity paths: pass (most), one wrong answer per question then pass (G-02), second wrong on the same question (G-06), declined (G-07), third party (G-08, G-09). Not covered: day_month_swapped (no mock customer has DOB day ≤ 12 with a swap script here), unclear who answered, wrong number, deceased (all NOCON).
- Date classes: today (G-01, G-16), business day in range (G-14 card), weekend (G-02), closure day (G-03; G-08 for a callback), after the last date (G-14 loan), vague (G-03), past date — not covered. Weekday words: "this Friday", "next Friday", "Friday next week", "tomorrow".
- Amount classes: full, more than full (G-01), part in range at the floor boundary (G-16), below floor (G-14), too much (G-02), split (G-16).
- Minutes: R2 (G-02, G-14, G-16), R3 (G-14), R4 (G-03).
- Bands: Early (G-03, G-05, G-14 p1, G-15 p3), Middle (G-01, G-02, G-14 p2), Late (G-04).
