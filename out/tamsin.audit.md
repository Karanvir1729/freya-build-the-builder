# Coverage audit: tamsin.workflow.json

Rules: `tamsin.rules.json`. Generator: `gen_tamsin.py`. Model claude-opus-5-5, 132 s, $4.71, 10 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 70 | 26 | 1 | 3 | 6 | 106 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R45** (contradicted): Say once the sentence; if repeated, close: before security questions declined (IDREF); after, no arrangement (TDN) with a `refused` note on every open product, no second look.
   - why: After verification, a repeated no-talk sets every open product to 'refused', and finalize then sends it to fin_refused (second look → TDN2L or TDN with a second-look offer), which breaks both the no-second-look rule and the plain TDN close; finalize also picks the reason from the first non-paid product instead of the most serious one.
   - fix: Policy ev_notalk: when c >= notalk_limit after verification, still write add_note reason 'refused' for each open/agreed product, but set the product state to 'notalk' (not 'refused') and set vars['final_route']='fin_tdn'. In finalize(), check final_route == 'fin_tdn' first and route to fin_tdn (outcome no_promise, reason TDN, farewell 'Thank you for your time, {{title}} {{last_name}}. Goodbye.') with no second look. Also change finalize to rank states by severity (service_error > hardship > dispute > refused > notalk/paid), sending 'refused' to fin_refused and treating paid next to turned-down as TDN/TDN2L. Make sure ask_dob/ask_phone_* task_message says 'This will only take a moment.' on the first no-talk and routes the second one to the IDREF close.
2. **R33** (contradicted): With several products, agree, read back and record each product before moving to the next.
   - why: With several products, advance() calls start_product for the next open product before any read-back, so all products are read back and recorded at the end; this breaks the agree→read back→record order per product, and the 'Your payment arrangement is recorded.' sentence is not said after each successful create_promise.
   - fix: Policy advance()/agree(): when a product becomes 'agreed', go straight to the confirm node with readback_line for that product only ('So that is {amount} for your {product} on {weekday day month}. Is that right?'). On confirm=yes, run record_promise for it. In ev_rec_after on create_promise ok:true, speak 'Your payment arrangement is recorded.' (set it as the next on_enter line), and only then call start_product(V, opn[0]) for the next open product. Remove the batch read-back in enter_wrapup.
3. **R77** (partial): `get_account` is refused until both questions are passed; if it fails, close as system failure.
   - why: nodes['load_account']['transitions'] is overwritten with [always('prepare')], so a failing get_account never reaches fin_service_error and the call cannot close as no_promise/SYSF.
   - fix: Generator: delete the line `nodes["load_account"]["transitions"] = [fl.always("prepare")]` (or replace it with an ordered list). load_account transitions must be: 1) -> fin_service_error if get_account_response.data.ok not_equals true/True (or get_account_failure_count greater_than 0); 2) always -> prepare. fin_service_error sets outcome=no_promise, reason=SYSF, and end_service_error speaks 'I'm sorry, our system is not responding. We will call you again. Goodbye.'
4. **R92** (partial): Transferred to restructuring: `transferred`/`XRST`, sentence said before `transfer_to_agent`.
   - why: The transfer sentences ('I am putting you through now. Please stay on the line.' / '...to Customer Care now...') are on_enter tts of code nodes, which don't speak; also, identity-step transfers call transfer_to_agent directly with no sentence, so every transfer case misses its mandatory sentence before transfer_to_agent.
   - fix: Turn xfer_restructuring, xfer_general and xfer_support into api_request nodes: on_enter tts holds the sentence (XRST/XGEN: 'I am putting you through now. Please stay on the line.'; XCARE: 'I am putting you through to Customer Care now. Please stay on the line.') and pre_actions call transfer_to_agent with queue restructuring/general/support, then route to fin_transferred_*. In ask_dob/ask_phone_a/ask_phone_b, remove the transfer_to_agent tool and add an is_tool_call/intent transition to xfer_general for the second request for a person (or a 'no' to 'Are you happy to continue with me?'). Do the same in negotiate by setting human_pending in ev_human so the next 'no' goes to xfer_general and is not counted as a refusal.
5. **R105** (partial): `add_note` reason is one of `refused`,`hardship`,`dispute`,`paid`,`service_error`; text must contain the listed content per reason.
   - why: note_text reads vars['customer_said'], but no node writes it, so the paid, dispute and hardship notes say '(not stated)' instead of how/when they paid, what is disputed, or the hardship in their own words.
   - fix: Add a free-text extraction field customer_said to the negotiate, confirm and hardship (pol_hardship) nodes: 'customer's own words: for already-paid, how and when they paid; for a dispute, what is disputed; for hardship, their circumstance'. In the negotiate task_message, on an already-paid claim, say 'Thank you. A payment can take up to two business days to reach us.' and ask how and when they paid before calling add_note. Have note_text use customer_said for reasons paid/dispute/hardship, and keep 'number of attempts and last offer amount+date' for refused and 'create_promise, number of tries: N' for service_error.

## contradicted (3)

