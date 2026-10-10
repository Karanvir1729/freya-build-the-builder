# Brief G — Corran Bay Bank, missed-payment calls by the automated assistant (raw material)

Four documents, forwarded to the build team as one pack by Collections Operations on Friday 9 October 2026. They are reproduced as received: the operations manager's mail, the extract of the Arrears Handling Standard she attached, the minutes of Friday's campaign review, and the dialler's code card.

---

## Document 1 — Mail from Collections Operations

**From:** Fenella Marsh, Collections Operations Manager
**To:** Assistant Build Team
**Cc:** Ewan Quayle (Dialler); Jo Pritchard (Conduct & Compliance)
**Date:** Thursday 1 October 2026, 17:20
**Subject:** Missed-payment calls: how the assistant should behave

Hello team,

Here is the long version of what we went through on Tuesday. The figures (bands, last dates, floors, closure days, hours) are in the Arrears Handling Standard, AHS-5; I attach section 5. Where my mail and the Standard say different things, go with the Standard. The codes the dialler accepts are on Ewan's code card; I will forward it when he has re-printed it. We have a campaign review on Friday the 9th and I expect a few decisions to come out of it, so I will send the minutes on as well.

**Who we ring.** Personal customers who are 1 to 45 days behind on one, two or three products: a credit card, a personal loan, a car loan. The dialler passes `customer_id`, `first_name`, `last_name`, `title` (Mr or Ms) and `now`, the date and time of the call in the form `2026-10-14T11:00`. Every date the assistant works out runs from `now`. `customer_id` goes into every tool call. Our systems take whatever they are given (a promise on a Sunday, a promise for one pound), so the assistant has to keep the rules itself.

**Opening.** Every call starts, word for word: "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded." Then: "Could I speak to {first_name} {last_name}, please?" Only a yes, "speaking", "that's me", or the person saying their own name, counts. "Hello?", "who wants to know?" or "what's this about?" do not: ask the same question again, once. If after the second ask it is still not clear who you are talking to, close the call (not reached). If they ask something first, answer it, then ask; that ask is the second one. Once the right person is on the line, call them {title} {last_name}. If anyone asks whether this is a robot: "Yes, I am an automated assistant." and carry on. If anyone asks whether this is a scam: say they are free to hang up and call us on the number on the Corran Bay website, and carry on.

**What nobody hears before the security questions are passed.** None of these words: overdue, arrears, missed, owe, debt, balance, payment, account, and no product name either (card, credit card, loan, car loan). That includes the reason you give for the security questions. Conduct listen for "account" in particular, because the old script used it in the security question ("to access your account") and that alone told a flatmate what the call was about. Say instead that the questions are there to protect their personal details.

**Someone else picks up.** Say that you are calling with a personal message for {title} {last_name}, and ask when they will be available. Nothing else: not what it is about, not the bank's department. A relative or partner cannot answer the security questions and cannot arrange anything on the customer's behalf; if they offer, thank them, decline and go back to when the customer can be reached. We never call back the same day: the window is in AHS-5 5.6a. If what they say fits the window, book it with `schedule_callback` (date, time as HH:MM). If not, propose the nearest slot that fits, once. If they turn that down, book nothing. If the number is not the customer's, or they tell you the customer has died ("I am very sorry to hear that." and nothing more), or you cannot tell who answered, close as not reached. Ewan's card has the codes.

**Security questions.** Two, one at a time, date of birth first, then the last four digits of the phone number we hold. `verify_identity` after each answer. The date of birth goes to the service as YYYY-MM-DD; customers say dates day first, so a date given only in numbers is day, month, year. If the service answers with the hint `day_month_swapped`, ask for the date again with the month as a word; that does not count as a wrong answer. Our rule is per question: each question may be answered wrongly once and asked again; a second wrong answer to the SAME question ends the check. A wrong answer to the first question and a wrong answer to the second question is still a pass if the repeat answers are right. (The service has its own total limit of three wrong answers; ours bites first or at the same time, never later.) When the check ends, do not say what the call was about; say the line on the code card and close as not verified. If they will not answer, say once that the questions are there to protect their personal details. If they still will not, or if instead of answering they ask again what it is about, close as not verified (declined).

**After the security questions.** Call `get_account`. Say "I'm calling from Corran Bay Bank's Payments Support team about a missed payment." and then one sentence per product: the product in words ("your credit card ending 4821", "your personal loan", "your car loan"), the overdue amount, and how many days it is overdue. Products are taken in the order in AHS-5 5.9, not in the order the system lists them, and that order holds for the sentences too. Nothing about consequences: no fees, no credit file, no recovery agents, no court.

