# Coverage audit: harrow.workflow.json

Rules: `harrow.rules.json`. Generator: `gen_harrow.py`. Model claude-opus-5-5, 115 s, $4.41, 9 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 65 | 27 | 0 | 2 | 6 | 100 |

## Top fixes

1. **R76** (contradicted): Outcome/reason/closing-sentence table: each situation maps to an outcome, reason code and closing sentence said verbatim.
   - why: A transfer that comes after a recorded arrangement (for example 'can I speak to someone' in wrapup, or hardship after recording) closes as promise/FULLPTP|PARTPTP, or with a blank reason, when it should close as transferred/XRST|XGEN|XCARE. That fails the close_call check on every transfer-after-recording case (this also covers R78, R80, R81, R82, R74 and R95).
   - fix: In the code of fin_transferred_restructuring, fin_transferred_human and fin_transferred_support, delete the `if rec and rec.lower() not in ('none','null'): vars['outcome']='promise'; vars['reason']=promise_reason` branch. Always set vars['outcome']='transferred' and vars['reason'] to 'XRST', 'XGEN' or 'XCARE' respectively. In close_call pre_process_code, never drop or blank `reason`.
2. **R29** (contradicted): Before recording, read back and record only after a clear yes; on a change, check the new value and read back again. With several products, agree, read back and record each before the next.
   - why: With several products the agent agrees all of them first and then reads them back and records them together, so the read-back, create_promise and 'Your payment arrangement is recorded.' sequence is in the wrong order for every multi-product case (this also covers R30 and R31).
   - fix: In the policy code, change advance(). As soon as a product reaches state 'agreed', go to confirm and read back "So that is {amount} for your {product} on {weekday, day month}. Is that right?". Call create_promise only after a clear yes. Only then call start_product(V, opn[0]) for the next open product. In ev_rec_after, speak "Your payment arrangement is recorded." right after each ok:true, not once in enter_wrapup. After the 2nd failure, speak "I'm sorry, I could not record that." right away (also when nothing else was recorded, before fin_sysf), then add_note service_error and continue with the next product.
3. **R84** (partial): No arrangement, product(s) turned down, second-look call booked: no_promise / TDN2L.
   - why: The terminal farewells say extra words beyond the mandated closing sentence, so the verbatim closing check fails on every second-look and deceased case (this also covers R17 and R91).
   - fix: Set end_tdn2l spoken_message to exactly "Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye." Move the booking sentence "Your second-look call is booked for {{second_look_text}} at {{sl_time}}." into offer_second_look, to be spoken after schedule_callback succeeds, before the transition to fin_tdn2l. Set end_deceased spoken_message to exactly "I am very sorry to hear that."
4. **R92** (partial): Several products, nothing recorded, no transfer: all claimed paid → CLMPD; otherwise most serious decides in order SYSF, HDNX, DSPT, TDN2L, TDN. Paid next to turned-down is TDN or TDN2L.
   - why: With several products, finalize() takes the ending from the first non-paid product in list order, not from the most serious one, so mixed cases (for example refused + dispute, or paid + hardship-declined) get the wrong no_promise reason code.
   - fix: In policy code finalize(), when nothing is recorded and there is no transfer: if every product is 'paid', close CLMPD. Otherwise pick the key by severity across all product states, in this order: service_error→SYSF, hardship_declined→HDNX, dispute→DSPT, refused with second look booked→TDN2L, refused/notalk→TDN. Treat 'paid' next to 'refused' as TDN/TDN2L. Also send any 'refused' product to fin_secondlook before closing, even if another product was recorded (R32).
5. **R93** (partial): `add_note` reason is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`, and text must contain the specified content per reason.
   - why: add_note only sends product_id and reason, so the required note content is never stored. Every refused/hardship/dispute/paid/service_error note case fails (this also covers R34, R35, R39, R59 and R31).
   - fix: Add a body field `text` (default "{{note_text}}") to the add_note tool. In note_next(), set vars['note_text'] per reason: refused → f"{attempts_used} attempts; last offer {prop_amount} on {prop_date}"; hardship → the customer's words (new extraction field hardship_words); dispute → what is disputed (extraction dispute_what); paid → how and when paid (extraction paid_how_when); service_error → f"create_promise failed after {create_promise_failure_count} tries". Also, in ev_settle, remove the multi(V) condition so "Thank you. A payment can take up to two business days to reach us." is spoken on single-product calls too.

## contradicted (2)

- **R29** (_harrow.md Document 1 Read-back_): Before recording, read back and record only after a clear yes; on a change, check the new value and read back again. With several products, agree, read back and record each before the next.
  - where: policy code advance()/readback(); confirm node
  - evidence: `if opn:
                start_product(V, opn[0], prefix)
                return
            agreed = [p for p in ids if state(V, p) == 'agreed']`
  - fix: In advance(), route to confirm (read-back) and then record after each product is agreed, before calling start_product for the next open product. Do not agree every product first and read them back together.
- **R76** (_harrow.md Document 4 table_): Outcome/reason/closing-sentence table: each situation maps to an outcome, reason code and closing sentence said verbatim.
  - where: fin_transferred_restructuring/human/support code
  - evidence: `if True and rec and rec.lower() not in ('none', 'null'):
            vars['outcome'] = 'promise'`
  - fix: In the fin_transferred_* nodes, drop the recorded_pids branch so a transfer always closes as transferred/XRST|XGEN|XCARE. Also remove the extra sentences added to end_tdn2l and end_deceased.

## partial (27)

- **R17** (_harrow.md mail 'Someone else picks up'_): Wrong number, customer died, or cannot tell who answered: close not reached. On death say only the sentence.
  - where: setup/opening_retry/third_party transitions -> fin_nocon / fin_deceased; end_deceased terminal
  - evidence: `terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye."`
  - fix: Set end_deceased spoken_message to exactly "I am very sorry to hear that." (drop "Thank you. Goodbye."), because the rule says to speak only that sentence.
