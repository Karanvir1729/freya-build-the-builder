# Coverage audit: kestrel.workflow.json

Rules: `kestrel.rules.json`. Generator: `gen_kestrel.py`. Model claude-fable-5-1, 168 s, $13.85, 11 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 96 | 9 | 0 | 7 | 10 | 122 |

3 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R117** (contradicted): Same table as R33 (listed as the overridden target of memo item 5); see R33 for every row. HARD applies for hardship-declined-transfer until 14 October 2026.
   - why: Today is 10 Oct 2026, before the memo's 14 Oct switch, so every hardship-declined-transfer case expects close_call no_promise/HARD but fin_hardship always sends HSHP (also fails R51).
   - fix: fin_hardship code: replace vars['reason'] = 'HSHP' with vars['reason'] = 'HARD' if vars['today_iso'] < '2026-10-14' else 'HSHP' (keep outcome 'no_promise'); add HARD to the close_call tool reason enum/description and to the FINS/finalize() hardship mapping used by the multi-product close.
2. **R106** (contradicted): From 14 October the third attempt ("final-offer repeat") is withdrawn: attempt 1 (F and S) amount in play on the next business day; attempt 2 (S only) the floor on the latest date. Never repeat an offer that has been turned down.
   - why: a1 = next_bd(today) resolves to today on any business-day call, so attempt 1 re-offers the already refused 'today' date (skipped as refused), collapsing the ladder to a single floor offer and breaking 'never repeat a turned-down offer' (also fails R67 one-by-one flow).
   - fix: prepare code: change a1 = next_bd(today) to a1 = addbd(today, 1) (next business day strictly after the call date) wherever the attempt-1 / start_product rung-0 date is computed, so attempt 1 is 'amount in play on {{a1}}' and attempt 2 the floor on the latest date, and the per-product ladder never asks about today again.
3. **R99** (contradicted): "Next <weekday>" is the first such weekday after the call date even in the same week; "this <weekday>" or a bare weekday is the same day; if the call is on that weekday, "this" means today and "next" means seven days later.
   - why: resolve_when turns 'next Friday' into +7 beyond the first Friday and bare/'this' Friday on a Friday into +7 instead of today, so read-back and create_promise dates are wrong in every weekday case.
   - fix: check_offer code resolve_when: delta = (wd - today.weekday()) % 7; if delta == 0: delta = 0 if qualifier in ('this', None) else 7; else: use delta for both 'next X' and 'this X'/bare X; remove the weekday_table_first_after_plus7 '+7' rule in setup.
4. **R69** (contradicted): One named date for everything is checked per product: a product whose latest date is earlier goes on its own latest date (said in the read-back); a closure day is moved per 4.6 for each product; others keep the named date.
   - why: fit_day moves a named Saturday/Sunday/closure day to next_bd while 4.6 and the spoken read-back say 'the nearest business day before the day you named', so multi-product closure-day cases get the wrong date (also fails R95).
   - fix: prepare code fit_day: replace dd = next_bd(dd) with nb = prev_bd(dd); dd = nb if nb >= today else next_bd(dd), mirroring check_one's closed_day_move == 'before' branch, so the 'bd' tag read-back and the proposed date agree.
5. **R98** (contradicted): For a vague period ("next week", "end of the month", "when I get paid"): ask once for the exact day; if none, propose the last business day of the current week (if the call is on it, the next business day after); if after the latest date, propose the latest date.
   - why: After the one 'Which exact day would that be?' ask, the vague branch always proposes the product's latest date instead of the last business day of the current week, so 'next week / when I get paid' cases get the wrong proposed date.
   - fix: check_offer code check_one vague branch: compute wk = lastbd_of_week(today); if today == wk: wk = addbd(today, 1); prop = wk if wk <= dl else dl; then set_prop(V, pid, pa, prop) and say T('vague_deadline', deadline=txt_short(prop), ...) instead of dl.

## contradicted (7)

- **R51** (_kestrel.md email of 6 Oct 'Hardship'_): If the customer declines the transfer, call `add_note` reason `hardship` on every product with the circumstance in the customer's own words, and close `no_promise` with the hardship code from the list (HARD in v3).
  - where: ev_hs_decline() -> note_next() add_note reason hardship with said_hardship text; fin_hardship sets reason HSHP
  - evidence: `vars['reason'] = 'HSHP'`
  - fix: The rule's code list v3 value is HARD; fin_hardship writes HSHP (generator relies on memo item 5 in force from 14 Oct). If the campaign runs before 14 Oct or the memo is not part of the brief, change FINS['hardship'] reason to 'HARD'; the add_note part (reason hardship, customer's own words via said_hardship) is implemented.