**Asking.** With one product, the first question is word for word: "Can you pay the overdue amount in full today?" With several: "Can you pay all of these in full today?" Then, if not, product by product. The assistant never asks how much the customer can pay, in any wording: it proposes every amount. A date or an amount the customer offers is never a refusal; check it against the Standard and move on. When the customer simply says no (no date, no amount), that is where the attempt ladder in AHS-5 5.5 starts. Never offer again something they have already turned down. "Too much" is handled in 5.4.

**Partial payments.** Part payments are fine (they are better than nothing) but they have to come in quickly, so they have a shorter last date than full payments: see 5.4. If the customer wants to split, part now and the rest later, we record only ONE arrangement per product: the part they are paying first, if it is at least the floor and the date fits. Tell them the rest stays overdue and we will contact them about it. Do not try to record the second part.

**Read-back.** Before recording, read it back: "So that is {amount} for your {product} on {weekday, day month}. Is that right?" Record only after a clear yes. If they change something, check the new value and read back again. With several products, agree, read back and record each product before you move to the next one. After each successful `create_promise` (`ok: true`), say, word for word: "Your payment arrangement is recorded." Never say it before. If `create_promise` fails, try once more. If the second try fails too, say "I'm sorry, I could not record that.", add a note with reason `service_error`, and go on with the other products if there are any.

**Second look.** This is new for this campaign and Jo is keen on it. When a product ends with no arrangement because the customer turned down the offers (the ladder ran out, or they turned down the floor), the assistant offers, once per call and before the goodbye, a "second-look call": a colleague rings them back to go through it again. The day and the hours are in AHS-5 5.7; the customer chooses the time. If they agree, book it with `schedule_callback` and say "Your second-look call is booked for {weekday, day month} at {HH:MM}." Only for turned-down products: not for disputes, already-paid, hardship, or someone who just does not want to talk. One second-look call per call, even if two products were turned down.

**Things customers say.**
- Already paid: "Thank you. A payment can take up to two business days to reach us." No arrangement on that product; `add_note` reason `paid`, with how and when they say they paid.
- Not mine / never had it: do not argue, no arrangement on that product, `add_note` reason `dispute` with what they dispute.
- Wants a plan, lower monthly amounts, a payment holiday: do not describe anything, `transfer_to_agent` queue `restructuring`.
- Wants a person: ask once, "I can help you with this now. Are you happy to continue with me?" If they say no or ask again, `transfer_to_agent` queue `general`.
- Illness, bereavement, job loss, anything like it: "I'm sorry to hear that." No attempt of any kind, not even the first. Tell them you will put them through to our Customer Care team, who can help, and `transfer_to_agent` queue `support`. If they say they do not want to be put through, do not push: `add_note` reason `hardship` on every product, with the circumstance in their own words, and close. If they then offer a date or an amount themselves, that is a normal arrangement.
- Does not want to talk: say once "This will only take a moment." If they say it again, close (before the security questions: declined; after: no arrangement, with a `refused` note on every product still open, and no second look).
- Anything you cannot answer from the tools: "I don't have that information."

**Notes.** Every product that ends the call without an arrangement gets one `add_note`, single product or several, unless the call was transferred (a transfer freezes everything: arrangements already recorded stay, nothing else is recorded, no notes) or we never got as far as `get_account`.

**Closing.** Every call ends with the closing sentence for its code and then exactly one `close_call`, the last tool call, with an outcome and a code from the card. For a transfer, the closing sentence is said just before `transfer_to_agent`.

Unrelated: the team photo is now on Thursday 15 October at 12:30 in the atrium. And please stop booking meeting room 3 for lunch.

Fenella

---

## Document 2 — Attachment: Arrears Handling Standard AHS-5, section 5 (extract)

*Corran Bay Bank — Arrears Handling Standard, AHS-5, issue 4, approved 1 September 2026. Section 5: Missed-payment calls made by the automated assistant. Sections 1–4 and 6–9 are not included.*

### 5.1 Business days and closure days

A business day is Monday to Friday, excluding the bank's closure days. For the rest of 2026 the closure days are:

| Date | Day | Reason |
|---|---|---|
| 2026-10-22 | Thursday | St Corran's Day |
| 2026-11-13 | Friday | core banking cut-over (planned) |
| 2026-11-24 | Tuesday | Regatta Day |
| 2026-12-25 | Friday | Christmas Day |
| 2026-12-28 | Monday | Boxing Day (substitute) |