- **R33** (_tamsin.md Document 1 'Read-back'_): With several products, agree, read back and record each product before moving to the next.
  - where: policy advance(): starts the next open product before any read-back; all agreed products are read back together, then recorded
  - evidence: `if opn:
                start_product(V, opn[0], prefix)
                return`
  - fix: In advance()/agree(), send each agreed product to confirm -> record_promise before calling start_product for the next open product.
- **R38** (_tamsin.md Document 1 'Second look'_): Second look only for turned-down products: not disputes, already-paid, hardship or not wanting to talk. One per call even if two products turned down.
  - where: policy finalize / ev_notalk -> fin_refused
  - evidence: `if c >= int(P['notalk_limit']):
                for p in pids(V):
                    if state(V, p) in ('open', 'agreed'):
                        pset(V, p, 'state', 'refused')`
  - fix: Give no-talk closes their own state or final_route that goes to fin_tdn instead of fin_refused. Have finalize route to fin_refused whenever any product is 'refused', not only when it is the first non-paid state.
- **R45** (_tamsin.md Document 1 'Things customers say' does not want to talk_): Say once the sentence; if repeated, close: before security questions declined (IDREF); after, no arrangement (TDN) with a `refused` note on every open product, no second look.
  - where: opening_retry (IDREF); ev_notalk -> finalize -> fin_refused
  - evidence: `"notalk_first": "This will only take a moment."`
  - fix: After verification, a repeated no-talk must go to fin_tdn (TDN) after the refused notes, never fin_refused (second look). In ask_dob/ask_phone, say "This will only take a moment." on the first no-talk.

## missing (1)

- **R62** (_tamsin.md Document 2 section 5.4 rule table row split_): Wants to split: record only the first part, as part payment, if at least the floor.
  - fix: Add a 'split' value to the stance/offer extraction (or the per_product handling) so that only the first part is recorded as a part payment when it is at least the floor; otherwise fall back to the floor offer.

## partial (26)

- **R20** (_tamsin.md Document 1 'Someone else picks up'_): Wrong number, customer deceased (say only the sentence), or cannot tell who answered: close not reached (NOCON).
  - where: setup/opening_retry/third_party transitions -> fin_wrong_number/fin_unclear/fin_deceased; end_deceased terminal
  - evidence: `terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye."`
  - fix: In FINS['deceased'], set the end_deceased spoken_message to exactly "I am very sorry to hear that." (remove the extra "Thank you. Goodbye.") so only the required sentence is spoken.
- **R31** (_tamsin.md Document 1 'Partial payments'_): Split payments: record only ONE arrangement per product, the first part, if at least the floor and date fits; tell them the rest stays overdue and we will contact them; never record the second part.
  - where: check_one agrees a single amount at or above the floor; end_promise_part farewell
  - evidence: `spoken_message="Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye."`
  - fix: Add an extraction/instruction for a split offer ('50 now, 50 next week'): take only the first part as offer_amount/offer_when, and say right away that the rest stays overdue and we will contact them.
- **R32** (_tamsin.md Document 1 'Read-back'_): Read back before recording; record only after a clear yes; on change, check and read back again; several products: agree, read back, record each before the next.
  - where: confirm node (readback_line) -> rec_next only on confirm=yes; change_offer re-checks
  - evidence: `"readback_item": "[amount] for your [words] [when]"`
  - fix: With several products, read back and record each product before starting the next (see R33). For today/tomorrow, use 'on {weekday day month}' in the read-back instead of 'today, ...'.
- **R34** (_tamsin.md Document 1 'Read-back'_): After each successful `create_promise` (`ok: true`) say the sentence word for word; never before.
  - where: enter_wrapup wrap_line (wrapup on_enter tts), after all records
  - evidence: `"recorded": "Your payment arrangement is recorded."`
  - fix: Say 'Your payment arrangement is recorded.' after each create_promise that returns ok: true (in ev_rec_after), not once after all products.
- **R35** (_tamsin.md Document 1 'Read-back'_): If `create_promise` fails, try once more; if it fails again, say the sentence, `add_note` reason `service_error`, continue with other products.
  - where: ev_rec_after fail_max=2 retry, state service_error, note_text; enter_wrapup rec_failed
  - evidence: `return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2))`
  - fix: Speak 'I'm sorry, I could not record that.' right after the second failure, even when no product is recorded (now it is only in wrap_line, which runs only if something was recorded).