- **R67** (_kestrel.md email of 6 Oct 'Several products'_): `get_account` returns one to three products, each banded from its own `days_late`; state all first, ask once whether they can clear all today; if not, go through products one by one in the returned order without asking about today again.
  - where: prepare code: statement + question_all; to_one_by_one / start_product rung 0 at a1
  - evidence: `a1 = next_bd(today)                                     # 4.8 attempt 1: the next business day after the call date`
  - fix: next_bd(today) returns today itself when today is a business day, so the first per-product offer asks 'can you pay ... today' again; use a1 = addbd(today, 1) in prepare so the per-product ladder never re-asks about today.
- **R69** (_kestrel.md email of 6 Oct, 'Several products'_): One named date for everything is checked per product: a product whose latest date is earlier goes on its own latest date (said in the read-back); a closure day is moved per 4.6 for each product; others keep the named date.
  - where: prepare code: all_offer / fit_day (tags 'dl' and 'bd'), readback own_deadline / moved_bd
  - evidence: `dd = next_bd(dd)`
  - fix: fit_day moves a closed day to the NEXT business day while 4.6 (closed_day_move='before') and the read-back text ', the nearest business day before the day you named' require the previous business day; in fit_day use prev_bd(dd) (falling back to next_bd only if that is before today), as check_one does.
- **R98** (_kestrel.md CP-7 section 4.6 table row 5_): For a vague period ("next week", "end of the month", "when I get paid"): ask once for the exact day; if none, propose the last business day of the current week (if the call is on it, the next business day after); if after the latest date, propose the latest date.
  - where: check_offer code: check_one vague branch (vague_again = 'deadline')
  - evidence: `set_prop(V, pid, pa, dl)
                say(V, join([T('vague_deadline', deadline=txt_short(dl), words=pg(V, pid, 'words')), V['offer_question']]))`
  - fix: After the one 'Which exact day would that be?' ask, propose lastbd_of_week(monday of today) (the next business day after it when today is that day), and only the deadline when that day is after the deadline; currently it always proposes the product's latest date.
- **R99** (_kestrel.md CP-7 section 4.7_): "Next <weekday>" is the first such weekday after the call date even in the same week; "this <weekday>" or a bare weekday is the same day; if the call is on that weekday, "this" means today and "next" means seven days later.
  - where: check_offer code: resolve_when weekday_rule 'first_after_plus7' + setup weekday_table_first_after_plus7
  - evidence: `delta = (wd - today.weekday()) % 7 or 7   # bare / 'this X' = the first X after today; 'next X' = seven days later`
  - fix: In resolve_when make 'next X' = first X after today ((wd-today.weekday())%7 or 7) and 'this X'/bare X = same, except when today is X: 'this' = today (delta 0) and 'next' = +7; currently 'next' is always +7 beyond the first occurrence and bare/this on that weekday gives +7 instead of today.
- **R106** (_kestrel.md memo of 12 Oct item 2_): From 14 October the third attempt ("final-offer repeat") is withdrawn: attempt 1 (F and S) amount in play on the next business day; attempt 2 (S only) the floor on the latest date. Never repeat an offer that has been turned down.
  - where: prepare code: a1 = next_bd(today) used as attempt-1 date
  - evidence: `a1 = next_bd(today)                                     # 4.8 attempt 1: the next business day after the call date`
  - fix: next_bd(today) returns today when today is a business day, so attempt 1 repeats the opening 'today' offer (and is skipped as already refused); use a1 = addbd(today, 1) for the next business day after the call date.
- **R117** (_kestrel.md code list v3 closing codes table_): Same table as R33 (listed as the overridden target of memo item 5); see R33 for every row. HARD applies for hardship-declined-transfer until 14 October 2026.
  - where: fin_hardship code: reason always HSHP, no date switch for calls before 14 October 2026
  - evidence: `vars['reason'] = 'HSHP'`
  - fix: In fin_hardship code set vars['reason'] = 'HARD' if vars['today_iso'] < '2026-10-14' else 'HSHP' (and add HARD to the close_call reason description).

## partial (9)

- **R36** (_kestrel.md email of 6 Oct 'Identity'_): If the customer does not want to answer, explain once that the questions protect their account and nothing can be discussed without them; if they still decline, or ask again what the call is about instead of answering, close `not_verified` with code IDD.
  - where: ask_phone/ask_dob ID_COMMON question-back line; refusal_* extraction -> count_decline_* (2 -> fin_declined); qb_* nodes; fin_declined IDD
  - evidence: `then say that these questions are there to protect their account and nothing can be discussed without them, then ask the same question again.`
  - fix: In ask_phone/ask_dob task_message add an explicit line for a first refusal (decline_count = 1): say once that the questions protect their account and nothing can be discussed without them, then ask again; the explanation is currently only tied to a question back.
