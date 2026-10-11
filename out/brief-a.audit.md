# Coverage audit: brief-a.workflow.json

Rules: `brief-a.rules.json`. Generator: `gen_brief-a.py`. Model claude-opus-5-5, 65 s, $4.38, 7 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 58 | 3 | 0 | 0 | 0 | 61 |

6 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R22** (partial): If customer won't answer, explain once the questions protect the account; asking what the call is about counts as declining. Second refusal/question closes `not_verified` / `declined`.
   - why: A refusal at one stage followed by a question back at another (or the reverse) is counted on separate or reset counters, so the call goes on instead of closing not_verified/declined, and close_call sends the wrong outcome.
   - fix: Code nodes count_decline_* and qb_*: replace the separate counters with one shared counter, vars['identity_decline_count'] = int(vars.get('identity_decline_count') or 0) + 1. Do not reset it in verify_identity or when moving from ask_dob to ask_phone. Set the route to 'close' when the count is >= 2 and to 'retry' otherwise; 'close' goes to fin_declined (outcome=not_verified, reason=declined). In the ask_dob and ask_phone task_message, add: 'If {{identity_decline_count}} is 0 and the customer declines or asks what the call is about, explain once that these questions protect their account and ask again. Do not repeat that explanation.'
2. **R31** (partial): "Next <weekday>" means that weekday in the following calendar week; "this <weekday>" the current week. "Next Friday" said on Friday is the following week's Friday.
   - why: 'This <weekday>' always resolves to a future date with % 7, so 'this Monday' said on a Wednesday becomes next week's Monday. The promise date is then wrong and the deadline check gives the wrong result.
   - fix: check_offer code, resolve_when weekday branch: keep 'next' as delta = (7 - today.weekday()) + wd. For the 'this' prefix, use delta = wd - today.weekday() (that weekday in the current Monday-to-Sunday week; it can be in the past, so the past-date check rejects it). Only a bare weekday with no prefix should keep (wd - today.weekday()) % 7. Also update the offer_date extraction description to keep the 'this'/'next' prefix in the extracted value.
3. **R59** (partial): Thank the customer and say goodbye before `close_call`.
   - why: The deceased farewell does not thank the customer, so the mandatory 'thank and say goodbye' closing is missed on deceased-contact cases.
   - fix: Generator FINS['deceased'] / end_deceased terminal spoken_message: change it to "I am sorry for your loss. Thank you for letting me know. Goodbye." Check that every other end_* spoken_message contains both 'Thank you' and 'Goodbye'.

## partial (3)

- **R22** (_brief-a.md rule 15_): If customer won't answer, explain once the questions protect the account; asking what the call is about counts as declining. Second refusal/question closes `not_verified` / `declined`.
  - where: ask_dob/ask_phone task_message; count_decline_* and qb_* code nodes -> fin_declined
  - evidence: `vars['qb_route'] = 'close' if n >= 2 else 'retry'`
  - fix: Use one shared counter for refusals and questions back across both stages, not reset by verify_identity, so a refusal followed by a question (or the reverse) closes not_verified/declined. Have the prompt explain the protection only on the first refusal.
- **R31** (_brief-a.md rule 22_): "Next <weekday>" means that weekday in the following calendar week; "this <weekday>" the current week. "Next Friday" said on Friday is the following week's Friday.
  - where: check_offer code: resolve_when weekday branch; offer_date extraction description
  - evidence: `delta = (7 - today.weekday()) + wd ... else: delta = (wd - today.weekday()) % 7`
  - fix: In resolve_when, for the 'this' prefix use delta = wd - today.weekday() (that weekday in the current Monday-to-Sunday week, possibly past) instead of % 7. Then 'this Monday' said on a Wednesday is no longer moved to next week.
