# Coverage audit: ashvale.workflow.json

Rules: `ashvale.rules.json`. Generator: `gen_ashvale.py`. Model claude-fable-5-1, 113 s, $9.86, 8 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 79 | 3 | 0 | 0 | 18 | 100 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R95** (partial): Outcome/code table: each end-of-call situation maps to one `outcome` and one `reason` code; the promise close leaves reason empty (the dialler stamps it). VUL added for hardship; HDS from message 2.1 is not on the list.
   - why: A get_account/prepare failure after security currently falls through to negotiate with outcome/reason left at not_verified/NVD, so every 'bank service failed' test case ends with the wrong close_call pair instead of no_promise/SYS.
   - fix: load_account / prepare: add deterministic transitions evaluated first — on load_account: `get_account_failure_count greater_than 0` -> fin_service_error, and on prepare code set vars['prepare_error']='true' when there are no products or a prepare_state error, with transition `prepare_error equals true` -> fin_service_error. fin_service_error code must set vars['outcome']='no_promise'; vars['reason']='SYS' (same as the existing create_promise path), and end_service_error terminal speaks the failure farewell; also add note_next='service_error' for each open product so add_note still runs.
2. **R81** (partial): From Monday 5 October hardship calls stay with the assistant: say the sorry sentence, make no proposal, say the Financial Support sentence, note every product `hardship` with what the customer said, close no promise code VUL. No transfer to `support` (was: offer support transfer, HDS). A date or amount the customer names is still logged as normal.
   - why: The hardship note text reads vars['customer_said'] which no node ever extracts, so every hardship case logs 'In their words: (not stated)' and fails the 'note contains what the customer said' check.
   - fix: Add to the extraction_schema of negotiate, confirm and hardship nodes a free-text field `customer_said` described as 'the customer's own words describing the hardship (illness, bereavement, job loss, etc.); empty if none'. In prepare code keep note_text = '%s: customer %s. In their words: %s' % (w, lab, vars.get('customer_said') or '(not stated)') and make the hardship node task_message instruct: 'Say exactly: "I'm sorry you're going through that." Make NO proposal. Say exactly: "Our Financial Support team will write to you within five working days." Do not transfer to support.' Keep fin_hardship outcome no_promise / reason VUL.
3. **R63** (partial): Every product ending the call without a promise gets an `add_note` (`refused`, `hardship`, `dispute`, `paid` or `service_error`) with a line of text saying what happened, single-product calls included.
   - why: The service_error note text hard-codes 'number of tries: 2' via max(n, 2) although fail_max=1, so the add_note text misreports what happened, and any reason missing from NOTE_ENUM is silently dropped so a product can end without its note.
   - fix: prepare code note_text: replace `return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2))` with `% (w, max(n, 1))` (real create_promise_failure_count). In the add_note tool definition set the body field `reason` enum explicitly to ["refused","hardship","dispute","paid","service_error"] and in the generator assert set(note_reasons) <= set(NOTE_ENUM) so no reason is dropped; ensure record_note is entered for single-product calls too (route from every fin_* non-promise node through record_note before the end_* terminal).

## partial (3)

- **R63** (_ashvale.md message 2.1 'Several products'_): Every product ending the call without a promise gets an `add_note` (`refused`, `hardship`, `dispute`, `paid` or `service_error`) with a line of text saying what happened, single-product calls included.
  - where: prepare code: note_next / note_text, Policy notes=True, note_reasons refused/hardship/dispute/paid/service_error; record_note tool add_note
  - evidence: `return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2))`
  - fix: In note_text for service_error use the real count (fail_max=1 means one try): replace max(n, 2) with max(n, 1) so the note text says what actually happened; also confirm add_note's reason enum contains all five values (note_reasons silently drops any missing from NOTE_ENUM).