- **R63** (_kestrel.md email of 6 Oct, 'Other things customers say'_): Someone asking for a person gets one straight away, no "can I help you first": `transfer_to_agent` queue `general`, close `transferred` with code TRH.
  - where: ask_phone/ask_dob tool transfer_to_agent (queue general) -> fin_transferred_human; negotiate/confirm pol_human (human_limit 1) -> xfer_general; wrapup wrap_human
  - evidence: `description: Transfer the call to a human agent. CALL it straight away when the customer asks for a person; do not ask whether you can help first.`
  - fix: hardship node has no route for a human request: add the topic extraction (or an hs_answer value 'human') and a transition -> pol_human / xfer_general so a person is given straight away there too.
- **R64** (_kestrel.md email of 6 Oct, 'Other things customers say'_): If they do not want to talk, say once it will only take a moment; if repeated, close with code IDD before identity is confirmed, or RF after it (with a `refused` note on every product).
  - where: opening_retry task_message + who2 refuses -> fin_declined (IDD); negotiate pol_notalk notalk_limit 2 -> refused states + notes -> fin_refused (RF); ask_* count_decline -> fin_declined
  - evidence: `"notalk_first": "This will only take a moment.",                                        # R63 once`
  - fix: In ask_phone/ask_dob task_message add: if the customer says they do not want to talk, say once 'This will only take a moment.' and ask the question again (count_decline currently retries without that line).
- **R76** (_kestrel.md email of 6 Oct 'Closing'_): Thank the customer and say goodbye, then exactly one `close_call`, the last tool call of every call, always with an outcome and a code from the list (including promise closes, which carry PRM).
  - where: tool close_call (lifecycle end_of_call) reading outcome/reason from fin_* nodes; fin_promise sets promise/PRM
  - evidence: `V[P['reason_var']] = V['promise_reason']`
  - fix: enter_wrapup sets outcome='promise' but reason='' (promise_reasons is empty), so a call that drops during wrapup sends close_call without a code (pre_process_code pops the empty reason); set vars['reason']='PRM' in enter_wrapup when promise_reason() is empty.
- **R77** (_kestrel.md email of 6 Oct 'Closing'_): The dialler rejects a close without a code, including promise closes, which carry PRM.
  - where: fin_promise code; prepare code enter_wrapup
  - evidence: `V[P['reason_var']] = V['promise_reason']`
  - fix: enter_wrapup sets reason to '' (promise_reasons is {}), and close_call pre_process_code pops an empty reason: a hang-up during wrapup closes with outcome promise and no code. In enter_wrapup set V['reason'] = 'PRM' when promise_reason(V) is ''.
- **R95** (_kestrel.md CP-7 section 4.6 table row 2_): If the customer names a Saturday, Sunday or closure day not after the latest date, explain it would not process until the following business day and offer the nearest business day before the named day.
  - where: check_offer code: check_one closed_day_move 'before' + texts.weekend_or_holiday
  - evidence: `if P['closed_day_move'] == 'before':
                    nb = prev_bd(nd)`
  - fix: fit_day (used by all_offer / pay_claimed / change_claims for a day named for several products) moves to next_bd(dd) while the read-back tag says 'the nearest business day before the day you named'; use prev_bd there too (falling back to next_bd when before today).
- **R111** (_kestrel.md memo of 12 Oct item 5_): From 14 October the close for "hardship, customer declined the transfer" is `no_promise` / HSHP instead of HARD; all other outcome/code rows of code list v3 stay unchanged (see full table).
  - where: fin_* code nodes (FINS table): hardship -> no_promise/HSHP, all other rows present except not_verified/SVC
  - evidence: `"hardship": ("no_promise", "HSHP", "Thank you for your time, {{title}} {{last_name}}, and take care. Goodbye."),`
  - fix: Add a fin_id_service_error (not_verified / SVC) terminal and route verify_identity repeated failures (verify_identity_failure_count >= 3 or ok false repeatedly) in ask_phone/ask_dob to it.
- **R112** (_kestrel.md memo item 5_): From 14 October, several products and no promise: transfer code if transferred; else `paid`/AP if every product noted paid; else `no_promise` with the most serious note: `service_error` (SVC), `hardship` (HSHP, was HARD), `dispute` (DSP), `refused` (RF).
  - where: prepare code: finalize() (recorded -> promise, all paid -> paid, else first non-paid product state)
  - evidence: `for s in sts:
                    if s != 'paid':
                        key = fk.get(s) or fk['default']`
  - fix: finalize() takes the first non-paid product's state in list order, not the most serious; rank states service_error > hardship > dispute > refused and pick the highest-ranked across products.