- **R59** (_brief-a.md rule 47_): Thank the customer and say goodbye before `close_call`.
  - where: end_* terminal spoken_message
  - evidence: `terminal: endedReason=not_reached_deceased, spoken_message="I am sorry for your loss. Goodbye."`
  - fix: In FINS['deceased'], add a thank-you to the farewell, e.g. "I am sorry for your loss. Thank you for letting me know. Goodbye."

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | tool definitions: all tools call the mock API | url: POST https://freya-bank-mock.freyavoice.workers.dev/v1/get_account |
| R02 | implemented | opening -> ask_dob/ask_phone -> load_account -> prepare statement -> negotiate/confirm/record_promise -> fin_* nodes | I am calling from the collections team about a late payment on your ' + words + '. The past-due amount is ' + fmt(past_due) + ', and it is ' + str(days_late) +  |
| R03 | implemented | setup code reads vars['now']; every tool body.customer_id default; get_account in load_account | body.customer_id (string): default "{{customer_id}}" |
| R04 | implemented | every tool definition body.customer_id | body.customer_id (string): default "{{customer_id}}" |
| R05 | implemented | system_prompt; opening on_enter tts | Address the customer as {{title}} {{last_name}}. |
| R06 | implemented | setup code: nowdt from vars['now']; prepare today_of / resolve_when | raw = str(vars.get('now') or '').strip() |
| R07 | implemented | opening on_enter tts | Hello, this is Freya Bank's digital assistant. Please note that we record this call. Am I speaking with {{title}} {{last_name}}? |
| R08 | implemented | opening_retry / third_party / ask_dob / ask_phone task_message | Do not mention the reason for the call, collections, a debt, a payment, a product or an amount. |
| R09 | implemented | opening on_enter tts; opening_retry task_message | Then ask exactly: "Am I speaking with {{title}} {{last_name}}?" |
| R10 | implemented | who1/who2 extraction; setup -> opening_retry; opening_retry transition 6 -> fin_unclear | unclear = anything else: 'hello', 'go ahead', 'who is this?', 'what is this about?', a question, silence. |
| R11 | implemented | system_prompt; aside extraction + finish_turn code | - If asked whether you are a robot or an AI: say "Yes, I am Freya Bank's digital assistant.", then continue. |
| R12 | implemented | third_party task_message | STRICT: Never say why you are calling. Never mention the bank account, a product, a debt, an amount, a payment or collections, even if they ask or offer to pay  |
| R13 | implemented | setup code: callback_text; third_party.task_message; tool schedule_callback; third_party transition -> fin_callback | lines.append('Today, ' + txt(today) + ' (' + today.isoformat() + '), from ' + start + ' up to 19:00.') |
| R14 | implemented | third_party.task_message; third_party transition 4 -> fin_no_callback | - If the second answer is also outside the window, or they cannot say when, do not book: call transition_to_fin_no_callback. |
| R15 | implemented | third_party transition 3 -> fin_wrong_number; setup/opening_retry routes; fin_wrong_number code | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R16 | implemented | third_party transition 2 -> fin_deceased; end_deceased terminal spoken_message | terminal: endedReason=not_reached_deceased, spoken_message="I am sorry for your loss. Goodbye." |
| R17 | implemented | third_party.task_message STRICT line | Never mention the bank account, a product, a debt, an amount, a payment or collections, even if they ask or offer to pay or help. ... Do not ask them any securi |
| R18 | implemented | ask_dob.task_message + tool verify_identity (field date_of_birth); ask_phone + verify_identity#2 (field phone_last4) | call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 19 |
| R19 | implemented | verify_identity post_process_code; ask_dob/ask_phone transition -> fin_failed on wrong_answers_left 0 | 1. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "0")  ["three wrong answers"] |
| R20 | implemented | tool verify_identity post_process_code (hint branch) | d['what_to_do_next'] = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to say the date of birth again with the month as a word, for ex |
| R21 | implemented | verify_identity post_process_code MAX_WRONG; fin_failed code; end_failed terminal spoken_message | spoken_message="I am sorry, I could not verify your identity, so I cannot continue. Please use the Freya Bank mobile app or visit a branch. Thank you, goodbye." |
| R22 | partial | ask_dob/ask_phone task_message; count_decline_* and qb_* code nodes -> fin_declined | vars['qb_route'] = 'close' if n >= 2 else 'retry' |
| R23 | implemented | verify_identity post_process_code ok=false branch; verify_identity#2 answer field description | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R24 | implemented | ask_phone transition 1 -> load_account (only route into get_account) | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True")  ["identity verifi |
| R25 | implemented | prepare code: statement (spoken by negotiate on_enter tts {{say_next}}); words = 'credit card ending ' + card_last4 or ptype.replace('_',' ') | statement = ('Thank you, ' + str(vars.get('title') or '') + ' ' + str(vars.get('last_name') or '') + '. I am calling from the collections team about a late paym |
| R26 | implemented | setup code / prepare code: HOL, BWD, isbd | HOL = set(['2026-10-26', '2026-11-11', '2026-11-26', '2026-12-25', '2027-01-01']) |
| R27 | implemented | setup code: early_deadline/late_deadline; prepare code: days_late band and rungs | if days_late <= 7: deadline = ...early_deadline; rungs = [('full_or_floor', a1)] else: ...late_deadline; rungs = [('full_or_floor', a1), ('floor', deadline)] *unverified* |
| R28 | implemented | check_offer code: check_one (before_today, after_deadline, not isbd) | if nd < t: issues.append(('before_today', ...)) ... elif nd > dl: issues.append(('after_deadline', ...)) ... elif not isbd(nd): *unverified* |
| R29 | implemented | check_offer code: check_one weekend_or_holiday branch with closed_day_move 'after'; texts weekend_or_holiday | "weekend_or_holiday": "[named] is not a business day, so I cannot record it. The next business day is [date]." |
| R30 | implemented | check_offer code: check_one vague branch (vague_asked once, then vague_again='deadline' proposes the deadline) | set_prop(V, pid, pa, dl) / say(V, join([T('vague_deadline', deadline=txt_short(dl), words=pg(V, pid, 'words')), V['offer_question']])) *unverified* |
| R31 | partial | check_offer code: resolve_when weekday branch; offer_date extraction description | delta = (7 - today.weekday()) + wd ... else: delta = (wd - today.weekday()) % 7 *unverified* |
| R32 | implemented | check_offer code: check_one after_deadline issue sets nd = dl and offers it; refusal goes through refuse() ladder | "after_deadline": "The latest date I can record is [deadline]." |
| R33 | implemented | prepare code statement (full past-due today) + negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. |
| R34 | implemented | prepare code: floor by ptype | if ptype == 'credit_card': ... floor = p.get('minimum_payment') ... else: ... floor = p.get('instalment_amount') *unverified* |
| R35 | implemented | check_offer code: too_much()/ev_offer offered_floor once; texts too_much_floor; ladder rung ('floor', deadline) | "too_much_floor": "I understand. The lowest amount I can accept is [floor], your [floor_name]. The rest stays overdue." |
| R36 | implemented | check_offer code: check_one below_floor / above_full; second below-floor -> refuse() | if pg(V, pid, 'offered_floor') == 'yes' and g(V, 'mode') != 'hardship': V['offer_verdict'] = 'below_floor'; refuse(V, pid) |
| R37 | implemented | prepare code: statement (spoken by negotiate on_enter tts {{say_next}}) | + words + '. The past-due amount is ' + fmt(past_due) + ', and it is ' + str(days_late) + ' days late. Can you make this payment today?') |
| R38 | implemented | negotiate extract stance + transition 7 -> check_offer (before count_refusal) | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R39 | implemented | setup code: attempt1_date; prepare code: rungs; policy refuse()/rung() | rungs = [('full_or_floor', a1), ('floor', deadline)] |
| R40 | implemented | policy refuse(): refused_offers skipped, exhausted -> state refused -> finalize -> fin_refused | if k >= len(L):             pset(V, pid, 'state', 'refused') |
| R41 | implemented | negotiate transition 1 -> pol_hardship; hardship node -> xfer_support / hs_decline -> fin_hardship | "hardship": "I am sorry to hear that. Would you like me to connect you with our customer support team?" |
| R42 | implemented | system prompt; negotiate/confirm/hardship task_message COMMON | - Never offer a discount, waiver, payment plan or any term you were not given. |
| R43 | implemented | policy readback() -> confirm on_enter tts; confirm transition yes -> rec_next -> record_promise | "readback_item": "[words], [amount], [when]", ... "readback_tail": ". Do you confirm?" *unverified* |
| R44 | implemented | confirm transition 1 -> change_offer; policy ev_change -> check_one -> confirm | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R45 | implemented | policy recorded_guard / ev_wrap_change; wrapup task_message | "wrap_change": "A recorded promise cannot be changed or cancelled on this call, but you can change it in the Freya Bank mobile app." |
| R46 | implemented | record_promise -> rec_after (ev_rec_after, fail_max 2) -> fin_service_error; end_service_error spoken_message | if f < int(P['fail_max']):                         V['rec_ok'] = 'pending'                         V['route'] = 'record' |
| R47 | implemented | policy enter_wrapup -> wrapup on_enter tts {{wrap_line}} | "after_recorded": "You will receive a text message confirming this promise." |
| R48 | implemented | negotiate transition 5 -> pol_paid -> fin_paid; end_paid terminal spoken_message | spoken_message="Thank you for letting me know. Payments can take one business day to appear, so I will not take a promise today. |
| R49 | implemented | negotiate/confirm topic=dispute -> pol_dispute (ev_settle) -> finalize -> fin_dispute (no_promise/dispute) | dispute = says the debt or the product is not theirs, they never had it, or it was closed or paid off in the past. |
| R50 | implemented | negotiate/confirm/wrapup topic new_plan -> xfer_restructuring (transfer_to_agent#2 queue restructuring) -> fin_transferred_restructuring | 2. -> xfer_restructuring  if (topic equals "new_plan")  ["topic new_plan"] |
| R51 | implemented | ask_dob/ask_phone task_message + transfer_to_agent queue general; pol_human ev_human human_limit 2 -> xfer_general -> fin_transferred_human | - If the customer asks for a human: the first time, ask whether you can help them yourself. If they insist, call transfer_to_agent. |
| R52 | implemented | system_prompt; asides scam in policy finish_turn | - If asked whether this is a scam: say they can verify this call by phoning Freya Bank's customer service number, then continue. |
| R53 | implemented | system_prompt; COMMON in negotiate/confirm/hardship/wrapup | - Never invent figures, dates or reasons. If you do not have the information, say so. |
| R54 | implemented | pol_notalk ev_notalk notalk_limit 2 -> fin_refused; count_decline_dob/phone decline_count 2 -> fin_declined; opening_retry who2 refuses -> fin_declined | if c >= int(P['notalk_limit']): |
| R55 | implemented | tool close_call (alwaysRunsAt end_of_call) reading outcome/reason set by fin_* code nodes | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R56 | implemented | FINS table -> fin_* nodes; close_call outcome enum and reason description | reason_desc="transferred: restructuring/human/support. no_promise: refused/hardship/dispute/service_error. not_verified: failed/declined. not_reached: callback/ |
| R57 | implemented | wrapup transitions -> wrap_human -> xfer_general -> fin_transferred_human; wrapup new_plan -> xfer_restructuring -> fin_transferred_restructuring | 3. -> xfer_restructuring  if (wrap equals "new_plan")  ["asks for a new plan"] |
| R58 | implemented | POLICY multi=False, notes=False; no add_note tool defined | multi=False, notes=False,                                   # one product; Brief A never uses add_note |
| R59 | partial | end_* terminal spoken_message | terminal: endedReason=not_reached_deceased, spoken_message="I am sorry for your loss. Goodbye." |
| R60 | implemented | tool close_call lifecycle end_of_call + pre_process_code; fin_* nodes set reason for every other outcome | if b.get('outcome') in ('promise', 'paid') or not b.get('reason'): |
| R61 | implemented | tool create_promise body defaults + pre_process_code; rec_next code sets rec_pid/rec_amount/rec_date | want = [('product_id', str(vars.get('rec_pid') or '')), ('amount', str(vars.get('rec_amount') or '')), ('date', str(vars.get('rec_date') or '')[:10])] |