- **R22** (_harrow.md Document 1 Security questions_): If they won't answer, say once the questions protect their personal details; if still not, or they ask again what it's about, close not verified (declined, IDREF).
  - where: ask_dob/ask_phone task_message; count_decline_* and qb_* code -> fin_declined
  - evidence: `refused if they refuse to answer the security question, say they do not want to talk, or ask AGAIN what the call is about instead of answering.`
  - fix: A second 'what is this about' that is extracted as 'refused' only takes decline_count to 1 and the agent asks again. Route refusal_dob/refusal_phone == refused straight to fin_declined when question_count_* >= 1, or when the protect-details line was already said.
- **R28** (_harrow.md mail 'Partial payments'_): Split payments: record only ONE arrangement per product, the first part, if at least the floor and date fits; say rest stays overdue and we will contact them; never record the second part.
  - where: policy code check_one (floor/part_deadline), recorded_guard; end_promise_part terminal
  - evidence: `"too_much_floor": "I understand. The smallest amount I can record is [floor]. The rest stays overdue and we will contact you about it."`
  - fix: Add a split-payment rule to the offer_amount/offer_when extraction: take only the first part. When a part amount (at least the floor, below the full amount) is agreed, have check_one/agree add 'The rest stays overdue and we will contact you about it.' at agreement time. Right now that line is only spoken on the too-much path.
- **R30** (_harrow.md Document 1 Read-back_): After each successful `create_promise` (`ok: true`) say the sentence word for word; never before.
  - where: policy code enter_wrapup -> wrapup on_enter tts
  - evidence: `"recorded": "Your payment arrangement is recorded."`
  - fix: Speak 'Your payment arrangement is recorded.' after each successful create_promise (in ev_rec_after, before moving to the next product). Today it is said once, after all products are recorded.
- **R31** (_harrow.md Document 1 Read-back_): If `create_promise` fails, try once more; if it fails again, say the apology, `add_note` reason `service_error`, and continue with other products.
  - where: policy code ev_rec_after (fail_max 2), note_next service_error, enter_wrapup rec_failed
  - evidence: `parts = [line] + [T('rec_failed', words=pg(V, p, 'words')) for p in bad]`
  - fix: Speak 'I'm sorry, I could not record that.' right after the second failure, even when no product was recorded (today that case goes to fin_sysf and the apology is never said). Also add a note text field to add_note that contains 'create_promise' and the number of tries.
- **R32** (_harrow.md mail 'Second look'_): When a product is turned down (ladder ran out or floor refused), offer once per call before goodbye a second-look call per AHS-5 5.7; customer picks time; book with `schedule_callback` and say the sentence.
  - where: fin_secondlook -> offer_second_look; schedule_callback#2; end_tdn2l spoken_message
  - evidence: `Your second-look call is booked for {{second_look_text}} at {{sl_time}}. Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye.`
  - fix: In finalize(), route to fin_secondlook whenever any product has state 'refused', even if another product was recorded (today final_route 'promise' skips the offer) or an earlier product was disputed or hardship.
- **R34** (_harrow.md mail 'Things customers say' already paid_): Already paid: say the sentence; no arrangement on that product; `add_note` reason `paid` with how and when paid.
  - where: policy code ev_settle (T('paid')), note_reasons paid -> record_note
  - evidence: `pre = T(kind, words=T('and').join(words)) if multi(V) else ''`
  - fix: Speak 'Thank you. A payment can take up to two business days to reach us.' for single-product calls too (remove the multi(V) condition in ev_settle). Also add a note text field to add_note that captures how and when the customer paid.