No arrangement may be dated on a Saturday, a Sunday or a closure day. The call date counts as day 0; "the n-th business day after the call date" counts the first business day after the call date as the 1st.

### 5.2 Weeks and weekday words

A week runs Monday to Sunday. "This <weekday>" and a weekday named on its own mean that weekday in the current week if it is still to come (today included), otherwise in the following week. "Next <weekday>" means that weekday in the following week (the week after the current one), whatever day the call is made. "Tomorrow" is the calendar day after the call date, business day or not.

### 5.3 Bands, last dates and attempts

Each product is banded on its own `days_late`.

| Band | `days_late` | Last date for a full payment | Attempts |
|---|---|---|---|
| Early | 1 to 7 | the calendar day 14 days after the call date; if that is not a business day, the first business day after it | 1 |
| Middle | 8 to 20 | the 6th business day after the call date | 2 |
| Late | 21 to 45 | the 3rd business day after the call date | 2 |
| over 45 | treated as Late | | |

### 5.4 Amounts, floors and part payments

The floor is the smallest amount that may be recorded.

| Product | Floor |
|---|---|
| credit_card | `minimum_payment` |
| personal_loan | `instalment_amount` |
| car_loan | `instalment_amount` |

| The customer | Rule |
|---|---|
| agrees to the full overdue amount (`past_due`) | full payment: any valid date up to the band's last date |
| offers an amount from the floor up to but not including `past_due` | part payment: accept the amount; the date may be no later than the **part-payment last date** (below) |
| offers more than `past_due` | record `past_due` |
| offers less than the floor | say it cannot be recorded and offer the floor, once; if refused, the product is turned down |
| says the full amount is too much | offer the floor, once, and say that the rest stays overdue and we will contact them about it; then agree the date; if the floor is refused, the product is turned down (no further attempt) |
| wants to split (part now, rest later) | record only the first part, as a part payment, if it is at least the floor |

**Part-payment last date:** the 2nd business day after the call date, or the band's last date if that is earlier.

### 5.5 Attempt ladder

An attempt is used when the customer says no with no date and no amount, refuses flatly, or does not answer. Attempts are counted per product; every product starts at attempt 1.

| Attempt | Early | Middle | Late |
|---|---|---|---|
| 1 | full amount on the band's last date | full amount on the band's last date | full amount on the next business day after the call date |
| 2 | — | floor on the part-payment last date | floor on the part-payment last date |

When the band's attempts are used, stop: the product is turned down (note `refused`, with the number of attempts made and the last offer, amount and date).

### 5.6 Dates the customer names

| The customer names | Rule |
|---|---|
| today, or a business day up to the last date that applies (full or part payment) | accept |
| a Saturday, Sunday or closure day up to that last date | offer the first business day after it; if that is later than the last date, offer the last business day before the named day |
| a day later than the last date | say that the last date is the latest day that can be recorded, and offer it; if refused, it counts as an attempt |
| a day before today | it cannot be recorded; ask for a day from today on |
| a vague time ("next week", "end of the month", "payday") | ask once for the exact day; if none, propose the last date that applies |

### 5.6a Callback for a third party

A callback is booked on the next business day after the call date or the business day after that, never the call date itself, at a time from 10:00 to 16:00, both included. If the time offered does not fit, propose the same time on the first business day in the window (or, if the time is outside the hours, the nearest end of the hours on that day).

### 5.7 Second-look call

On the 3rd business day after the call date, at a time the customer chooses from 12:00 to 18:00, both included. If the time named is outside these hours, say the hours once and ask again; if the second time does not fit either, book nothing.

### 5.8 Recording

`create_promise` is called at most twice for the same arrangement (one retry). An arrangement already recorded is not changed in the same call.

### 5.9 Several products

Products are dealt with in order of `days_late`, the most days late first; products with the same `days_late` keep the order in which `get_account` returned them. Bands, floors, last dates and attempts are per product. A dispute, an already-paid claim or a turned-down product does not end the call; go on to the next product. A transfer ends the call; arrangements already recorded stay.

---

## Document 3 — Minutes of the missed-payment campaign review

**Corran Bay Bank — Collections Operations**
**Meeting:** Missed-payment campaign review (assistant go-live)
**Date:** Friday 9 October 2026, 10:00–11:15, room 3 (sandwiches were in room 2)
**Present:** Fenella Marsh (chair), Ewan Quayle, Jo Pritchard, Ravi Doshi (Treasury Ops), Mairi Lennox (Card Services)
**Minutes:** Ravi Doshi

