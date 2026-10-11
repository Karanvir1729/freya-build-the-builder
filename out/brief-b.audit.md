# Coverage audit: brief-b.workflow.json

Rules: `brief-b.rules.json`. Generator: `gen_brief-b.py`. Model claude-fable-5-1, 86 s, $7.48, 6 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 71 | 0 | 0 | 0 | 8 | 79 |

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | prepare code: single-product statement branch; whole workflow | if len(items) == 1: |
| R02 | implemented | tools verify_identity / verify_identity#2: baked field, answer description, post_process_code | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What are the last four digits of the phone number on file?' |
| R03 | implemented | tool schedule_callback body fields | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, between 10:00 and 19:00. |
| R04 | superseded | superseded by R63 |  |
| R05 | implemented | setup code (now), system prompt (title/last_name), every tool body (customer_id); assemble without test_variables | raw = str(vars.get('now') or '').strip() |
| R06 | implemented | all tool definitions body.customer_id (schedule_callback, verify_identity, transfer_to_agent, get_account, create_promise, add_note, close_call) | body.customer_id (string): default "{{customer_id}}" |
| R07 | implemented | system prompt | Address the customer as {{title}} {{last_name}}. |
| R08 | implemented | setup code: today derived from vars['now']; prepare code resolve_when comment | nowdt = datetime.datetime.fromisoformat(raw[:16]) |
| R09 | implemented | opening on_enter tts (first line for every answerer) | on_enter tts: "Hello, this is Freya Bank's digital assistant. Please note that we record this call. Am I speaking with {{title}} {{last_name}}?" |
| R10 | implemented | opening_retry.task_message, third_party.task_message STRICT line, ask_dob/ask_phone ID_COMMON rule 1 | - Do not mention the reason for the call, collections, a debt, a payment, a product or an amount. If asked what the call is about or how much they owe, say you  |
| R11 | implemented | opening on_enter tts; opening_retry.task_message 'ask exactly' | Then ask exactly: "Am I speaking with {{title}} {{last_name}}?" |
| R12 | implemented | opening extract who1 (WHO_DESC) -> setup route 5 -> opening_retry; opening_retry transition 6 -> fin_unclear | 6. -> fin_unclear  if always  ["always"] |
| R13 | implemented | opening_retry.task_message | If the person asked a question, answer it briefly first: who you are -> you are Freya Bank's digital assistant; a robot or AI -> 'Yes, I am Freya Bank's digital |
| R14 | implemented | system_prompt 'Always' bullet 1; negotiate/confirm/hardship/wrapup task_message COMMON; opening_retry task_message; policy asides 'robot' | - If asked whether you are a robot or an AI: say "Yes, I am Freya Bank's digital assistant.", then continue. |
| R15 | implemented | third_party task_message STRICT line and 'Your only job' line | Your only job: ask when {{title}} {{last_name}} can be reached, then book a callback. |
| R16 | implemented | setup code: callback_text (today after now up to 19:00, next business day 10:00-19:00); third_party tool schedule_callback; transition -> fin_callback (not_reached/callback) | start = '10:00' if cur < '10:00' else 'after ' + cur |
| R17 | implemented | third_party task_message bullets 2-3; transition 4 transition_to_fin_no_callback -> fin_no_callback (not_reached/no_callback) | - If the second answer is also outside the window, or they cannot say when, do not book: call transition_to_fin_no_callback. |
| R18 | implemented | third_party transition 3 (tp_status wrong_number) and setup/opening_retry routes -> fin_wrong_number; fin_wrong_number code | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R19 | implemented | setup/opening_retry/third_party routes on deceased -> fin_deceased (not_reached/deceased); end_deceased terminal spoken_message | terminal: endedReason=not_reached_deceased, spoken_message="I am sorry for your loss. Thank you for your time, goodbye." |
| R20 | implemented | third_party task_message STRICT line | Never mention the bank account, a product, a debt, an amount, a payment or collections, even if they ask or offer to pay or help. If they ask what it is about,  |
| R21 | implemented | ask_dob task_message + tool verify_identity (field date_of_birth baked); ask_phone task_message + tool verify_identity#2 (field phone_last4); transition ask_dob -> ask_phone on verified | When they give it, call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then ye |
| R22 | implemented | ask_dob transition 1 and ask_phone transition 2 on wrong_answers_left == 0 -> fin_failed; verify_identity post_process_code 'Wrong answer... ask again' | 1. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "0")  ["three wrong answers"] |
| R23 | implemented | tool verify_identity post_process_code hint branch (HINTS day_month_swapped) | d['what_to_do_next'] = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to say the date of birth again with the month as a word, for ex |
| R24 | implemented | verify_identity post_process_code MAX_WRONG line; routes -> fin_failed (not_verified/failed); end_failed terminal spoken_message | spoken_message="I am sorry, I could not verify your identity, so I cannot continue. Please use the Freya Bank mobile app or visit a branch. Thank you, goodbye." |
| R25 | implemented | ask_dob/ask_phone task_message ID_COMMON refusal line; count_decline_dob/phone code (decline_count >= 2 -> fin_declined); qb_dob/qb_phone code (question_count >= 2 -> fin_declined); fin_declined code not_verified/declined | vars['decline_route'] = 'close' if n >= 2 else 'retry' |
| R26 | implemented | ask_phone transition 1 -> load_account (api_node get_account) | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True")  ["identity verifi |
| R27 | superseded | superseded by R64 |  |
| R28 | implemented | setup / prepare code: HOL, BWD, isbd | HOL = set(['2026-10-26', '2026-11-11', '2026-11-26', '2026-12-25', '2027-01-01']) |
| R29 | implemented | setup code: early_deadline/late_deadline; prepare code: days_late band and rungs | vars['early_deadline'] = addbd(today, 12).isoformat() |
| R30 | implemented | check_offer code: check_one (before_today / after_deadline / weekend_or_holiday issues) | issues.append(('before_today', T('before_today', named=txt_short(nd)))) |
| R31 | implemented | check_offer code: check_one elif not isbd(nd) -> next_bd, after nd > dl check; texts weekend_or_holiday | "weekend_or_holiday": "[named] is not a business day, so I cannot record it. The next business day is [date]." |
| R32 | implemented | check_offer code: check_one vague branch (vague_asked once, then set_prop(pa, dl) + vague_deadline); texts vague | set_prop(V, pid, pa, dl) |
| R33 | implemented | check_offer code: resolve_when weekday branch (WDRULE this_week); negotiate extraction offer_date description | delta = (7 - today.weekday()) + wd |
| R34 | implemented | check_offer code: check_one nd > dl -> after_deadline text + offer_question at deadline; refuse -> count_refusal -> refuse() | "after_deadline": "The latest date I can record for your [words] is [deadline]." |
| R35 | implemented | prepare code: statement asks full past-due today; rungs full_or_floor; negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. The only offer you may make is the current offer in STATE, |
| R36 | implemented | prepare code: floor per product type | floor = p.get('minimum_payment') |
| R37 | implemented | check_offer code: too_much() (offered_floor once, else refuse); ladder rung 2 ('floor', deadline); texts too_much_floor | "too_much_floor": "I understand. The lowest amount I can accept is [floor], the [floor_name]. The rest stays overdue." |
| R38 | implemented | check_offer code: check_one below_floor branch (offered_floor once, then refuse) and agree() when no issues | "below_floor": "I cannot record [named]. The lowest amount I can record is [floor], your [floor_name]." |
| R39 | superseded | superseded by R66 |  |
| R40 | implemented | negotiate extraction stance (STANCE_DESC) + negotiate transition 7 check_offer before 10 count_refusal | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R41 | implemented | setup code attempt1_date / late_deadline; prepare code rungs + policy refuse()/rung() | rungs = [('full_or_floor', a1), ('floor', deadline)] |
| R42 | implemented | policy refuse(): refused_offers skip + state refused -> finalize -> fin_refused | if k >= len(L):                 pset(V, pid, 'state', 'refused') |
| R43 | implemented | negotiate transition 1 -> pol_hardship; ev_hardship text; hardship node transitions -> xfer_support / hs_decline -> fin_hardship | "hardship": "I am sorry to hear that. Would you like me to connect you with our customer support team?" |
| R44 | implemented | system prompt + COMMON in negotiate/confirm/hardship/wrapup task_message | - Never offer a discount, a waiver, a payment plan or any term that is not in STATE. If asked, say you cannot offer that. |
| R45 | superseded | superseded by R69 |  |
| R46 | implemented | confirm transition 1 -> change_offer; policy ev_change -> check_one -> agree -> advance (readback) | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R47 | implemented | policy rec_next (one create_promise per agreed product), recorded_guard, ev_wrap_change wrap_change text | "wrap_change": "A recorded promise cannot be changed or cancelled on this call, but you can change it in the Freya Bank mobile app." |
| R48 | superseded | superseded by R75 |  |
| R49 | implemented | policy enter_wrapup (after_recorded appended to wrap_line, spoken by wrapup on_enter tts) | "after_recorded": "You will receive a text message confirming this promise." |
| R50 | superseded | superseded by R72 |  |
| R51 | superseded | superseded by R71 |  |
| R52 | implemented | negotiate/confirm/wrapup transition topic new_plan -> xfer_restructuring (transfer_to_agent#2 queue restructuring) -> fin_transferred_restructuring | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R53 | implemented | policy ev_human (human_first then xfer_general on 2nd) + ask_dob/ask_phone ID_COMMON with transfer_to_agent queue general -> fin_transferred_human | "human_first": "I can help you with most things myself. Is there anything I can help you with before I transfer you?" |
| R54 | implemented | system prompt scam line; negotiate/confirm/hardship aside 'scam' in finish_turn; opening_retry task_message | - If asked whether this is a scam: say they can verify this call by phoning Freya Bank's customer service number, then continue. |
| R55 | implemented | system prompt + COMMON in negotiate/confirm/hardship/wrapup task_message | - A question these facts do not answer: say you do not have that information. |
| R56 | implemented | prepare/pol_notalk code: ev_notalk (notalk_limit 2 -> refused -> fin_refused); count_decline_dob/phone -> fin_declined; opening_retry transition 5 -> fin_declined | if c >= int(P['notalk_limit']): |
| R57 | implemented | tool close_call config alwaysRunsAt end_of_call; pre_process_code drops empty reason | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R58 | implemented | fin_* code nodes (FINS table) + finalize(): recorded->promise, all paid->paid, else first non-paid state; close_call body outcome/reason | "service_error": ("no_promise", "service_error", "I am sorry, I could not record your promise because of a technical problem. Thank you for your time, {{title}} |
| R59 | implemented | wrapup transitions -> wrap_human -> xfer_general -> fin_transferred_human; wrapup -> xfer_restructuring -> fin_transferred_restructuring (fin code overwrites outcome set by enter_wrapup) | 3. -> xfer_restructuring  if (wrap equals "new_plan")  ["asks for a new plan"] |
| R60 | superseded | superseded by R70 |  |
| R61 | implemented | every end_* terminal spoken_message (thanks + Goodbye), close_call runs at end_of_call afterwards | terminal: endedReason=promise, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R62 | implemented | whole workflow: Brief A flow (opening, third_party, identity, negotiate ladder, closings) with multi=True policy for 1-3 products | """Brief B generator, v3: Brief A + Brief B (one to three products) on builder/policy.py. |
| R63 | implemented | load_account response_mapping data.products -> prepare code loop register_product per product (own past_due, days_late, floor) | register_product(vars, pid, words, past_due, floor, floor_name, deadline, rungs) |
| R64 | implemented | prepare code: statement (one sentence per product) -> negotiate on_enter tts {{say_next}} | statement += 'Your ' + w + ' has ' + fmt(pd) + ' past due, ' + str(dl_) + ' days late. ' |
| R65 | implemented | prepare code: per-product deadline from days_late (<=7 early_deadline = 12 bd, else late_deadline = 7 bd) | if days_late <= 7: |
| R66 | implemented | prepare code: statement ends 'Can you pay all of them today?'; ev_refuse stage all -> to_one_by_one -> refuse() offers rung 0 (full on attempt1_date) with attempts_used 1, products in pids order | "one_by_one": "Let us go through them one by one.", |
| R67 | implemented | policy code: per-pid vars attempts_used_<pid>, refused_offers_<pid>, checks_<pid> (register_product, refuse, rung) | pset(V, pid, 'attempts_used', k + 1) |
| R68 | implemented | policy code: all_offer -> fit_day caps at the product's deadline with tag 'dl'; readback appends own_deadline text | "own_deadline": ", which is the latest date I can record for it", |
| R69 | implemented | prepare code: readback() + confirm transition 2 -> rec_next; rec_next/ev_rec_after loop record_promise once per agreed product | "readback_tail": ". Do you confirm?", |
| R70 | implemented | prepare code: note_next() with P['note_reasons'] {refused,hardship,dispute,paid,service_error}; record_note node (add_note with note_pid/note_reason); advance() -> note_next when nothing agreed | if st in P['note_reasons'] and pg(V, p, 'noted') == 'no': |
| R71 | implemented | negotiate transition 6 -> pol_dispute; prepare code: ev_settle('dispute') sets state dispute, advance() continues with next open product; note_next adds add_note reason dispute | "dispute": "Thank you for telling me. I will not take a promise for your [words].", |
| R72 | implemented | negotiate transition 5 -> pol_paid; prepare code: ev_settle('paid') text 'paid', advance() continues; note_next adds add_note reason paid | "paid": "Thank you for letting me know. Payments can take one business day to appear, so I will not take a promise for your [words].", |
| R73 | implemented | negotiate/confirm/wrapup transitions topic new_plan -> xfer_restructuring (transfer_to_agent#2 queue restructuring) -> fin_transferred_restructuring; no record/note on that path | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R74 | implemented | prepare code: rec_next() defer_notes -> enter_wrapup before note_next; xfer_* nodes go straight to fin_transferred_*; notes_on_transfer=False | # notes wait until the wrap-up has decided the ending: a transfer from the wrap-up adds no notes at all |
| R75 | implemented | prepare code: ev_rec_after() fail_max=2 re-routes to record once, then state service_error -> note_next add_note service_error; enter_wrapup says recorded only for state recorded; negotiate/confirm 'Never say that a promise is recorded.' | if f < int(P['fail_max']): |
| R76 | implemented | prepare code: finalize() -> fin_keys; check_offer-family transitions 1-6 to fin_promise/fin_paid/fin_hardship/fin_dispute/fin_service_error/fin_refused; xfer_* -> fin_transferred_*; identity/opening fin_* nodes | elif sts and all(s == 'paid' for s in sts): |
| R77 | implemented | tool create_promise body defaults + pre_process_code (float amount, date[:10]); rec_next sets rec_pid/rec_amount/rec_date per product | body.amount (number): default "{{rec_amount}}" |
| R78 | implemented | tool add_note body (customer_id, product_id {{note_pid}}, reason {{note_reason}}, text {{note_text}}); note_reasons restricted to NOTE_ENUM in generator | body.reason (string): default "{{note_reason}}" |
| R79 | implemented | tool close_call: outcome enum, lifecycle alwaysRunsAt end_of_call, pre_process_code drops reason for promise/paid; fin_* nodes set reason for every other outcome | if b.get('outcome') in ('promise', 'paid') or not b.get('reason'): |