- **R35** (_harrow.md mail 'Things customers say' dispute_): Not mine / never had it: do not argue, no arrangement on that product, `add_note` reason `dispute` with what is disputed.
  - where: pol_dispute -> ev_settle state 'dispute'; note_reasons dispute -> record_note
  - evidence: `body.reason (string): default "{{note_reason}}"`
  - fix: Add a note text field to add_note stating what is disputed. Add 'Do not argue about a dispute' to the negotiate/confirm task_message.
- **R37** (_harrow.md mail 'Things customers say' person_): Wants a person: ask once the sentence; if no or asks again, `transfer_to_agent` queue `general`.
  - where: policy code ev_human (human_limit 2) -> xfer_general; ask_dob/ask_phone task_message
  - evidence: `"human_first": "I can help you with this now. Are you happy to continue with me?"`
  - fix: After human_first is spoken in negotiate, treat a 'no' to 'Are you happy to continue with me?' as a request for a person: add a human_pending flag that sends a stance refuse to pol_human/xfer_general instead of count_refusal.
- **R39** (_harrow.md Document 1 Things customers say_): If they decline transfer, do not push: `add_note` reason `hardship` on every product with their words, and close. A date or amount they then offer themselves is a normal arrangement.
  - where: hardship transition support_no -> hs_decline; ev_hs_decline/note_next -> record_note; finalize -> fin_hardship HDNX
  - evidence: `body.reason (string): default "{{note_reason}}"`
  - fix: add_note sends only product_id and reason, so the customer's own words are never stored. Add a text/details body field filled from an extraction of the hardship circumstance in their words (if the API allows it).
- **R40** (_harrow.md mail 'Things customers say' does not want to talk_): Say once the sentence; if repeated, close: before security questions declined; after, no arrangement with `refused` note on every open product, no second look.
  - where: opening_retry task_message + refuses -> fin_declined; ev_notalk (notalk_limit 2) + fin_secondlook skip -> fin_tdn
  - evidence: `If they said they do not want to talk: say "This will only take a moment."`
  - fix: In ask_dob/ask_phone ID_COMMON, have the first 'do not want to talk' get "This will only take a moment." (a second one -> fin_declined), instead of counting it as a plain refusal without the sentence.
- **R43** (_harrow.md Document 1 Closing_): Every call ends with the code's closing sentence then exactly one `close_call` as last tool call, with outcome and code; for a transfer the sentence is said just before `transfer_to_agent`.
  - where: fin_* code nodes + end_* terminals; xfer_* on_enter tts; close_call alwaysRunsAt end_of_call
  - evidence: `- If they ask for a person: the first time say "I can help you with this now. Are you happy to continue with me?" If they ask again or say no, call transfer_to_agent.`
  - fix: In ask_dob/ask_phone, have the model say "I am putting you through now. Please stay on the line." before calling transfer_to_agent, or route to xfer_general instead of the in-node tool.
- **R53** (_harrow.md AHS-5 5.4 rule table row below floor_): Offers less than the floor: say it cannot be recorded and offer the floor once; if refused, product turned down.
  - where: check_offer code: check_one below_floor branch; refuse()
  - evidence: `"below_floor": "I cannot record [named]. The smallest amount I can record is [floor]."`
  - fix: In refuse(), when offered_floor is 'yes' and the refused offer was the floor, mark the product 'refused' right away. Do not move on to the next offer on the attempt list.
- **R54** (_harrow.md AHS-5 5.4 row too much_): Full amount too much: offer the floor once, say the rest stays overdue and we will contact them, then agree date; floor refused = turned down, no further attempt.
  - where: check_offer code: too_much() / ev_offer too_much branch
  - evidence: `"too_much_floor": "I understand. The smallest amount I can record is [floor]. The rest stays overdue and we will contact you about it."`
  - fix: When the customer refuses the floor offered after 'too much', mark the product 'refused' right away. Today refuse() can still offer the next attempt, for example the floor on the part-payment last date.
- **R55** (_harrow.md AHS-5 5.4 row split_): Wants to split: record only the first part, as a part payment, if at least the floor.
  - where: check_offer code: check_one (amount between floor and full accepted, part_deadline applied)
  - evidence: `if pdl and amt is not None and amt < full_of(V, pid) and pdl < dl:`
  - fix: Add a 'split' instruction or extraction so that when the customer proposes several instalments, only the first amount is taken as the offer and recorded as a part payment if it is at least the floor.
- **R59** (_harrow.md AHS-5 5.5_): When band attempts are used, stop: product turned down, note `refused` with attempts made and last offer (amount and date).
  - where: refuse() sets state 'refused'; note_next -> record_note add_note reason refused
  - evidence: `body.reason (string): default "{{note_reason}}"`
  - fix: Give add_note a text field (pre_process_code or body) that holds the number of attempts made and the last offer's amount and date, taken from attempts_used, prop_amount and prop_date.