1. **Go-live.** Confirmed for the first dialler run on Wednesday 14 October 2026. The assistant will be checked against these minutes from that day.

2. **Card floor.** Mairi showed that customers who pay one minimum payment on a card are back in arrears within a month. Agreed: from go-live the smallest amount the assistant records on a credit card is **half of the overdue amount (`past_due`), rounded up to the next multiple of 5**, and never more than `past_due`. Loans stay at the instalment amount. Mairi to update the card scripts for the human team as well.

3. **Middle band.** Treasury want the 8–20 day customers to pay before the month-end run. Agreed: their last date for a full payment is **the 4th business day after the call date**. Early and Late bands stay as they are. The question of widening the Early band to 10 days was discussed; no change for now, Fenella to bring numbers in November.

4. **Cut-over.** Core banking cut-over has been brought forward by the vendor to **Friday 6 November 2026**. Payment processing is closed on that day. Friday 13 November is an ordinary working day again. Ewan to tell the dialler vendor; nobody to book leave on the 6th.

5. **Second look.** Jo reported that the pilot second-look calls were well received. No change to the rules; the 12:00–18:00 hours stay.

6. **Wrong-answer rule.** Ewan asked whether we should move to the identity service's three-in-total rule. No: we keep one retry per question. No change.

7. **AOB.** The Christmas lunch is on Friday 11 December. The Treasury dashboard will be moved to the new BI tool in January.

Actions: Mairi (card scripts), Ewan (vendor, cut-over), Fenella (Early band numbers, November).

---

## Document 4 — Dialler code card (printed copy)

*Dialler — closing codes for the automated assistant, card v2, 28 September 2026.*

Every `close_call` has one `outcome` from the dialler's list (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from this card. The closing sentence is said, word for word, before `close_call` (for a transfer, before `transfer_to_agent`).

| Situation | `outcome` | `reason` | Closing sentence |
|---|---|---|---|
| at least one arrangement recorded, no transfer after it, every arrangement for the full overdue amount | promise | FULLPTP | "Thank you, {title} {last_name}. Your arrangement is in place. Goodbye." |
| at least one arrangement recorded, no transfer after it, at least one arrangement for less than the overdue amount | promise | PARTPTP | "Thank you, {title} {last_name}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye." |
| every product claimed as already paid, nothing recorded | paid | CLMPD | "Thank you for letting us know. Goodbye." |
| transferred to restructuring | transferred | XRST | "I am putting you through now. Please stay on the line." |
| transferred to a person on request (queue `general`) | transferred | XGEN | "I am putting you through now. Please stay on the line." |
| transferred to Customer Care, hardship (queue `support`) | transferred | XCARE | "I am putting you through to Customer Care now. Please stay on the line." |
| no arrangement; product(s) turned down; no second-look call booked; or customer would not continue after the security questions | no_promise | TDN | "Thank you for your time, {title} {last_name}. Goodbye." |
| no arrangement; product(s) turned down; second-look call booked | no_promise | TDN2L | "Thank you for your time, {title} {last_name}. Speak to you then. Goodbye." |
| hardship, customer did not want Customer Care | no_promise | HDNX | "Thank you for telling me. Take care, {title} {last_name}. Goodbye." |
| customer disputes | no_promise | DSPT | "We will look into this and write to you. Goodbye." |
| bank system failed (two failed tries of `create_promise`, or `get_account` failing) | no_promise | SYSF | "I'm sorry, our system is not responding. We will call you again. Goodbye." |
| security questions failed | not_verified | IDNO | "For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. Goodbye." |
| customer would not answer the security questions | not_verified | IDREF | "I understand. You can use the Corran Bay app or visit any branch. Goodbye." |
| someone else answered, callback booked | not_reached | TPCB | "Thank you, we will call back then. Goodbye." |
| someone else answered and no callback booked; wrong number; customer deceased; could not tell who answered | not_reached | NOCON | "Thank you. Goodbye." |

**Several products, nothing recorded, no transfer:** if every product is claimed paid, CLMPD. Otherwise the most serious situation on the call decides, in this order: SYSF, HDNX, DSPT, TDN2L, TDN. (A product claimed paid next to a turned-down one is TDN or TDN2L.)

**Notes (`add_note`):** `reason` is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`. The `text` must contain: refused — the number of attempts made and the last offer (amount and date); hardship — what the customer said, in their words; dispute — what is disputed; paid — how and when the customer says they paid; service_error — "create_promise" and the number of tries.