- **R36** (_tamsin.md Document 1 'Second look'_): When a product is turned down (ladder ran out or floor refused), offer once per call before goodbye a second-look call (AHS-5 5.7, customer chooses time); if agreed, `schedule_callback` and say the sentence.
  - where: finalize -> fin_refused (on_enter tts + schedule_callback#2) -> fin_tdn2l
  - evidence: `- After the tool result, say exactly: "Your second-look call is booked for {{secondlook_text}} at <HH:MM>."`
  - fix: Also offer the second look when a product was refused but another was recorded (finalize now routes to fin_promise). Use txt_short (no year) for secondlook_text.
- **R37** (_tamsin.md Document 1 'Second look'_): If agreed, book with `schedule_callback` (day/hours per 5.7, customer picks time) and say the confirmation line.
  - where: fin_refused task_message + tool schedule_callback#2 + transition -> fin_tdn2l
  - evidence: `- After the tool result, say exactly: "Your second-look call is booked for {{secondlook_text}} at <HH:MM>."`
  - fix: The ok-route fin_refused -> fin_tdn2l fires right after the tool result, so the line is likely never spoken. Also, secondlook_text includes the year. Move the sentence into end_tdn2l spoken_message, built from a txt_short date ({weekday day month}) plus the booked time.
- **R39** (_tamsin.md Document 1 'Things customers say' already paid_): Already paid: say the sentence; no arrangement on that product; `add_note` reason `paid` with how and when they paid.
  - where: end_paid spoken_message; note_next reason paid; note_text
  - evidence: `return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)')`
  - fix: customer_said is never set. Have the agent ask how and when they paid, extract that into customer_said (or a paid_details variable) in negotiate/confirm, and put it into the paid note text.
- **R42** (_tamsin.md Document 1 'Things customers say' person_): Wants a person: ask once the sentence; if no or asks again, `transfer_to_agent` queue `general`.
  - where: ask_dob/ask_phone task_message; ev_human (human_limit 2) -> xfer_general
  - evidence: `"human_first": "I can help you with this now. Are you happy to continue with me?"`
  - fix: In negotiate, a 'no' to the human_first question is read as stance refuse (count_refusal), not as a transfer. Set a human_pending flag in ev_human and route the next 'no' to xfer_general.
- **R44** (_tamsin.md Document 1 'Things customers say' hardship_): If they refuse the transfer, don't push: `add_note` reason `hardship` on every product with their words, and close (HDNX). If they then offer a date or amount themselves, it is a normal arrangement.
  - where: hardship node support_no -> hs_decline -> note_next reason hardship -> fin_hardship (HDNX)
  - evidence: `lab = {'paid': 'says already paid', 'dispute': 'disputes', 'hardship': 'hardship'}.get(st, st)`
  - fix: The hardship note never has the customer's own words, because customer_said is never extracted. Add an extraction of the circumstance in their words at pol_hardship and use it in note_text.
- **R48** (_tamsin.md Document 1 'Closing'_): Every call ends with the code's closing sentence then exactly one `close_call`, the last tool call, with outcome and code from the card; for transfers, the sentence is said just before `transfer_to_agent`.
  - where: fin_* code nodes + end_* terminals; close_call lifecycle; xfer_* on_enter tts
  - evidence: `terminal: endedReason=transferred_XGEN, spoken_message="Please stay on the line."`
  - fix: Two gaps. (1) An ID-stage transfer_to_agent called by the model goes to fin_transferred_human with no sentence before the transfer: route the ID request to xfer_general instead. (2) load_account's transitions were overwritten, so a get_account failure never reaches fin_service_error (SYSF): restore that route.
- **R58** (_tamsin.md Document 2 section 5.4 rule table row part_): Offers floor up to but not including `past_due`: accept as part payment, dated no later than the part-payment last date.
  - where: check_offer code check_one part_deadline guard
  - evidence: `pdl = pdate(pg(V, pid, 'part_deadline'))   # optional: a brief with a shorter last date for part payments`
  - fix: Part payments are accepted, but the part-payment last date is never enforced: per-product part_deadline is never set. In PREPARE_BODY after register_product add pset(vars, pid, 'part_deadline', min(part_dl, deadline).isoformat()).
- **R60** (_tamsin.md Document 2 section 5.4 rule table row below floor_): Offers less than floor: say it cannot be recorded, offer the floor once; if refused, product turned down.
  - where: check_offer code check_one below_floor -> refuse()
  - evidence: `issues.append(('below_floor', T('below_floor', named=fmt(na), floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words'))))`
  - fix: After the floor is offered via below_floor, a refusal goes to refuse() and can reach the next ladder offer, which is the floor again. In refuse(), set the product to 'refused' when offered_floor == 'yes'.
- **R61** (_tamsin.md Document 2 section 5.4 rule table row too much_): Says full amount is too much: offer floor once, say rest stays overdue and we will contact them, then agree date; floor refused = turned down, no further attempt.
  - where: check_offer code too_much() and texts too_much_floor
  - evidence: `"too_much_floor": "I understand. I can record [floor] instead; the rest stays overdue and we will contact you about it."`
  - fix: After the floor is offered, a refusal calls refuse(), which can make another ladder attempt. If offered_floor == 'yes', mark the product turned down with no further attempt.
- **R63** (_tamsin.md Document 2 section 5.4 part-payment last date_): Part-payment last date: the 2nd business day after the call date, or the band's last date if earlier.
  - where: setup code part_deadline; PREPARE_BODY floor rung min(part_dl, deadline)
  - evidence: `vars['part_deadline'] = addbd(today, 2).isoformat()`
  - fix: The date is computed correctly and used for the system's floor offer, but not for amounts the customer names. Set part_deadline_<pid> = min(part_dl, deadline) in PREPARE_BODY so check_one caps part payments.
- **R77** (_tamsin.openapi.json /get_account_): `get_account` is refused until both questions are passed; if it fails, close as system failure.
  - where: load_account transitions; ask_phone_a/b transition 1 -> load_account
  - evidence: `nodes["load_account"]["transitions"] = [fl.always("prepare")]`
  - fix: Remove the transitions override so load_account routes to fin_service_error (no_promise/SYSF) when get_account fails, before the always -> prepare route.
- **R86** (_tamsin.md Document 4 intro_): Every `close_call` has one outcome (`promise`,`paid`,`transferred`,`no_promise`,`not_verified`,`not_reached`) and one reason code from the card; the closing sentence is said word for word before `close_call` (for a transfer, before `transfer_to_agent`).
  - where: close_call enums; fin_* terminals; xfer_* on_enter tts
  - evidence: `tools: verify_identity, transfer_to_agent`
  - fix: Route identity-step transfer requests through the xfer_general node, so 'I am putting you through now. Please stay on the line.' is said before transfer_to_agent instead of the model calling transfer_to_agent directly in ask_dob/ask_phone_*.
- **R87** (_tamsin.md Document 4 intro_): The closing sentence for the code is said word for word before `close_call`; for a transfer, before `transfer_to_agent`.
  - where: xfer_restructuring/xfer_support/xfer_general on_enter tts; end_* terminals
  - evidence: `- If they ask for a person: ask once "I can help you with this now. Are you happy to continue with me?" If they say no or ask again, call transfer_to_agent.`
  - fix: In ask_dob/ask_phone_a/ask_phone_b, replace the direct transfer_to_agent tool with a transition to xfer_general so its closing sentence is spoken before the transfer.
- **R88** (_tamsin.md Document 4 table_): Outcome/reason/closing sentence table: each situation maps to the outcome, code and exact closing sentence listed.
  - where: FINS terminals; check_offer routes; load_account
  - evidence: `nodes["load_account"]["transitions"] = [fl.always("prepare")]`
  - fix: Restore the get_account-failure route to fin_service_error (SYSF), and say the XGEN closing sentence before identity-step transfers by routing them via xfer_general.
- **R92** (_tamsin.md Document 4 table row XRST_): Transferred to restructuring: `transferred`/`XRST`, sentence said before `transfer_to_agent`.
  - where: xfer_restructuring code node on_enter tts -> xfer_call_restructuring -> fin_transferred_restructuring (XRST)
  - evidence: `NODE xfer_restructuring [code] (passthrough)
  on_enter tts: "I am putting you through now. Please stay on the line."`
  - fix: Code nodes don't speak, so the sentence may never be said before the transfer. Move the tts line to a node that speaks before transfer_to_agent#2 runs, e.g. a conversation node or an api_request node whose on_enter tts plays before its pre_action.
- **R93** (_tamsin.md Document 4 table row XGEN_): Transferred to a person on request (queue `general`): `transferred`/`XGEN`.
  - where: xfer_general code node on_enter tts -> xfer_call_general -> fin_transferred_human (XGEN); ask_dob/ask_phone_* transfer_to_agent -> fin_transferred_human
  - evidence: `4. -> fin_transferred_human  if (transfer_to_agent_success_count greater_than 0)  ["transferred"]`
  - fix: In ask_dob/ask_phone_a/ask_phone_b, route a second request for a person to xfer_general instead of letting the model call transfer_to_agent directly. Also make sure 'I am putting you through now. Please stay on the line.' is said from a node that speaks, not a code node.
- **R94** (_tamsin.md Document 4 table row XCARE_): Transferred to Customer Care for hardship (queue `support`): `transferred`/`XCARE`.
  - where: hardship support_yes -> xfer_support code node on_enter tts -> xfer_call_support -> fin_transferred_support (XCARE)
  - evidence: `NODE xfer_support [code] (passthrough)
  on_enter tts: "I am putting you through to Customer Care now. Please stay on the line."`
  - fix: Code nodes don't speak, so move the Customer Care sentence to a node that speaks before transfer_to_agent#3 runs.
- **R99** (_tamsin.md Document 4 table row SYSF_): Bank system failed (two failed `create_promise` tries, or `get_account` failing): `no_promise`/`SYSF`.
  - where: rec_after (fails >= fail_max 2 -> service_error) -> fin_service_error; load_account transitions
  - evidence: `nodes["load_account"]["transitions"] = [fl.always("prepare")]`
  - fix: Keep the get_account_failed -> fin_service_error transition on load_account (remove the line that overwrites the transitions with always -> prepare), so a failing get_account closes as no_promise/SYSF.
- **R103** (_tamsin.md Document 4 table row NOCON_): Someone else answered and no callback; wrong number; customer deceased; could not tell who answered: `not_reached`/`NOCON`.
  - where: fin_no_callback code + end_no_callback terminal; fin_wrong_number/fin_unclear -> fin_no_callback; fin_deceased -> end_deceased
  - evidence: `terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye."`
  - fix: The NOCON outcome/reason is right on every path. On the deceased path, the end_deceased spoken_message adds 'I am very sorry to hear that.' to the code-card farewell. Change it to exactly "Thank you. Goodbye.", or confirm the brief allows a different deceased farewell.
- **R104** (_tamsin.md Document 4 several products note_): Several products, nothing recorded, no transfer: all claimed paid → CLMPD; otherwise most serious decides in order SYSF, HDNX, DSPT, TDN2L, TDN; paid next to turned-down is TDN or TDN2L.
  - where: policy finalize() in check_offer/finalize code
  - evidence: `for s in sts:
    if s != 'paid':
        key = fk.get(s) or fk['default']
        break`
  - fix: Right now finalize picks the reason from the first non-paid product in list order. Make it rank the product states by severity instead: service_error > hardship > dispute > refused (refused then goes to the second-look node for TDN2L/TDN). That way a refused first product next to a disputed one ends DSPT, not TDN.
- **R105** (_tamsin.md Document 4 notes_): `add_note` reason is one of `refused`,`hardship`,`dispute`,`paid`,`service_error`; text must contain the listed content per reason.
  - where: policy note_text()/note_next(); tool add_note
  - evidence: `return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)')`
  - fix: The note text reads vars 'customer_said', but no node ever writes that variable, so hardship, dispute and paid notes will say '(not stated)'. Add a free-text extraction for customer_said (for paid: how and when they paid; for dispute: what is disputed; for hardship: their own words) on the negotiate, confirm and hardship nodes.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | tool verify_identity / verify_identity#2 body + post_process_code | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R02 | implemented | ask_phone_a/ask_phone_b transition all_verified -> load_account; prepare code reads product fields | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True")  ["identity verifi |
| R03 | implemented | tool create_promise body + pre_process_code; prepare code recorded_guard | # one promise per product: a recorded promise is never reopened or recorded again (the brief's change sentence) |
| R04 | implemented | tool schedule_callback (third_party) and schedule_callback#2 (fin_refused) | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, from 10:00 to 16:00. |
| R05 | implemented | tool close_call (alwaysRunsAt end_of_call); fin_* code nodes set outcome/reason | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R06 | implemented | prepare code: days_late bands, product types, up to three products (ordinals) | if days_late <= 7: ... elif days_late <= 20: ... else: *unverified* |
| R07 | implemented | setup code parses now; opening uses first_name/last_name; every tool body customer_id default | raw = str(vars.get('now') or '').strip() |
| R08 | implemented | every tool definition body.customer_id | body.customer_id (string): default "{{customer_id}}" |
| R09 | implemented | prepare/check_offer code check_one (business day, floor, deadline checks) | issues.append(('weekend_or_holiday', T('weekend_or_holiday', named=txt_short(nd), date=txt_short(nb)))) |
| R10 | implemented | generator HOLIDAYS / DATES / PREPARE_BODY (AHS-5 s.5 + minutes) | # ---------------------------------------------------------------- setup: dates (AHS-5 5.1, 5.3, 5.4, 5.6a, 5.7) |
| R11 | implemented | opening on_enter tts | on_enter tts: "Hello, this is the automated assistant of Corran Bay Bank. This call may be recorded. Could I speak to {{first_name}} {{last_name}}, please?" |
| R12 | implemented | setup transition -> opening_retry; opening_retry transitions -> fin_unclear -> fin_no_callback (NOCON) | 6. -> fin_unclear  if always  ["always"] |
| R13 | implemented | system_prompt | Once the right person is on the line, address them as {{title}} {{last_name}}. |
| R14 | implemented | system_prompt 'Always' list; also ID_COMMON / third_party / negotiate task_messages | - If asked whether you are a robot: say "Yes, I am an automated assistant.", then continue. |
| R15 | implemented | system_prompt 'Always' list | - If asked whether this is a scam: say they are free to hang up and call us on the number on the Corran Bay website, then continue. |
| R16 | implemented | ask_dob / ask_phone_a / ask_phone_b task_message 'Rules for this step'; system_prompt | - Never say overdue, arrears, missed, owe, debt, balance, payment, account, or any product name (card, credit card, loan, car loan), also not as the reason for  |
| R17 | implemented | third_party.task_message STRICT line | STRICT: say only that you are calling with a personal message for {{title}} {{last_name}}. Never say what it is about, nor the bank's department. |
| R18 | implemented | third_party.task_message | If they offer to answer questions or arrange anything for the customer, thank them, decline, and go back to when the customer can be reached. |
| R19 | implemented | third_party.task_message + setup code callback_text + tool schedule_callback | - If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed business day (if the time is outside 10:00-16:00, the nearest  |
| R20 | partial | setup/opening_retry/third_party transitions -> fin_wrong_number/fin_unclear/fin_deceased; end_deceased terminal | terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye." |
| R21 | implemented | ask_dob -> after_dob -> ask_phone_a/b; tools verify_identity (date_of_birth) and verify_identity#2/#3 (phone_last4) | Say you need to ask two security questions to protect their personal details, one at a time. Ask the first: their date of birth. |
| R22 | implemented | ask_dob.task_message; tool verify_identity post_process_code | When they give it, call verify_identity with answer = YYYY-MM-DD. A date given only in numbers is day, month, year (05/03/1990 = 1990-03-05). |
| R23 | implemented | ask_dob transitions (wrong_answers_left 1/0 -> fin_failed); after_dob code; ask_phone_b transitions (left 0 -> fin_failed) | vars['phone_variant'] = 'b' if left == '2' else 'a' |
| R24 | implemented | fin_failed code (not_verified/IDNO) -> end_failed terminal; verify_identity post_process_code | terminal: endedReason=not_verified_IDNO, spoken_message="For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. G |
| R25 | implemented | ask_dob/ask_phone_* task_message (ID_COMMON) + refusal extraction -> count_decline_* code -> fin_declined (not_verified/IDREF) | vars['decline_route'] = 'close' if n >= 2 else 'retry' |
| R26 | implemented | load_account pre_action get_account; prepare code: statement + one sentence per product, sorted by days_late desc then get_account order | statement = "I'm calling from Corran Bay Bank's Payments Support team about a missed payment. " |
| R27 | implemented | system prompt; negotiate/confirm/wrapup task_message COMMON | - Never mention fees, credit file, recovery agents or court. |
| R28 | implemented | prepare code: statement ending; policy to_one_by_one after a no to the all-products question | statement += 'Can you pay the overdue amount in full today?' |
| R29 | implemented | negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and NEVER ask how much they can pay. |
| R30 | implemented | negotiate transition 7 -> check_offer (before the stance routes); count_refusal -> refuse() ladder skips refused_offers | offer = names their own date, amount or period: never a refusal. |
| R31 | partial | check_one agrees a single amount at or above the floor; end_promise_part farewell | spoken_message="Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch about it. Goodbye." |
| R32 | partial | confirm node (readback_line) -> rec_next only on confirm=yes; change_offer re-checks | "readback_item": "[amount] for your [words] [when]" |
| R33 | contradicted | policy advance(): starts the next open product before any read-back; all agreed products are read back together, then recorded | if opn:                 start_product(V, opn[0], prefix)                 return |
| R34 | partial | enter_wrapup wrap_line (wrapup on_enter tts), after all records | "recorded": "Your payment arrangement is recorded." |
| R35 | partial | ev_rec_after fail_max=2 retry, state service_error, note_text; enter_wrapup rec_failed | return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2)) |
| R36 | partial | finalize -> fin_refused (on_enter tts + schedule_callback#2) -> fin_tdn2l | - After the tool result, say exactly: "Your second-look call is booked for {{secondlook_text}} at <HH:MM>." |
| R37 | partial | fin_refused task_message + tool schedule_callback#2 + transition -> fin_tdn2l | - After the tool result, say exactly: "Your second-look call is booked for {{secondlook_text}} at <HH:MM>." |
| R38 | contradicted | policy finalize / ev_notalk -> fin_refused | if c >= int(P['notalk_limit']):                 for p in pids(V):                     if state(V, p) in ('open', 'agreed'):                         pset(V, p, ' |
| R39 | partial | end_paid spoken_message; note_next reason paid; note_text | return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)') |
| R40 | implemented | pol_dispute -> ev_settle; note_next reason dispute; note_text | "dispute": "Thank you for telling me. I will not make an arrangement for your [words]." |
| R41 | implemented | negotiate transition topic new_plan -> xfer_restructuring -> transfer_to_agent#2 (queue restructuring) -> fin_transferred_restructuring (XRST) | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R42 | partial | ask_dob/ask_phone task_message; ev_human (human_limit 2) -> xfer_general | "human_first": "I can help you with this now. Are you happy to continue with me?" |
| R43 | implemented | pol_hardship -> ev_hardship say T('hardship'); hardship node support_yes -> xfer_support (queue support, XCARE) | "hardship": "I'm sorry to hear that. I will put you through to our Customer Care team, who can help." |
| R44 | partial | hardship node support_no -> hs_decline -> note_next reason hardship -> fin_hardship (HDNX) | lab = {'paid': 'says already paid', 'dispute': 'disputes', 'hardship': 'hardship'}.get(st, st) |
| R45 | contradicted | opening_retry (IDREF); ev_notalk -> finalize -> fin_refused | "notalk_first": "This will only take a moment." |
| R46 | implemented | system prompt; negotiate/confirm/hardship/wrapup task_message | - Never invent figures, dates or reasons; if you cannot answer from the tools: "I don't have that information." |
| R47 | implemented | policy note_next (notes=True, notes_on_transfer=False, defer_notes) -> record_note add_note | # notes wait until the wrap-up has decided the ending: a transfer from the wrap-up adds no notes at all |
| R48 | partial | fin_* code nodes + end_* terminals; close_call lifecycle; xfer_* on_enter tts | terminal: endedReason=transferred_XGEN, spoken_message="Please stay on the line." |
| R49 | superseded | superseded by  |  |
| R50 | implemented | setup code: isbd / addbd; prepare code check_one weekend_or_holiday | return d.weekday() in BWD and d.isoformat() not in HOL |
| R51 | superseded | superseded by R83 |  |
| R52 | implemented | prepare/check_offer code check_one (weekend_or_holiday moves to next_bd) and fit_day | issues.append(('weekend_or_holiday', T('weekend_or_holiday', named=txt_short(nd), date=txt_short(nb)))) |
| R53 | implemented | check_offer code resolve_when (weekday_rule 'this_week', tomorrow = today+1) | delta = (7 - today.weekday()) + wd |
| R54 | superseded | superseded by R81 |  |
| R55 | superseded | superseded by R80 |  |
| R56 | implemented | prepare code PREPARE_BODY: non-card floor | floor = float(p.get('instalment_amount')) |
| R57 | implemented | check_offer code check_one: after_deadline capped at deadline_of(pid) (band last date) | elif nd > dl: |
| R58 | partial | check_offer code check_one part_deadline guard | pdl = pdate(pg(V, pid, 'part_deadline'))   # optional: a brief with a shorter last date for part payments |
| R59 | implemented | check_offer code check_one above_full with above_full='agree' | "above_full": "The overdue amount is [full], so I will record [full]." |
| R60 | partial | check_offer code check_one below_floor -> refuse() | issues.append(('below_floor', T('below_floor', named=fmt(na), floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words')))) |
| R61 | partial | check_offer code too_much() and texts too_much_floor | "too_much_floor": "I understand. I can record [floor] instead; the rest stays overdue and we will contact you about it." |
| R62 | missing |  | none |
| R63 | partial | setup code part_deadline; PREPARE_BODY floor rung min(part_dl, deadline) | vars['part_deadline'] = addbd(today, 2).isoformat() |
| R64 | implemented | negotiate extraction stance=refuse -> count_refusal -> refuse() per product attempts_used | refuse = a no with no date and no amount ('no', 'I can't'), or no answer ('I don't know'). |
| R65 | implemented | prepare code: rungs per band (early_deadline / middle_deadline / late_a1 / part_deadline) | rungs = [('full_or_floor', a1), ('floor', min(part_dl, deadline))] |
| R66 | implemented | policy code refuse() -> state 'refused'; note_next/note_text -> record_note add_note | return ('%s: turned down. Attempts made: %d. Last offer: %s on %s.' % (w, max(n, 1), fmt(a), d.isoformat() if d else '') |
| R67 | implemented | policy code check_one (before_today / after_deadline / weekend_or_holiday / vague with vague_again='deadline') | issues.append(('after_deadline', T('after_deadline', deadline=txt_short(dl), named=txt_short(nd), words=pg(V, pid, 'words')))) |
| R68 | implemented | policy code check_one weekend_or_holiday branch (closed_day_move 'after', capped at the last date) | nb = next_bd(nd) |
| R69 | implemented | policy code check_one after_deadline + refuse() ladder skip of refused offers | "after_deadline": "The last date I can record for your [words] is [deadline]; that is the latest day that can be recorded." |
| R70 | implemented | policy code check_one before_today text | "before_today": "[named] has already passed, so it cannot be recorded. Please choose a day from today on." |
| R71 | implemented | policy code check_one vague branch (vague_asked once, then vague_deadline) | set_prop(V, pid, pa, dl) |
| R72 | implemented | third_party.task_message + setup code callback_text + schedule_callback field descriptions | - If it does not fit, propose ONCE the nearest slot that fits: the same time on the first allowed business day (if the time is outside 10:00-16:00, the nearest  |
| R73 | implemented | setup code secondlook_iso = addbd(today, 3); fin_refused task_message + schedule_callback#2 | - If the time is outside the hours, say the hours (12:00 to 18:00) once and ask again. If the second time does not fit either, or they decline, call transition_ |
| R74 | implemented | policy code ev_rec_after (fail_max 2) + recorded_guard / wrap_change | if f < int(P['fail_max']): |
| R75 | implemented | prepare code: sort by days_late then index; register_product per product | idx.sort(key=lambda t: (-int(float(t[1].get('days_late') or 0)), t[0])) |
| R76 | implemented | policy code ev_settle / refuse -> advance(); xfer_* nodes -> fin_transferred_* | opn = [p for p in ids if state(V, p) == 'open'] |
| R77 | partial | load_account transitions; ask_phone_a/b transition 1 -> load_account | nodes["load_account"]["transitions"] = [fl.always("prepare")] |
| R78 | implemented | tool verify_identity post_process_code; verify_identity#2 answer field | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R79 | implemented | generator docstring / policy values (minutes rules applied unconditionally) | Rules in force: minutes of 9 Oct (card floor = half past_due rounded up to 5, capped; middle band = 4th business day; cut-over closure moved to 6 Nov, 13 Nov a  |
| R80 | implemented | prepare code: floor computation | floor = min(past_due, math.ceil(past_due / 2.0 / 5.0 - 1e-9) * 5.0) |
| R81 | implemented | setup code: early/middle/late deadlines; prepare code: band rungs | vars['middle_deadline'] = addbd(today, 4).isoformat() |
| R82 | superseded | superseded by  |  |
| R83 | implemented | setup code HOL / BWD | HOL = set(['2026-10-22', '2026-11-06', '2026-11-24', '2026-12-25', '2026-12-28']) |
| R84 | implemented | fin_refused on_enter tts / task_message; tool schedule_callback#2 | they choose a time from 12:00 to 18:00. |
| R85 | implemented | ask_dob transitions; after_dob code; ask_phone_a/ask_phone_b transitions | vars['phone_variant'] = 'b' if left == '2' else 'a' |
| R86 | partial | close_call enums; fin_* terminals; xfer_* on_enter tts | tools: verify_identity, transfer_to_agent |
| R87 | partial | xfer_restructuring/xfer_support/xfer_general on_enter tts; end_* terminals | - If they ask for a person: ask once "I can help you with this now. Are you happy to continue with me?" If they say no or ask again, call transfer_to_agent. |
| R88 | partial | FINS terminals; check_offer routes; load_account | nodes["load_account"]["transitions"] = [fl.always("prepare")] |
| R89 | implemented | fin_promise -> fin_promise_full; end_promise_full terminal spoken_message | terminal: endedReason=promise_FULLPTP, spoken_message="Thank you, {{title}} {{last_name}}. Your arrangement is in place. Goodbye." |
| R90 | implemented | fin_promise -> fin_promise_part (promise_split from promise_reason PARTPTP); end_promise_part terminal spoken_message | terminal: endedReason=promise_PARTPTP, spoken_message="Thank you, {{title}} {{last_name}}. The rest of the overdue amount is still due and we will be in touch a |
| R91 | implemented | policy finalize (all states paid -> fin_keys paid) -> fin_paid; end_paid terminal spoken_message | terminal: endedReason=paid_CLMPD, spoken_message="Thank you. A payment can take up to two business days to reach us. Thank you for letting us know. Goodbye." |
| R92 | partial | xfer_restructuring code node on_enter tts -> xfer_call_restructuring -> fin_transferred_restructuring (XRST) | NODE xfer_restructuring [code] (passthrough)   on_enter tts: "I am putting you through now. Please stay on the line." |
| R93 | partial | xfer_general code node on_enter tts -> xfer_call_general -> fin_transferred_human (XGEN); ask_dob/ask_phone_* transfer_to_agent -> fin_transferred_human | 4. -> fin_transferred_human  if (transfer_to_agent_success_count greater_than 0)  ["transferred"] |
| R94 | partial | hardship support_yes -> xfer_support code node on_enter tts -> xfer_call_support -> fin_transferred_support (XCARE) | NODE xfer_support [code] (passthrough)   on_enter tts: "I am putting you through to Customer Care now. Please stay on the line." |
| R95 | implemented | fin_refused transition_to_fin_tdn -> fin_tdn; end_tdn terminal spoken_message | terminal: endedReason=no_promise_TDN, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R96 | implemented | fin_refused schedule_callback ok -> fin_tdn2l; end_tdn2l terminal spoken_message | terminal: endedReason=no_promise_TDN2L, spoken_message="Thank you for your time, {{title}} {{last_name}}. Speak to you then. Goodbye." |
| R97 | implemented | hardship support_no -> hs_decline (state hardship) -> finalize -> fin_hardship; end_hardship terminal | terminal: endedReason=no_promise_HDNX, spoken_message="Thank you for telling me. Take care, {{title}} {{last_name}}. Goodbye." |
| R98 | implemented | pol_dispute -> finalize (fin_keys dispute) -> fin_dispute; end_dispute terminal | terminal: endedReason=no_promise_DSPT, spoken_message="We will look into this and write to you. Goodbye." |
| R99 | partial | rec_after (fails >= fail_max 2 -> service_error) -> fin_service_error; load_account transitions | nodes["load_account"]["transitions"] = [fl.always("prepare")] |
| R100 | implemented | ask_dob/ask_phone_* wrong_answers_left routes -> fin_failed; end_failed terminal | terminal: endedReason=not_verified_IDNO, spoken_message="For your security I cannot continue on this call. You can use the Corran Bay app or visit any branch. G |
| R101 | implemented | count_decline_* / qb_* close -> fin_declined; end_declined terminal | terminal: endedReason=not_verified_IDREF, spoken_message="I understand. You can use the Corran Bay app or visit any branch. Goodbye." |
| R102 | implemented | third_party transition 1 -> fin_callback (code: not_reached/TPCB) -> end_callback terminal spoken_message | terminal: endedReason=not_reached_TPCB, spoken_message="Thank you, we will call back then. Goodbye." |
| R103 | partial | fin_no_callback code + end_no_callback terminal; fin_wrong_number/fin_unclear -> fin_no_callback; fin_deceased -> end_deceased | terminal: endedReason=not_reached_NOCON, spoken_message="I am very sorry to hear that. Thank you. Goodbye." |
| R104 | partial | policy finalize() in check_offer/finalize code | for s in sts:     if s != 'paid':         key = fk.get(s) or fk['default']         break |
| R105 | partial | policy note_text()/note_next(); tool add_note | return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)') |
| R106 | superseded | superseded by  |  |