- **R74** (_harrow.md Document 4 intro_): Every `close_call` has one `outcome` (`promise`, `paid`, `transferred`, `no_promise`, `not_verified`, `not_reached`) and one `reason` code from the card; closing sentence said word for word before `close_call` (transfer: before `transfer_to_agent`).
  - where: close_call enums; fin_* code nodes; xfer_* on_enter tts
  - evidence: `vars['reason'] = str(vars.get('promise_reason') or '')`
  - fix: In the fin_transferred_* nodes, always set outcome transferred with XRST/XGEN/XCARE and never a blank reason. In ask_dob/ask_phone, make the agent say 'I am putting you through now. Please stay on the line.' before calling transfer_to_agent.
- **R75** (_harrow.md Document 4 intro_): The closing sentence is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.
  - where: xfer_* on_enter tts; ask_dob/ask_phone transfer_to_agent tool; end_* spoken_message
  - evidence: `- If they ask for a person: the first time say "I can help you with this now. Are you happy to continue with me?" If they ask again or say no, call transfer_to_agent.`
  - fix: In ask_dob/ask_phone, have the agent say 'I am putting you through now. Please stay on the line.' before transfer_to_agent, or route the transfer through the xfer_general node. Remove the extra 'Goodbye.' from the end_transferred_* terminals.
- **R78** (_harrow.md Document 4 table row PARTPTP_): At least one arrangement recorded, no transfer after it, at least one for less than overdue amount: promise / PARTPTP.
  - where: fin_promise transition -> end_promise_part; end_promise_part terminal spoken_message; fin_transferred_* code
  - evidence: `terminal: endedReason=promise_PARTPTP, spoken_message="Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."`
  - fix: PARTPTP must require no transfer after the recording: in fin_transferred_restructuring/human/support, drop the 'recorded_pids -> outcome promise' branch so a transfer after a recorded arrangement ends transferred/X*, not promise/PARTPTP.
- **R80** (_harrow.md Document 4 table row XRST_): Transferred to restructuring: transferred / XRST; sentence said before `transfer_to_agent`.
  - where: xfer_restructuring on_enter tts + transfer_to_agent#2 (queue restructuring); fin_transferred_restructuring code
  - evidence: `            vars['outcome'] = 'promise'
            vars['reason'] = str(vars.get('promise_reason') or '')`
  - fix: In fin_transferred_restructuring always set outcome transferred / reason XRST, even when recorded_pids is set (a transfer after the arrangement is not a promise ending).
- **R81** (_harrow.md Document 4 table row XGEN_): Transferred to a person on request (queue `general`): transferred / XGEN.
  - where: xfer_general on_enter tts + transfer_to_agent#4 (queue general); fin_transferred_human code
  - evidence: `NODE xfer_general [api_request] (passthrough)
  on_enter tts: "I am putting you through now. Please stay on the line."`
  - fix: In fin_transferred_human always set outcome transferred / reason XGEN; remove the recorded_pids promise override (e.g. a transfer requested in wrapup after recording).
- **R82** (_harrow.md Document 4 table row XCARE_): Transferred to Customer Care for hardship (queue `support`): transferred / XCARE.
  - where: xfer_support on_enter tts + transfer_to_agent#3 (queue support); fin_transferred_support code
  - evidence: `on_enter tts: "I am putting you through to Customer Care now. Please stay on the line."`
  - fix: In fin_transferred_support always set outcome transferred / reason XCARE; remove the recorded_pids promise override.
- **R84** (_harrow.md Document 4 table row TDN2L_): No arrangement, product(s) turned down, second-look call booked: no_promise / TDN2L.
  - where: offer_second_look -> fin_tdn2l; end_tdn2l terminal spoken_message
  - evidence: `spoken_message="Your second-look call is booked for {{second_look_text}} at {{sl_time}}. Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye."`
  - fix: Make end_tdn2l spoken_message exactly "Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye." (drop the added booking sentence).
- **R91** (_harrow.md Document 4 table row NOCON_): Someone else answered and no callback booked; wrong number; customer deceased; could not tell who answered: not_reached / NOCON.
  - where: fin_nocon/end_nocon; third_party, opening_retry always -> fin_nocon; fin_deceased/end_deceased
  - evidence: `terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye."`
  - fix: Outcome/reason are right on every NOCON path, but end_deceased speaks extra words. Set end_deceased spoken_message to the NOCON sentence "Thank you. Goodbye." unless the brief gives a separate deceased line.