- **R81** (_ashvale.md message 5.1 item 2_): From Monday 5 October hardship calls stay with the assistant: say the sorry sentence, make no proposal, say the Financial Support sentence, note every product `hardship` with what the customer said, close no promise code VUL. No transfer to `support` (was: offer support transfer, HDS). A date or amount the customer names is still logged as normal.
  - where: pol_hardship -> hardship node on_enter say_next (verbatim sentences), hardship task_message 'Make NO proposal', targets xfer_support -> hs_decline, note_reasons hardship, fin_hardship (no_promise VUL)
  - evidence: `return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)')`
  - fix: note_text reads vars['customer_said'] but no node extracts it: add a 'customer_said' extraction (the customer's own words) on negotiate/confirm/hardship so the hardship note contains what the customer said.
- **R95** (_ashvale.md code list v5 table_): Outcome/code table: each end-of-call situation maps to one `outcome` and one `reason` code; the promise close leaves reason empty (the dialler stamps it). VUL added for hardship; HDS from message 2.1 is not on the list.
  - where: fin_promise..fin_unclear code nodes (all 15 outcome/reason pairs match; `if False and rec` makes a transfer after a promise close as the transfer)
  - evidence: `vars['outcome'] = 'no_promise'
            vars['reason'] = 'SYS'`
  - fix: SYS covers only create_promise: add a route from load_account/prepare on get_account failure (no products / prepare_state error) to fin_service_error instead of falling through to negotiate with outcome still NVD.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | setup code: HOL (also prepare code HOL) | HOL = set(['2026-10-19', '2026-11-12', '2026-12-09', '2026-12-25', '2026-12-28', '2027-01-01']) |
| R02 | implemented | setup code: HOL / isbd (24 Dec not listed, Thursday weekday -> business day) | return d.weekday() in BWD and d.isoformat() not in HOL |
| R03 | superseded | superseded by  |  |
| R04 | implemented | system prompt {{title}} {{last_name}}, setup code vars['now'], who1 extraction {{first_name}}, prepare code products loop (ordinals first/second/third) | raw = str(vars.get('now') or '').strip() |
| R05 | implemented | setup code (today from vars['now']), prepare code today_iso, every tool body.customer_id default | today = datetime.date.fromisoformat(str(vars.get('today_iso'))) |
| R06 | implemented | all tool definitions body.customer_id; check_one code enforces business day/deadline/floor before create_promise | body.customer_id (string): default "{{customer_id}}" |
| R07 | implemented | opening on_enter tts | on_enter tts: "Hello, this is the automated assistant from Ashvale Bank. This call is recorded for quality and security. May I speak with {{title}} {{last_name} |
| R08 | implemented | opening extraction who1 description | customer = ONLY 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} {{last_name}}). |
| R09 | implemented | opening_retry task_message + transition 6 -> fin_unclear (not_reached/UNK) | 6. -> fin_unclear  if always  ["always"] |
| R10 | implemented | opening_retry task_message | Then ask exactly: "May I speak with {{title}} {{last_name}}, please?" This is the second and last time you ask. |
| R11 | implemented | system prompt (also opening_retry, third_party, ID_COMMON, negotiate asides) | - If asked whether you are a robot, an AI or a machine: say exactly "Yes, I'm Ashvale Bank's automated assistant." and carry on. |
| R12 | implemented | system prompt (also opening_retry, ID_COMMON, negotiate asides) | - If asked whether this is a scam: say "You can hang up and ring the number on the back of your card or on your statement." and carry on. |
| R13 | implemented | system prompt (also opening_retry, third_party STRICT, ask_dob/ask_phone rules) | - Until both security questions are passed, never use the words arrears, overdue, owe, debt, payment or collections, and never name a product, to anyone. |
| R14 | implemented | third_party on_enter tts + task_message | on_enter tts: "I'm calling about a private matter for {{title}} {{last_name}}. When would be a good time to reach them?" |
| R15 | implemented | third_party.task_message STRICT line | If they offer to pay or to help with it, thank them, say no, that it can only be dealt with by {{title}} {{last_name}}, and ask again when they can be reached.  |
| R16 | superseded | superseded by R76 |  |
| R17 | implemented | third_party tool schedule_callback (time HH:MM, pre_process normalise) + transition 1 -> fin_callback (not_reached/CBB) | 1. -> fin_callback  if (schedule_callback_response.data.ok equals "true" OR schedule_callback_response.data.ok equals "True")  ["callback booked"] |
| R18 | implemented | third_party.task_message window lines + transition 4 -> fin_no_callback (not_reached/CBX) | say the hours are 08:30 to 17:00 today or on the next two business days, and ask ONCE for another time. |
| R19 | implemented | third_party transition 3 -> fin_wrong_number (also setup/opening_retry who=wrong_number); fin_wrong_number code | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R20 | implemented | fin_deceased code (not_reached/DCD) + end_deceased terminal spoken_message | terminal: endedReason=not_reached_DCD, spoken_message="I'm very sorry for your loss." |
| R21 | implemented | ask_dob -> ask_phone nodes, verify_identity tools (field date_of_birth / phone_last4), post_process_code hints | Check identity with two security questions, one at a time. Ask the first now: "Could you tell me your date of birth, please?" |
| R22 | implemented | ask_dob.task_message + verify_identity pre_process_code (ORDER = 'dmy', to_date) | call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 19 |
| R23 | implemented | verify_identity post_process_code hint day_month_swapped branch | msg = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to say the date of birth again with the month as a word, for example 14 March 19 |
| R24 | superseded | superseded by R80 |  |
| R25 | implemented | verify_identity post_process_code LIMIT msg + ask_dob/ask_phone transition id_route exhausted -> fin_failed (not_verified/NVF) + end_failed terminal | msg = 'Second wrong answer in total: the check has ended. Do not ask again and do not say what the call was about. Tell the customer they can use the Ashvale mo |
| R26 | implemented | ask_dob/ask_phone task_message rule 2 + refusal extraction + count_decline_* code (2 -> fin_declined not_verified/NVD) | - If the customer refuses to answer or asks what the call is about instead of answering: explain that these questions are there to protect their account and tha |
| R27 | implemented | ask_phone transition 1 (all_verified -> load_account get_account) + prepare code statement spoken as negotiate on_enter tts {{say_next}} | statement = 'Thank you, ' + name + ". I'm calling from Ashvale's Customer Payments team about an overdue balance. "   # R27 |
| R28 | implemented | prepare code: statement (spoken by negotiate on_enter tts {{say_next}}) | statement += 'Your ' + w + ' has ' + fmt(pd) + ' overdue, ' + str(dl_) + ' days overdue. ' |
| R29 | implemented | prepare code: statement question (single vs multi) and texts question_all | statement += 'Would you be able to pay the full overdue balance today?'   # R29 verbatim |
| R30 | implemented | system_prompt 'Never ask the customer how much they can pay'; prepare prop_of full_of; negotiate transition 7 check_offer before count_refusal; stance extraction | - Never ask the customer how much they can pay, in any wording: you propose every amount. |
| R31 | implemented | negotiate extraction stance + transition 7 -> check_offer (ahead of count_refusal) | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R32 | superseded | superseded by R69 |  |
| R33 | implemented | setup / prepare code: HOL, BWD, isbd | HOL = set(['2026-10-19', '2026-11-12', '2026-12-09', '2026-12-25', '2026-12-28', '2027-01-01']) |
| R34 | implemented | check_offer code: check_one issues before_today / after_deadline / weekend_or_holiday | if nd < t: |
| R35 | implemented | check_offer code: check_one weekend_or_holiday branch (closed_day_move 'after', capped at deadline) | "weekend_or_holiday": "[named] is not a business day, so I can't log it. The next business day after it is [date].",   # R35 |
| R36 | implemented | check_offer code: check_one after_deadline branch (nd = dl, offer re-asked); refusal via count_refusal -> refuse() | "after_deadline": "[deadline] is the last day we can log for your [words].",            # R36 |
| R37 | implemented | check_offer code: check_one before_today branch | "before_today": "[named] has already passed, so I need a day from today onwards.",      # R37 |
| R38 | implemented | check_offer code: check_one vague branch (vague_asked once, then vague_again='deadline' proposes the latest date) | "vague_deadline": "The latest date we can log for your [words] is [deadline].",         # R38 then propose the latest date |
| R39 | implemented | prepare/check_offer code resolve_when (weekday_rule first_after_plus7) and DATE_DESC extraction | delta = (wd - today.weekday()) % 7 or 7   # bare / 'this X' = the first X after today; 'next X' = seven days later |
| R40 | implemented | check_offer code: check_one (floor..full agreed as proposed; above_full='agree' logs the full amount with the sentence) | "above_full": "The full overdue amount is [full], so I will log [full].",                # R40 more than the full amount: log the full amount |
| R41 | implemented | check_offer code: check_one below_floor branch + texts below_floor; count_refusal -> refuse() | issues.append(('below_floor', T('below_floor', named=fmt(na), floor=fmt(fl_), floor_name=pg(V, pid, 'floor_name'), words=pg(V, pid, 'words')))) |
| R42 | implemented | too_much code node: too_much() with texts too_much_floor; refusal -> refuse() | "too_much_floor": "I understand. I can log [floor]. The rest of the balance stays overdue." |
| R43 | superseded | superseded by R68 |  |
| R44 | superseded | superseded by R70 |  |
| R45 | implemented | count_refusal code: refuse() ladder exhaustion + refused_offers check; note_next reason refused; fin_refused | pset(V, pid, 'state', 'refused') |
| R46 | superseded | superseded by R81 |  |
| R47 | implemented | hardship transition 3 -> check_offer; ev_hardship hs_offer / ev_hs_decline -> ev_offer | 3. -> check_offer  if (offer_kind equals "exact" OR offer_ref equals "floor" OR offer_ref equals "full")  ["the customer names a date or an amount"] |
| R48 | implemented | system prompt + negotiate/confirm/hardship/wrapup task_message COMMON + aside reduction | - Nothing else is on offer: no discount, no waiver, no payment holiday, no plan, no freezing interest. |
| R49 | implemented | confirm on_enter tts readback_line (readback() with words/amount/when + readback_tail); confirm transition 2 -> rec_next -> record_promise; transition 1 -> change_offer | "readback_tail": ". Shall I go ahead and log that?" |
| R50 | implemented | confirm transition -> change_offer; ev_change -> check_one -> agree -> advance -> readback | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R51 | implemented | recorded_guard / ev_wrap_change with texts wrap_change; wrapup task_message | "wrap_change": "Once it's logged it can't be changed or cancelled on this call, but you can change it in the Ashvale mobile app." |
| R52 | superseded | superseded by R78 |  |
| R53 | implemented | enter_wrapup (after rec_next finds no more agreed products) appends texts after_recorded; wrapup on_enter tts wrap_line | "after_recorded": "You'll receive a text message confirming this arrangement today." |
| R54 | implemented | pol_paid -> ev_settle('paid'); texts paid / end_paid terminal spoken_message; note_reasons paid; fin_paid outcome paid/CLP | terminal: endedReason=paid_CLP, spoken_message="Thank you for letting me know. Payments can take up to two business days to show on your account with us. Thank  |
| R55 | implemented | pol_dispute -> ev_settle('dispute'); texts dispute; note_reasons dispute; fin_dispute outcome no_promise/DIS | vars['outcome'] = 'no_promise'             vars['reason'] = 'DIS' |
| R56 | implemented | negotiate/confirm/wrapup transition topic new_plan -> xfer_restructuring (baked queue restructuring) -> fin_transferred_restructuring XRS | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R57 | implemented | prepare code: ev_human (human_limit 2, human_first text) + human_dob/human_phone counters -> xfer_general -> fin_transferred_human | "human_first": "Is there anything I can help you with myself first?",                   # R57 ask once whether the assistant can help |
| R58 | implemented | opening_retry transition who2=refuses -> fin_declined; count_decline_* (decline_count 2) -> fin_declined; prepare code ev_notalk (notalk_limit 2) sets open/agreed products refused -> notes -> fin_refused RTP | fl.eq("who2", "refuses", "fin_declined", "does not want to talk, said twice (R58, before security)"), |
| R59 | implemented | system prompt + negotiate/confirm/hardship/wrapup task_message COMMON | - Anything you cannot answer from the facts you were given: say exactly "I'm afraid I don't have that information." Never invent a figure, a date or a reason. |
| R60 | implemented | prepare code: per-product register_product (band, deadline, ladder), statement lists all products + question_all once; to_one_by_one/start_product take open products in pids order with rung 0 (a1, not today), attempts_used per pid | statement += 'Would you be able to pay all of these in full today?'     # R29 verbatim |
| R61 | implemented | prepare code: all_offer -> fit_day caps at the product's own deadline with tag 'dl'; readback adds own_deadline text | "own_deadline": ", which is the latest date we can log for it",                         # R61 |
| R62 | implemented | prepare code: readback() joins all agreed products into one line with one readback_tail; rec_next -> record_promise -> rec_after -> rec_next loops over agreed products in pids order | return T('readback_head') + T('readback_sep').join(items) + T('readback_tail') |
| R63 | partial | prepare code: note_next / note_text, Policy notes=True, note_reasons refused/hardship/dispute/paid/service_error; record_note tool add_note | return '%s: create_promise failed, number of tries: %d.' % (w, max(n, 2)) |
| R64 | implemented | structure: notes only in policy nodes after load_account; pol_human/wrap_human/new_plan route straight to xfer_* (defer_notes, Policy notes_on_transfer=False); fin_transferred_* set transferred regardless of recorded_pids (promise_decides=False) | notes_on_transfer=False,                                    # R64: no notes at all on a transferred call |
| R65 | implemented | end_* terminal spoken_message (BYE/BYE_T); close_call lifecycle tool alwaysRunsAt end_of_call; close_call pre_process_code drops reason for promise | if b.get('outcome') in ('promise',) or not b.get('reason'): |
| R66 | implemented | prepare code finalize(): 'recorded' -> promise, all paid -> paid, else first non-paid state's fin key in pids order; fin_promise sets reason ''; fin_transferred_* override a logged promise (promise_decides=False) | POLICY.end_pair(key, outcome, reason, farewell, nodes, promise_decides=False)   # R66: a transfer after a logged promise closes as the transfer |
| R67 | superseded | superseded by  |  |
| R68 | implemented | prepare code: credit_card floor = max(round(past_due/2,2), minimum_payment); other types floor = instalment_amount | floor = max(round(past_due / 2.0, 2), mp)      # R68: half the overdue balance, or the minimum payment where higher |
| R69 | implemented | prepare code: days_late <= 9 -> today+18 calendar days moved to next business day, 1 rung at a1; else deadline = addbd(today, 5), rungs [full_or_floor@a1, floor@deadline] | deadline = addbd(today, 5) |
| R70 | implemented | prepare code: a1 = addbd(today, 2), late band deadline = addbd(today, 5), rungs | rungs = [('full_or_floor', a1), ('floor', deadline)] |
| R71 | superseded | superseded by  |  |
| R72 | superseded | superseded by  |  |
| R73 | superseded | superseded by  |  |
| R74 | superseded | superseded by  |  |
| R75 | superseded | superseded by  |  |
| R76 | implemented | setup code: callback_text (today after now up to 17:00, next two business days 08:30-17:00); tool schedule_callback time description; third_party task_message | lines.append(txt(nbd) + ' (' + nbd.isoformat() + '), from 08:30 up to 17:00 included.') |
| R77 | implemented | third_party task_message outside-window bullet + transition_to_fin_no_callback -> fin_no_callback (not_reached CBX) | say the hours are 08:30 to 17:00 today or on the next two business days, and ask ONCE for another time. |
| R78 | implemented | tool create_promise maxRetries 0; prepare code ev_rec_after with fail_max 1 -> state service_error; note_reasons service_error; finalize -> fin_service_error (no_promise SYS); end_service_error spoken_message / rec_failed text | "rec_failed": "I'm sorry, I couldn't confirm that arrangement on this call. Our team will be in touch with you about it.",   # R78 verbatim |
| R79 | implemented | prepare code: rec_next loops over remaining 'agreed' products after ev_rec_after; finalize picks promise when any product is 'recorded'; enter_wrapup names failed products | if 'recorded' in sts:             key = fk['promise'] |
| R80 | implemented | tool verify_identity post_process_code (shared id_wrong counter, done = nw >= 2), ask_dob/ask_phone transitions id_route exhausted -> fin_failed (not_verified NVF), day_month_swapped hint, end_failed spoken_message | done = nw >= 2 or str(left) == '0' |
| R81 | partial | pol_hardship -> hardship node on_enter say_next (verbatim sentences), hardship task_message 'Make NO proposal', targets xfer_support -> hs_decline, note_reasons hardship, fin_hardship (no_promise VUL) | return '%s: customer %s. In their words: %s' % (w, lab, said or '(not stated)') |
| R82 | implemented | hardship transitions 3 (check_offer on offer_kind exact / offer_ref) and 1 (pol_human -> ev_human: human_first once, then xfer_general); ev_hardship keeps hs_offer | 3. -> check_offer  if (offer_kind equals "exact" OR offer_ref equals "floor" OR offer_ref equals "full")  ["the customer names a date or an amount"] |
| R83 | implemented | hardship transition 1 -> pol_human; ev_human (human_limit 2) -> xfer_general (queue general) -> fin_transferred_human (transferred XHM) | 1. -> pol_human  if (hs_answer equals "human")  ["the customer asks for a person"] |
| R84 | implemented | tool close_call reason description (VUL in list); MAX_WRONG=2 and hardship-stays-with-assistant implemented as the rules in force | paid: CLP. transferred: XRS/XHM. no_promise: RTP/VUL/DIS/SYS. not_verified: NVF/NVD. not_reached: CBB/CBX/WRN/DCD/UNK. Empty for promise. |
| R85 | superseded | superseded by R69 |  |
| R86 | superseded | superseded by R70 |  |
| R87 | implemented | prepare code: floor computation per product type | floor = max(round(past_due / 2.0, 2), mp)      # R68: half the overdue balance, or the minimum payment where higher |
| R88 | superseded | superseded by R76 |  |
| R89 | implemented | prepare code statement (single-product first ask), texts readback_tail, after_recorded (enter_wrapup, once), paid text + end_paid spoken_message | statement += 'Would you be able to pay the full overdue balance today?'   # R29 verbatim |
| R90 | implemented | confirm on_enter tts {{readback_line}} (prepare code readback: readback_tail), before record_promise | "readback_tail": ". Shall I go ahead and log that?", |
| R91 | implemented | prepare code enter_wrapup: after_recorded appended to wrap_line once (wrap_done guard), spoken by wrapup on_enter tts after rec_next has recorded every agreed product | "after_recorded": "You'll receive a text message confirming this arrangement today.", |
| R92 | implemented | prepare code texts 'paid' (multi-product prefix via ev_settle) and end_paid terminal spoken_message | spoken_message="Thank you for letting me know. Payments can take up to two business days to show on your account with us. Thank you for your time, {{title}} {{l |
| R93 | implemented | setup/prepare code HOL (from SPEC calendar holidays) and FINS / fin_* nodes (dialler list v5 codes) | HOL = set(['2026-10-19', '2026-11-12', '2026-12-09', '2026-12-25', '2026-12-28', '2027-01-01']) |
| R94 | implemented | fin_* code nodes set outcome/reason pairs; fin_paid sets CLP; tool close_call pre_process_code drops reason only for promise | if b.get('outcome') in ('promise',) or not b.get('reason'): |
| R95 | partial | fin_promise..fin_unclear code nodes (all 15 outcome/reason pairs match; `if False and rec` makes a transfer after a promise close as the transfer) | vars['outcome'] = 'no_promise'             vars['reason'] = 'SYS' |
| R96 | implemented | prepare code note_reasons {refused,hardship,dispute,paid,service_error} + note_text (one plain line) feeding tool add_note body.reason/body.text | "note_reasons": {"refused": "refused", "hardship": "hardship", "dispute": "dispute", "paid": "paid", "service_error": "service_error"} *unverified* |
| R97 | implemented | tool verify_identity post_process_code (ok=false not counted) + pre_process_code normalise (to_date dmy -> YYYY-MM-DD, to_digits); verify_identity#2 answer 'Exactly four digits.' | msg = 'The answer could not be read. It does not count as wrong. Ask again: Could you tell me your date of birth, please?' |
| R98 | implemented | tool close_call definition (outcome enum) + pre_process_code; fin_paid sets CLP | body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"] |
| R99 | implemented | tool schedule_callback definition (customer_id baked, date* YYYY-MM-DD, time* HH:MM) + pre_process_code to_time | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, from 08:30 to 17:00 inclusive, later than now. |
| R100 | superseded | superseded by  |  |