- **R120** (_kestrel.md code list v3 note reasons table_): Note reasons: `refused` (attempts made and last offer amount/date), `hardship` (customer's words), `dispute` (what is disputed), `paid` (channel and day), `service_error` (the words "create_promise" and number of tries).
  - where: prepare/policy code: note_text (refused: attempts + last offer; service_error: 'create_promise failed, number of tries'; hardship/dispute/paid: customer_said words)
  - evidence: `return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)')`
  - fix: For reason paid the text only carries whatever the customer volunteered (customer_said asks for 'when or how', fallback '(not stated)'): make pol_paid / the paid line ask for the channel and the day when missing and extract both into the note text.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | tools verify_identity / verify_identity#2: baked field, answer description, pre_process digits, post_process_code | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R02 | implemented | tool verify_identity#2 post_process_code (hint / all_verified / verified / ok=false / wrong_answers_left branches) + ask_dob transitions | elif d.get('ok') is False or str(d.get('ok')).lower() == 'false': |
| R03 | implemented | tool add_note body (customer_id, product_id={{note_pid}}, reason={{note_reason}}, text) + prepare code note_reasons / note_next | "note_reasons": {"refused": "refused", "hardship": "hardship", "dispute": "dispute", "paid": "paid", "service_error": "service_error"} *unverified* |
| R04 | implemented | tool create_promise body + pre_process_code (amount forced to float, date to YYYY-MM-DD) + record_promise response_mapping data.ok -> rec_ok | want = [('product_id', str(vars.get('rec_pid') or '')), ('amount', str(vars.get('rec_amount') or '')), ('date', str(vars.get('rec_date') or '')[:10])] |
| R05 | implemented | tools transfer_to_agent (queue general), transfer_to_agent#2 (restructuring), transfer_to_agent#3 (support), #4 (general); customer_id baked in body | body.queue (string): default "restructuring" |
| R06 | implemented | generator header + prepare code (CP-7 values with memo overrides: 5th business day, twice minimum payment, HSHP) | "hardship": ("no_promise", "HSHP", ...),   # memo item 5: HSHP replaces HARD from 14 Oct *unverified* |
| R07 | superseded | superseded by  |  |
| R08 | implemented | prepare code: product loop (credit_card / loan types, days_late bands) + ordinals first/second/third | "ordinals": ["first", "second", "third"] |
| R09 | implemented | setup code (parses now as YYYY-MM-DDTHH:MM), opening tts ({{first_name}} {{last_name}}), tool bodies ({{customer_id}}), terminals ({{title}} {{last_name}}) | nowdt = datetime.datetime.fromisoformat(raw[:16]) |
| R10 | implemented | setup code (today from vars['now']) + prepare/check_offer code today_of / resolve_when relative to today_iso | raw = str(vars.get('now') or '').strip() |
| R11 | implemented | every tool definition body.customer_id default "{{customer_id}}" including close_call | body.customer_id (string): default "{{customer_id}}" |
| R12 | implemented | prepare/check_offer policy code (check_one: deadline, floor, business-day guards) + create_promise pre_process_code guard + negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. The only offer you may make is the current offer in STATE, |
| R13 | implemented | opening on_enter tts + opening.task_message | on_enter tts: "This is the digital assistant of Kestrel Bank. Please note that this call is recorded. Am I speaking with {{first_name}} {{last_name}}?" |
| R14 | implemented | opening on_enter tts / opening_retry task_message | on_enter tts: "This is the digital assistant of Kestrel Bank. Please note that this call is recorded. Am I speaking with {{first_name}} {{last_name}}?" |
| R15 | implemented | system prompt + ask_phone.task_message | Once identity is confirmed, address the customer as {{title}} {{last_name}}. |
| R16 | implemented | opening extraction who1 description (and who2) | customer = they confirm they are {{first_name}} {{last_name}}: 'yes', 'speaking', 'that's me', or they say the customer's own name. |
| R17 | implemented | setup transition 5 -> opening_retry; opening_retry transition 6 -> fin_unclear (not_reached/UNC) | 6. -> fin_unclear  if always  ["always"] |
| R18 | implemented | opening_retry.task_message | If the person asked a question, answer it in one short sentence first: who you are -> 'I am Kestrel Bank's digital assistant.'; a robot or AI -> say exactly |
| R19 | implemented | system prompt 'Always' item 1 (also opening_retry, ID_COMMON, negotiate COMMON) | - If asked whether you are a robot or an AI: say exactly "I am Kestrel Bank's digital assistant.", then continue. |
| R20 | implemented | system prompt 'Always' item 2 (also opening_retry, ID_COMMON, negotiate COMMON) | - If asked whether this is a scam: say they are welcome to hang up and call the number on the back of their card or on their statement, then continue. |
| R21 | implemented | opening.task_message, opening_retry.task_message, third_party.task_message, ask_phone/ask_dob ID_COMMON | Never say why you are calling; never say arrears, overdue, late, collections, debt, payment, instalment or any product name. |
| R22 | implemented | third_party.task_message STRICT line | STRICT: Say only that it is a personal banking matter that you can only discuss with {{title}} {{last_name}}, and ask when he or she can be reached. Nothing mor |
| R23 | superseded | superseded by R113 |  |
| R24 | superseded | superseded by  |  |
| R25 | implemented | tool schedule_callback (date YYYY-MM-DD, time HH:MM) + third_party transition 1 -> fin_callback (not_reached/CBK) | 1. -> fin_callback  if (schedule_callback_response.data.ok equals "true" OR schedule_callback_response.data.ok equals "True")  ["callback booked"] |
| R26 | implemented | third_party.task_message + transition 4 (transition_to_fin_no_callback) -> fin_no_callback (not_reached/NCB) | - If the day or time is outside the window, propose the nearest slot inside it, ONCE (the counter below says whether you already did). |
| R27 | implemented | third_party transition 3 -> fin_wrong_number (not_reached/WN); also setup/opening_retry wrong_number routes | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R28 | implemented | third_party transition -> fin_deceased (tp_status deceased); fin_deceased code; end_deceased terminal spoken_message | terminal: endedReason=not_reached_DEC, spoken_message="Please accept my condolences. Goodbye." |
| R29 | implemented | third_party.task_message STRICT paragraph | a relative cannot answer security questions, cannot be told anything about the account and cannot act for the customer on this call; if they offer to help or to |
| R30 | implemented | ask_phone (verify_identity baked field phone_last4) -> ask_dob (verify_identity#2 baked field date_of_birth); route on verified | 1. -> ask_dob  if (verify_identity_response.data.verified equals "true" OR verify_identity_response.data.verified equals "True")  ["phone digits correct"] |
| R31 | implemented | ask_dob.task_message + verify_identity#2 pre_process_code (FIELDS answer:date, ORDER 'dmy') | call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 19 |
| R32 | implemented | ask_phone / ask_dob transitions on wrong_answers_left "1" and "0" -> fin_failed; verify_identity post_process_code | 2. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "1")  ["second wrong answer"] |
| R33 | implemented | verify_identity post_process_code else branch (first wrong answer, wrong_answers_left 2: no route fires, model asks again) | d['what_to_do_next'] = 'Wrong answer. Tell the customer it does not match our records and ask again: What are the last four digits of the phone number we hold f |
| R34 | implemented | verify_identity#2 post_process_code hint branch (checked before the wrong-answer branches) | d['what_to_do_next'] = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month as a word, for examp |
| R35 | implemented | fin_failed code (not_verified/IDF) + end_failed terminal spoken_message; verify post MAX_WRONG line | spoken_message="I am sorry, for security I cannot continue by phone. You can use the Kestrel mobile app or visit a branch. Thank you, goodbye." |
| R36 | partial | ask_phone/ask_dob ID_COMMON question-back line; refusal_* extraction -> count_decline_* (2 -> fin_declined); qb_* nodes; fin_declined IDD | then say that these questions are there to protect their account and nothing can be discussed without them, then ask the same question again. |
| R37 | implemented | ask_dob transition 1 -> load_account on all_verified; load_account pre_action get_account | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True")  ["identity verifi |
| R38 | implemented | prepare code: statement built per product, then the question; spoken as negotiate on_enter tts {{say_next}} | statement += 'Your ' + w + ' has an overdue amount of ' + fmt(pd) + ', ' + str(dl_) + ' days overdue. ' |
| R39 | implemented | system prompt + negotiate/confirm/hardship/wrapup task_message COMMON line | - Nothing else is on the table: no discount, no waiver, no payment holiday, no plan, no fees, no credit file, no legal action, no 'collectors'. |
| R40 | implemented | prepare code: statement (single vs several products) spoken as negotiate on_enter tts {{say_next}} | statement += 'Are you able to clear the overdue amount today?' |
| R41 | implemented | negotiate.task_message + COMMON block (also confirm/hardship/wrapup) | Never ask the customer how much they can pay: the system proposes every amount. |
| R42 | implemented | too_much() in policy code (offered_floor once, else refuse) + texts too_much_floor; prepare code floor per product | "too_much_floor": "I understand. I can offer [floor] for your [words]. The remainder stays overdue and we will be in touch about it." |
| R43 | superseded | superseded by  |  |
| R44 | implemented | too_much() and check_one() in policy code: floor already offered -> refuse(V, pid) | if pg(V, pid, 'offered_floor') == 'yes' and g(V, 'mode') != 'hardship': |
| R45 | implemented | negotiate stance extraction + transition 7 -> check_offer before count_refusal; check_one() applies 4.5/4.6 checks | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R46 | implemented | negotiate transition 10 -> count_refusal; refuse() advances attempts_used along the per-band ladder built in prepare code | refuse = a flat refusal, a no with no date and no amount ('no', 'I can't', 'not today'), or a non-answer that avoids the question ('I don't know', 'maybe'). |
| R47 | implemented | refuse() in policy code: skips rungs in refused_offers, exhausts ladder; state_line 'never offer them again' | s += ' Offers already refused: ' + ', '.join([x.replace('@', ' on ') for x in rl]) + ': never offer them again.' |
| R48 | implemented | refuse() sets state refused; note_text() refused line; finalize() default -> fin_refused (no_promise, RF) | return ('%s: turned down. Attempts made: %d. Last offer: %s on %s.' % (w, max(n, 1), fmt(a), d.isoformat() if d else '') |
| R49 | implemented | ev_hardship() texts.hardship spoken as hardship on_enter tts; hardship.task_message 'Make NO persuasion attempt'; hardship transition 1 -> xfer_support (queue support) -> fin_transferred_support | "hardship": "I am sorry to hear that. Would you like me to put you through to our customer care team?" |
| R50 | implemented | hardship transition 1 -> xfer_support (transfer_to_agent#3 queue 'support') -> fin_transferred_support sets transferred/TSP | 1. -> xfer_support  if (hs_answer equals "support_yes")  ["the customer accepts the support team"] |
| R51 | contradicted | ev_hs_decline() -> note_next() add_note reason hardship with said_hardship text; fin_hardship sets reason HSHP | vars['reason'] = 'HSHP' |
| R52 | implemented | hardship transition 2 -> check_offer; ev_hardship stores hs_date/hs_amount and ev_hs_decline replays ev_offer; agree -> confirm -> record_promise -> fin_promise | 2. -> check_offer  if (offer_kind equals "exact" OR offer_ref equals "floor" OR offer_ref equals "full")  ["the customer names a date or an amount"] |
| R53 | implemented | negotiate/confirm/hardship/wrapup task_message (COMMON) + system prompt | - Nothing else is on the table: no discount, no waiver, no payment holiday, no plan, no fees, no credit file, no legal action, no 'collectors'. Never ask the cu |
| R54 | implemented | prepare code: readback() texts readback_item/readback_tail; confirm on_enter tts {{readback_line}}; confirm transition 2 -> rec_next -> record_promise | "readback_item": "[words], [amount], [when]", "readback_sep": "; your ", "own_deadline": ", which is the latest date I can record for it", "moved_bd": ", the ne |
| R55 | implemented | confirm transition 1 -> change_offer; prepare code ev_change -> check_one -> agree -> advance -> readback/confirm | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R56 | implemented | prepare code recorded_guard + text wrap_change; wrapup task_message; wrap_change node | # one promise per product: a recorded promise is never reopened or recorded again (the brief's change sentence) |
| R57 | implemented | prepare code ev_rec_after (state recorded only if rec_ok true) + enter_wrapup 'Your promise is recorded.'; COMMON 'Never say that a promise is recorded.' | ok = g(V, 'rec_ok').lower() == 'true' |
| R58 | implemented | prepare code ev_rec_after (fail_max 3), note_text service_error, finalize -> fin_service_error; end_service_error terminal | return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2)) |
| R59 | implemented | prepare code enter_wrapup: after_recorded appended once (wrap_done guard), after rec_next has recorded every agreed promise | "after_recorded": "We will email you a confirmation of this arrangement." |
| R60 | implemented | negotiate transition 5 -> pol_paid; prepare code ev_settle/note_text (reason paid, customer_said 'when or how'); fin_paid + end_paid terminal | terminal: endedReason=paid_AP, spoken_message="Payments made today show on our side on the next business day. Thank you for letting me know, {{title}} {{last_na |
| R61 | implemented | negotiate transition 6 -> pol_dispute; prepare code ev_settle (state dispute, no promise), note_text reason dispute with product words; fin_dispute -> end_dispute | "dispute": "I understand. I will not take a promise for your [words]." |
| R62 | implemented | negotiate/confirm/wrapup transitions topic new_plan -> xfer_restructuring (transfer_to_agent#2 queue restructuring) -> fin_transferred_restructuring | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R63 | partial | ask_phone/ask_dob tool transfer_to_agent (queue general) -> fin_transferred_human; negotiate/confirm pol_human (human_limit 1) -> xfer_general; wrapup wrap_human | description: Transfer the call to a human agent. CALL it straight away when the customer asks for a person; do not ask whether you can help first. |
| R64 | partial | opening_retry task_message + who2 refuses -> fin_declined (IDD); negotiate pol_notalk notalk_limit 2 -> refused states + notes -> fin_refused (RF); ask_* count_decline -> fin_declined | "notalk_first": "This will only take a moment.",                                        # R63 once |
| R65 | implemented | system_prompt + negotiate/confirm/hardship/wrapup task_message (COMMON) | - Never invent figures, dates or reasons. A question you cannot answer from the tools: say "I don't have that information." |
| R66 | implemented | prepare code: per-product loop (floor, days_late band, deadline, register_product) | days_late = int(float(p.get('days_late') or 0)) |
| R67 | contradicted | prepare code: statement + question_all; to_one_by_one / start_product rung 0 at a1 | a1 = next_bd(today)                                     # 4.8 attempt 1: the next business day after the call date |
| R68 | implemented | prepare code: register_product attempts_used per pid; start_product sets attempts_used 1 | pset(V, pid, 'attempts_used', 1) |
| R69 | contradicted | prepare code: all_offer / fit_day (tags 'dl' and 'bd'), readback own_deadline / moved_bd | dd = next_bd(dd) |
| R70 | implemented | prepare code: readback() + readback_tail; rec_next loops agreed products in pids order -> record_promise | "readback_tail": ". Shall I record that?" |
| R71 | implemented | prepare code: note_next (notes=True, note_reasons refused/hardship/dispute/paid/service_error) -> record_note | if st in P['note_reasons'] and pg(V, p, 'noted') == 'no': |
| R72 | implemented | prepare code: ev_settle / settle_claims set state per product then advance() to the next open product | # disputed products are settled one by one (the single topic would have settled every open product; extended |
| R73 | implemented | xfer_* api nodes -> fin_transferred_* directly; prepare code defer_notes / notes_on_transfer=False | # notes wait until the wrap-up has decided the ending: a transfer from the wrap-up adds no notes at all |
| R74 | implemented | prepare code: ev_rec_after (fail_max 3 -> state service_error, rec_next continues) + note_text service_error | return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2)) |
| R75 | implemented | end_* terminals spoken_message | terminal: endedReason=promise_PRM, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R76 | partial | tool close_call (lifecycle end_of_call) reading outcome/reason from fin_* nodes; fin_promise sets promise/PRM | V[P['reason_var']] = V['promise_reason'] |
| R77 | partial | fin_promise code; prepare code enter_wrapup | V[P['reason_var']] = V['promise_reason'] |
| R78 | implemented | tool close_call definition (outcome enum, customer_id default, lifecycle end_of_call) | body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"] |
| R79 | implemented | prepare code: per-product loop on days_late, addbd(today, 5) | deadline = addbd(today, 5)                                   # band S (and over 45): 5th business day (memo item 1) |
| R80 | superseded | superseded by R104 |  |
| R81 | superseded | superseded by R108 |  |
| R82 | implemented | prepare/check_offer code: check_one floor and full checks | if na < fl_ - 0.005: |
| R83 | implemented | setup code and prepare code: HOL set and BWD | HOL = set(['2026-10-30', '2026-11-20', '2026-12-24', '2026-12-25', '2026-12-28', '2026-12-31']) |
| R84 | implemented | generator HOLIDAYS from spec calendar (memo item 4 announced Founders' Day 2026-10-30) | HOLIDAYS = [h["date"] for h in SPEC["calendar"]["holidays"]]          # R83/R109: CP-7 4.3 + memo item 4 (Founders' Day) |
| R85 | implemented | check_offer code: check_one weekend_or_holiday branch and fit_day | elif not isbd(nd): |
| R86 | superseded | superseded by R113 |  |
| R87 | implemented | check_offer code: check_one (agree / below_floor / above_full branches) | above_full="agree",                                     # 4.5: record the full amount |
| R88 | implemented | check_offer code: check_one | if not issues: |
| R89 | implemented | check_offer code: check_one above_full branch | "above_full": "The overdue amount is [full], so I will record [full].",                 # 4.5: record the full amount |
| R90 | implemented | check_offer code: check_one below_floor (offered_floor once, then refuse) | "below_floor": "[named] cannot be recorded. The lowest amount I can record for your [words] is [floor]. The remainder stays overdue and we will be in touch abou |
| R91 | implemented | too_much code node: too_much() with offered_floor once, then refuse() | "too_much_floor": "I understand. I can offer [floor] for your [words]. The remainder stays overdue and we will be in touch about it.", |
| R92 | implemented | negotiate.task_message (COMMON) + system prompt last conduct line | Never ask the customer how much they can pay: the system proposes every amount. |
| R93 | implemented | check_offer code: check_one (before_today / after_deadline / isbd branches) | if nd < t: issues.append(('before_today', ...)) elif nd > dl: issues.append(('after_deadline', ...)) elif not isbd(nd): *unverified* |
| R94 | implemented | check_offer code: check_one -> agree when no issues | if not issues:                 agree(V, pid, na, nd) |
| R95 | partial | check_offer code: check_one closed_day_move 'before' + texts.weekend_or_holiday | if P['closed_day_move'] == 'before':                     nb = prev_bd(nd) |
| R96 | implemented | check_offer code: check_one after_deadline branch (nd = dl) + count_refusal -> refuse() | "after_deadline": "The latest date I can record for your [words] is [deadline], the last day that can be recorded." |
| R97 | implemented | check_offer code: check_one before_today branch + texts.before_today | "before_today": "[named] has already passed; it must be a day from today onwards." |
| R98 | contradicted | check_offer code: check_one vague branch (vague_again = 'deadline') | set_prop(V, pid, pa, dl)                 say(V, join([T('vague_deadline', deadline=txt_short(dl), words=pg(V, pid, 'words')), V['offer_question']])) |
| R99 | contradicted | check_offer code: resolve_when weekday_rule 'first_after_plus7' + setup weekday_table_first_after_plus7 | delta = (wd - today.weekday()) % 7 or 7   # bare / 'this X' = the first X after today; 'next X' = seven days later |
| R100 | implemented | negotiate extraction stance + check_offer code: refuse() / rung() too_much | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R101 | superseded | superseded by R106 |  |
| R102 | implemented | check_offer code: refuse() k >= len(L) -> state refused -> note_next reason 'refused' -> fin_refused | if k >= len(L):                 pset(V, pid, 'state', 'refused')                 V['offer_verdict'] = 'exhausted' |
| R103 | implemented | generator FINS hardship (HSHP), setup HOL (Founders' Day), prepare code band S 5 BD, floor twice minimum | "hardship": ("no_promise", "HSHP", "Thank you for your time, {{title}} {{last_name}}, and take care. Goodbye."),   # memo item 5: HSHP replaces HARD from 14 Oct |
| R104 | implemented | prepare code: band F/S deadline and rungs | deadline = addbd(today, 5)                                   # band S (and over 45): 5th business day (memo item 1) |
| R105 | implemented | prepare code: band split on days_late (1-10 -> 21 calendar days / prev_bd, one rung; else 5th business day, two rungs) | deadline = addbd(today, 5)                                   # band S (and over 45): 5th business day (memo item 1) |
| R106 | contradicted | prepare code: a1 = next_bd(today) used as attempt-1 date | a1 = next_bd(today)                                     # 4.8 attempt 1: the next business day after the call date |
| R107 | implemented | prepare code: refuse() skips rungs in refused_offers; state_line 'never offer them again' | s += ' Offers already refused: ' + ', '.join([x.replace('@', ' on ') for x in rl]) + ': never offer them again.' |
| R108 | implemented | prepare code: floor per product type | floor = min(2.0 * float(p.get('minimum_payment')), past_due)   # memo item 3: twice the minimum payment, never more than the overdue amount |
| R109 | implemented | setup/prepare code: HOL set and BWD | HOL = set(['2026-10-30', '2026-11-20', '2026-12-24', '2026-12-25', '2026-12-28', '2026-12-31']) |
| R110 | implemented | setup/prepare code: HOL set does not contain 2026-10-26, isbd() treats it as a business day | HOL = set(['2026-10-30', '2026-11-20', '2026-12-24', '2026-12-25', '2026-12-28', '2026-12-31']) |
| R111 | partial | fin_* code nodes (FINS table): hardship -> no_promise/HSHP, all other rows present except not_verified/SVC | "hardship": ("no_promise", "HSHP", "Thank you for your time, {{title}} {{last_name}}, and take care. Goodbye."), |
| R112 | partial | prepare code: finalize() (recorded -> promise, all paid -> paid, else first non-paid product state) | for s in sts:                     if s != 'paid':                         key = fk.get(s) or fk['default'] |
| R113 | implemented | setup code: callback_text (today after now up to 18:00, next 2 business days 09:00-18:00); schedule_callback time field HH:MM | lines.append(txt(nbd) + ' (' + nbd.isoformat() + '), from 09:00 up to 18:00 included.') |
| R114 | implemented | ask_phone -> ask_dob order; fin_failed route on wrong_answers_left 1; opening on_enter tts | 2. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "1")  ["second wrong answer"] |
| R115 | implemented | tool close_call body (outcome enum, reason) fed by every fin_* code node which sets both outcome and reason | body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"] |
| R116 | superseded | superseded by R111 |  |
| R117 | contradicted | fin_hardship code: reason always HSHP, no date switch for calls before 14 October 2026 | vars['reason'] = 'HSHP' |
| R118 | implemented | wrapup transitions -> wrap_human/xfer_restructuring, hardship -> xfer_support, then fin_transferred_* code overriding outcome/reason set by enter_wrapup | vars['outcome'] = 'transferred' |
| R119 | implemented | prepare/policy code: note_next (one add_note per product in note_reasons, noted=='no'), defer_notes + ev_human/ev_wrap_human routing straight to xfer_* without note_next; tool add_note reason from NOTE_ENUM | if st in P['note_reasons'] and pg(V, p, 'noted') == 'no': |
| R120 | partial | prepare/policy code: note_text (refused: attempts + last offer; service_error: 'create_promise failed, number of tries'; hardship/dispute/paid: customer_said words) | return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)') |
| R121 | superseded | superseded by R112 |  |
| R122 | implemented | prepare/policy code: finalize (key = fk['promise'] when any product is 'recorded') and enter_wrapup setting outcome/reason; fin_promise -> end_promise | if 'recorded' in sts: |