- **R92** (_harrow.md Document 4 several products note_): Several products, nothing recorded, no transfer: all claimed paid → CLMPD; otherwise most serious decides in order SYSF, HDNX, DSPT, TDN2L, TDN. Paid next to turned-down is TDN or TDN2L.
  - where: policy code finalize() in check_offer and other policy nodes; fin_secondlook -> offer_second_look
  - evidence: `for s in sts:
                    if s != 'paid':
                        key = fk.get(s) or fk['default']
                        break`
  - fix: In finalize(), choose the ending by severity across all products (service_error > hardship > dispute > refused/second look) instead of the first unpaid product in list order.
- **R93** (_harrow.md Document 4 notes_): `add_note` reason is one of `refused`, `hardship`, `dispute`, `paid`, `service_error`, and text must contain the specified content per reason.
  - where: tool add_note; policy note_reasons / note_next()
  - evidence: `body.reason (string): default "{{note_reason}}"`
  - fix: Add a text field to add_note. Have note_next() build it per reason: attempts plus last offer (refused), customer's words (hardship), what is disputed (dispute), how/when paid (paid), 'create_promise' plus number of tries (service_error).
- **R95** (_harrow.openapi.json /close_call_): `close_call` is always the last tool call; nothing is accepted after it; `reason` required for every outcome.
  - where: tool close_call (alwaysRunsAt end_of_call) pre_process_code; fin_* code nodes
  - evidence: `vars['reason'] = str(vars.get('promise_reason') or '')`
  - fix: In fin_paid/fin_tdn/fin_tdn2l/fin_hardship/fin_dispute/fin_sysf/fin_transferred_*, fall back to 'FULLPTP' instead of '' when promise_reason is empty, and stop close_call pre_process_code from dropping reason.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | generator docstring + tool close_call reason enum | outcome_desc="From the dialler code card: promise, paid, transferred, no_promise, not_verified, not_reached." |
| R02 | superseded | superseded by  |  |
| R03 | implemented | setup code (dates from now) + prepare code (credit_card / loan types, 1-3 products, day bands) | raw = str(vars.get('now') or '').strip() |
| R04 | implemented | setup code: today/now_time derived from vars['now'] | nowdt = datetime.datetime.fromisoformat(raw[:16]) |
| R05 | implemented | every tool definition body.customer_id | body.customer_id (string): default "{{customer_id}}" |
| R06 | implemented | check_offer policy code check_one (weekend/holiday, deadline, floor guards) | "below_floor": "I cannot record [named]. The smallest amount I can record is [floor]." |
| R07 | implemented | opening on_enter tts | on_enter tts: "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded. Could I speak to {{first_name}} {{last_name}}, please?" |
| R08 | implemented | who1/who2 extraction + setup -> opening_retry; opening_retry always -> fin_nocon (NOCON) | unclear = anything else: 'hello?', 'who wants to know?', 'what's this about?', any question, silence. |
| R09 | implemented | system prompt | Once the right person is on the line, call them {{title}} {{last_name}}. |
| R10 | implemented | system prompt + node task_messages + negotiate aside handling | - Robot question: say "Yes, I am an automated assistant.", then continue. |
| R11 | implemented | system prompt + node task_messages | Scam question: they are free to hang up and call us on the number on the Corran Bay website, then continue. |
| R12 | implemented | system prompt + ask_dob/ask_phone/opening_retry/third_party task_message FORBID line | - Before both security questions are passed never say: overdue, arrears, missed, owe, debt, balance, payment, account, card, credit card, loan, car loan. |
| R13 | implemented | ask_dob / ask_phone task_message rules | - The questions are there to protect their personal details: say exactly that if they ask why, or will not answer, then ask the same question again. |
| R14 | implemented | third_party.task_message | Never say why you are calling or which department. Say that you are calling with a personal message for {{title}} {{last_name}}, and ask when they will be avail |
| R15 | implemented | third_party.task_message | If they offer to answer questions, pay or arrange anything for the customer: thank them, decline, and ask again when {{title}} {{last_name}} can be reached. |
| R16 | implemented | third_party.task_message + setup code: callback_text + tool schedule_callback | - If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed day, or if the time is outside 10:00-16:00 the nearest end of  |
| R17 | partial | setup/opening_retry/third_party transitions -> fin_nocon / fin_deceased; end_deceased terminal | terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye." |
| R18 | implemented | ask_dob -> ask_phone, tools verify_identity / verify_identity#2 | 2. -> ask_phone  if (verify_identity_response.data.verified equals "true" OR verify_identity_response.data.verified equals "True")  ["date of birth correct"] |
| R19 | implemented | ask_dob.task_message + verify_identity post_process_code | msg = 'Day and month look swapped. NOT a wrong answer. Ask for the date of birth again with the month as a word, for example 14 March 1988.' |
| R20 | implemented | verify_identity post_process_code (id_wrong_dob / id_wrong_phone) + transition id_route_* -> fin_failed | done = nw >= 2 or str(left) == '0' |
| R21 | implemented | fin_failed code + end_failed terminal; verify post LIMIT_TXT | terminal: endedReason=not_verified_IDNO, spoken_message="For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. G |
| R22 | partial | ask_dob/ask_phone task_message; count_decline_* and qb_* code -> fin_declined | refused if they refuse to answer the security question, say they do not want to talk, or ask AGAIN what the call is about instead of answering. |
| R23 | implemented | load_account (get_account) -> prepare code: statement | head = "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. " |
| R24 | implemented | SYSTEM PROMPT + negotiate/confirm/wrapup task_message | - Never ask how much the customer can pay. Never mention fees, credit file, recovery agents or court. |
| R25 | implemented | prepare code: statement + init_negotiation stage 'all' + to_one_by_one | statement += 'Can you pay the overdue amount in full today?' if len(items) == 1 else 'Can you pay all of these in full today?' |
| R26 | implemented | SYSTEM PROMPT; negotiate.task_message; prepare code (amounts set by the system) | - Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. |
| R27 | implemented | negotiate stance extraction + transition 7 -> check_offer before count_refusal; policy code refuse()/refused_list/too_much() | offer = names their own date, amount or period (a date or amount is NEVER a refusal) |
| R28 | partial | policy code check_one (floor/part_deadline), recorded_guard; end_promise_part terminal | "too_much_floor": "I understand. The smallest amount I can record is [floor]. The rest stays overdue and we will contact you about it." |
| R29 | contradicted | policy code advance()/readback(); confirm node | if opn:                 start_product(V, opn[0], prefix)                 return             agreed = [p for p in ids if state(V, p) == 'agreed'] |
| R30 | partial | policy code enter_wrapup -> wrapup on_enter tts | "recorded": "Your payment arrangement is recorded." |
| R31 | partial | policy code ev_rec_after (fail_max 2), note_next service_error, enter_wrapup rec_failed | parts = [line] + [T('rec_failed', words=pg(V, p, 'words')) for p in bad] |
| R32 | partial | fin_secondlook -> offer_second_look; schedule_callback#2; end_tdn2l spoken_message | Your second-look call is booked for {{second_look_text}} at {{sl_time}}. Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye. |
| R33 | implemented | policy code finalize() fin_keys; fin_secondlook code (notalk_count skip); single offer_second_look node | vars['sl_route'] = 'skip' if n >= 2 else 'offer' |
| R34 | partial | policy code ev_settle (T('paid')), note_reasons paid -> record_note | pre = T(kind, words=T('and').join(words)) if multi(V) else '' |
| R35 | partial | pol_dispute -> ev_settle state 'dispute'; note_reasons dispute -> record_note | body.reason (string): default "{{note_reason}}" |
| R36 | implemented | negotiate/confirm/wrapup transition topic new_plan -> xfer_restructuring (queue restructuring) -> fin_transferred_restructuring (XRST) | -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R37 | partial | policy code ev_human (human_limit 2) -> xfer_general; ask_dob/ask_phone task_message | "human_first": "I can help you with this now. Are you happy to continue with me?" |
| R38 | implemented | prepare code texts.hardship + hardship node + hardship transition support_yes -> xfer_support (queue support) -> fin_transferred_support XCARE | "hardship": "I'm sorry to hear that. I will put you through to our Customer Care team, who can help. Is that all right?" |
| R39 | partial | hardship transition support_no -> hs_decline; ev_hs_decline/note_next -> record_note; finalize -> fin_hardship HDNX | body.reason (string): default "{{note_reason}}" |
| R40 | partial | opening_retry task_message + refuses -> fin_declined; ev_notalk (notalk_limit 2) + fin_secondlook skip -> fin_tdn | If they said they do not want to talk: say "This will only take a moment." |
| R41 | implemented | system prompt + negotiate/confirm/wrapup/offer_second_look COMMON | - A question the facts do not answer: "I don't have that information." |
| R42 | implemented | prepare code note_next/finalize; notes_on_transfer False (xfer routes skip notes); load_account failure -> fin_sysf | # notes wait until the wrap-up has decided the ending: a transfer from the wrap-up adds no notes at all |
| R43 | partial | fin_* code nodes + end_* terminals; xfer_* on_enter tts; close_call alwaysRunsAt end_of_call | - If they ask for a person: the first time say "I can help you with this now. Are you happy to continue with me?" If they ask again or say no, call transfer_to_ |
| R44 | superseded | superseded by R71 |  |
| R45 | implemented | setup/prepare code isbd/next_bd; check_one weekend_or_holiday; fit_day; ev_accept | issues.append(('weekend_or_holiday', T('weekend_or_holiday', named=txt_short(nd), date=txt_short(nb)))) |
| R46 | implemented | setup code addbd | while c < n and guard < 4000:         d = d + datetime.timedelta(days=1) |
| R47 | implemented | prepare code resolve_when (weekday_rule this_week) | else:   # that weekday in the following calendar week                         delta = (7 - today.weekday()) + wd |
| R48 | superseded | superseded by R69 |  |
| R49 | superseded | superseded by R68 |  |
| R50 | implemented | prepare code check_one (dl = deadline_of; part deadline only when amt < full) | if pdl and amt is not None and amt < full_of(V, pid) and pdl < dl: |
| R51 | implemented | prepare code check_one part_deadline cap + below_floor check; setup part_deadline | pset(vars, pid, 'part_deadline', part.isoformat())   # 5.4 part-payment last date |
| R52 | implemented | prepare code check_one above_full with P above_full='agree' | agree(V, pid, na, nd, prefix=pre)   # the brief: above the full amount, record the full amount and say so |
| R53 | partial | check_offer code: check_one below_floor branch; refuse() | "below_floor": "I cannot record [named]. The smallest amount I can record is [floor]." |
| R54 | partial | check_offer code: too_much() / ev_offer too_much branch | "too_much_floor": "I understand. The smallest amount I can record is [floor]. The rest stays overdue and we will contact you about it." |
| R55 | partial | check_offer code: check_one (amount between floor and full accepted, part_deadline applied) | if pdl and amt is not None and amt < full_of(V, pid) and pdl < dl: |
| R56 | implemented | setup code: part_deadline; prepare code: part = min(part_raw, dl) | vars['part_deadline'] = addbd(today, 2).isoformat() |
| R57 | implemented | negotiate extraction stance + count_refusal -> refuse(); start_product sets attempts_used 1 per product | refuse = a no with no date and no amount, a flat refusal, or no answer ('I don't know'). |
| R58 | implemented | prepare code: rungs per band | rungs = [('full_or_floor', D('late_a1')), ('floor', part)] |
| R59 | partial | refuse() sets state 'refused'; note_next -> record_note add_note reason refused | body.reason (string): default "{{note_reason}}" |
| R60 | implemented | check_offer code: check_one date issues and vague handling (vague_again deadline) | "before_today": "I cannot record a day that has passed. Please choose a day from today on." |
| R61 | implemented | setup code callback_text; third_party.task_message | - If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed day, or if the time is outside 10:00-16:00 the nearest end of  |
| R62 | implemented | setup code second_look_date; offer_second_look.task_message | - If the time is outside 12:00-18:00: say the hours are 12:00 to 18:00 once and ask again. If the second time does not fit either, or they decline, call transit |
| R63 | implemented | ev_rec_after fail_max 2; recorded_guard / wrap_change | "wrap_change": "An arrangement already recorded cannot be changed on this call." |
| R64 | implemented | prepare code: order by days_late then index; register_product per product | order = sorted(range(len(prods)), key=lambda i: (-int(float(prods[i].get('days_late') or 0)), i)) |
| R65 | implemented | prepare/check_offer code: ev_settle/refuse -> advance(); xfer_* -> fin_transferred_* -> end_transferred_* | if opn:             start_product(V, opn[0], prefix) |
| R66 | implemented | tool verify_identity post_process_code; verify_identity#2 answer field description | msg = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R67 | implemented | prepare code: credit card floor gated on today_iso >= '2026-10-14' | if str(vars.get('today_iso')) >= '2026-10-14': |
| R68 | implemented | prepare code: floor computation per product type | floor = float(int(math.ceil(past_due / 2.0 / 5.0 - 1e-9)) * 5) |
| R69 | implemented | setup code: early_deadline/middle_deadline/late_deadline; prepare code days_late bands | vars['middle_deadline'] = addbd(today, 4).isoformat() |
| R70 | superseded | superseded by  |  |
| R71 | implemented | setup code HOL set | HOL = set(['2026-10-22', '2026-11-06', '2026-11-24', '2026-12-25', '2026-12-28']) |
| R72 | implemented | offer_second_look task_message, on_enter tts and tool schedule_callback#2 | at a time you choose between 12:00 and 18:00? |
| R73 | implemented | verify_identity post_process_code per-question counter; ask_dob/ask_phone transition -> fin_failed | done = nw >= 2 or str(left) == '0' |
| R74 | partial | close_call enums; fin_* code nodes; xfer_* on_enter tts | vars['reason'] = str(vars.get('promise_reason') or '') |
| R75 | partial | xfer_* on_enter tts; ask_dob/ask_phone transfer_to_agent tool; end_* spoken_message | - If they ask for a person: the first time say "I can help you with this now. Are you happy to continue with me?" If they ask again or say no, call transfer_to_ |
| R76 | contradicted | fin_transferred_restructuring/human/support code | if True and rec and rec.lower() not in ('none', 'null'):             vars['outcome'] = 'promise' |
| R77 | implemented | fin_promise code -> end_promise terminal spoken_message | terminal: endedReason=promise_FULLPTP, spoken_message="Thank you, {{title}} {{last_name}}. Your arrangement is in place. Goodbye." |
| R78 | partial | fin_promise transition -> end_promise_part; end_promise_part terminal spoken_message; fin_transferred_* code | terminal: endedReason=promise_PARTPTP, spoken_message="Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch a |
| R79 | implemented | finalize (all states paid -> fin_paid); fin_paid code; end_paid terminal spoken_message | terminal: endedReason=paid_CLMPD, spoken_message="Thank you for letting us know. Goodbye." |
| R80 | partial | xfer_restructuring on_enter tts + transfer_to_agent#2 (queue restructuring); fin_transferred_restructuring code |             vars['outcome'] = 'promise'             vars['reason'] = str(vars.get('promise_reason') or '') |
| R81 | partial | xfer_general on_enter tts + transfer_to_agent#4 (queue general); fin_transferred_human code | NODE xfer_general [api_request] (passthrough)   on_enter tts: "I am putting you through now. Please stay on the line." |
| R82 | partial | xfer_support on_enter tts + transfer_to_agent#3 (queue support); fin_transferred_support code | on_enter tts: "I am putting you through to Customer Care now. Please stay on the line." |
| R83 | implemented | fin_secondlook (notalk skip) -> fin_tdn; offer_second_look transition_to_fin_tdn; end_tdn terminal | terminal: endedReason=no_promise_TDN, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R84 | partial | offer_second_look -> fin_tdn2l; end_tdn2l terminal spoken_message | spoken_message="Your second-look call is booked for {{second_look_text}} at {{sl_time}}. Thank you for your time, {{title}} {{last_name}}. Speak to you then. Go |
| R85 | implemented | hardship node hs_answer support_no -> hs_decline -> finalize fin_keys hardship -> fin_hardship; end_hardship terminal | terminal: endedReason=no_promise_HDNX, spoken_message="Thank you for telling me. Take care, {{title}} {{last_name}}. Goodbye." |
| R86 | implemented | negotiate topic dispute -> pol_dispute -> fin_dispute; end_dispute terminal | terminal: endedReason=no_promise_DSPT, spoken_message="We will look into this and write to you. Goodbye." |
| R87 | implemented | load_account get_account_response.ok false -> fin_sysf; ev_rec_after fail_max 2 -> service_error -> fin_sysf; end_sysf terminal | terminal: endedReason=no_promise_SYSF, spoken_message="I'm sorry, our system is not responding. We will call you again. Goodbye." |
| R88 | implemented | ask_dob/ask_phone id_route exhausted -> fin_failed; end_failed terminal | terminal: endedReason=not_verified_IDNO, spoken_message="For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. G |
| R89 | implemented | count_decline_*/qb_*/opening_retry -> fin_declined; end_declined terminal | terminal: endedReason=not_verified_IDREF, spoken_message="I understand. You can use the Corran Bay app or visit any branch. Goodbye." |
| R90 | implemented | third_party transition -> fin_callback (not_reached/TPCB); end_callback terminal spoken_message | terminal: endedReason=not_reached_TPCB, spoken_message="Thank you, we will call back then. Goodbye." |
| R91 | partial | fin_nocon/end_nocon; third_party, opening_retry always -> fin_nocon; fin_deceased/end_deceased | terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye." |
| R92 | partial | policy code finalize() in check_offer and other policy nodes; fin_secondlook -> offer_second_look | for s in sts:                     if s != 'paid':                         key = fk.get(s) or fk['default']                         break |
| R93 | partial | tool add_note; policy note_reasons / note_next() | body.reason (string): default "{{note_reason}}" |
| R94 | implemented | tool create_promise body + pre_process_code; record_promise node; recorded_guard() | want = [('product_id', str(vars.get('rec_pid') or '')), ('amount', str(vars.get('rec_amount') or '')), ('date', str(vars.get('rec_date') or '')[:10])] |
| R95 | partial | tool close_call (alwaysRunsAt end_of_call) pre_process_code; fin_* code nodes | vars['reason'] = str(vars.get('promise_reason') or '') |
| R96 | implemented | tool create_promise pre_process_code; record_promise node | b[f] = float(w) |
| R97 | implemented | ask_dob (verify_identity field date_of_birth) -> ask_phone (verify_identity#2 field phone_last4); post_process_code | msg = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R98 | implemented | ask_phone all_verified transition -> load_account (get_account); prepare code reads product fields | 2. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True") |
| R99 | implemented | tool schedule_callback (third_party) and schedule_callback#2 (offer_second_look); pre_process_code to_time | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, from 10:00 to 16:00. |
| R100 | superseded | superseded by  |  |
