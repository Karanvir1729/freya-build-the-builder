# Coverage audit: brief-d.workflow.json

Rules: `brief-d.rules.json`. Generator: `gen_brief-d.py`. Model claude-opus-5-5, 76 s, $1.82, 10 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 99 | 2 | 0 | 0 | 16 | 117 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R75** (partial): Whenever at least one promise was recorded and no transfer followed, close `promise` / PRM regardless of notes on other products.
   - why: When a promise is recorded, the finalize code still defaults to close_outcome='no_promise' / close_code='RF'. So if the customer hangs up or adds a note on another product before wrapup reaches fin_promise, close_call sends no_promise/RF instead of promise/PRM.
   - fix: 1) In tool create_promise post_process_code, when the result is ok (data.ok true/'True'), set vars['promise_recorded']='true', vars['close_outcome']='promise' and vars['close_code']='PRM'. 2) In finalize code, replace the default with: if vars.get('promise_recorded') in ('true','True') and not vars.get('transferred'): close_outcome='promise', close_code='PRM', else the current no_promise/RF. 3) In wrapup, put a transition before the others: promise_recorded equals 'true' and the customer ends or other products only get notes -> fin_promise. 4) Have every xfer_* node set vars['transferred']='true' so that a transfer after a promise still closes as transferred.
2. **R53** (partial): Plan/lower instalments/more time requests: describe nothing, `transfer_to_agent` queue `restructuring`, close transferred TRS.
   - why: A customer in hardship who asks for a payment plan, lower instalments or more time is told 'you cannot offer that' and is not transferred, so close_call never gets transferred/TRS and the transfer_to_agent call with queue restructuring is missing.
   - fix: In the hardship and hardship_notes nodes: add the value new_plan to the topic enum in extraction_schema ('wants a plan / lower instalments / more time'). Add the transition 'topic equals "new_plan" -> xfer_restructuring', evaluated before the other routes. In hardship.task_message, replace 'if they ask for one, say you cannot offer that' with 'If they ask for a payment plan, lower instalments or more time, do not describe or promise any plan terms; tell them you will pass them to a colleague who handles this, and transfer.' Make sure xfer_restructuring calls transfer_to_agent with queue='restructuring' baked in, and that its fin node sets outcome='transferred' and reason='TRS'.

## partial (2)

- **R53** (_brief-d.md item 1 'Other things'_): Plan/lower instalments/more time requests: describe nothing, `transfer_to_agent` queue `restructuring`, close transferred TRS.
  - where: negotiate transition topic=new_plan -> xfer_restructuring; wrapup wrap=new_plan -> xfer_restructuring
  - evidence: `4. -> xfer_restructuring  if (topic equals "new_plan")  ["wants a plan / lower instalments / more time"]`
  - fix: In the hardship node (and hardship_notes), add a new_plan value to the extraction that routes to xfer_restructuring, and replace the hardship task_message line 'if they ask for one, say you cannot offer that' for plan requests.
- **R75** (_brief-d.md item 4 closing with several products_): Whenever at least one promise was recorded and no transfer followed, close `promise` / PRM regardless of notes on other products.
  - where: finalize code -> wrapup -> fin_promise
  - evidence: `vars['close_outcome'] = 'no_promise'
    vars['close_code'] = 'RF'`
  - fix: Set vars close_outcome='promise' and close_code='PRM' in create_promise post_process_code as soon as a promise is recorded (or in finalize when rec is set), so that a hang-up in negotiate/wrapup after a recorded promise does not close as no_promise/RF

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | setup code: s_deadline (memo 1), prepare BANDS (memo 2), prepare floor (memo 3), HOL set (memo 4), fin_hardship HSHP (memo 5), callback_text 09:00-18:00 (memo 6) | vars['s_deadline'] = addbd(today, 5).isoformat() |
| R02 | superseded | superseded by  |  |
| R03 | implemented | prepare code: BANDS / WORDS / multi-product statement_text | BANDS = [('F', 10, 1, 'f_deadline', None), ('S', None, 2, 's_deadline', None)] |
| R04 | implemented | setup code: today derived from vars['now'] | raw = str(vars.get('now') or '').strip() |
| R05 | implemented | every tool definition body.customer_id incl. close_call | body.customer_id (string): default "{{customer_id}}" |
| R06 | implemented | tool create_promise pre_process_code (deadline/amount cap, closed-day snap) + negotiate.task_message RULES PER PRODUCT | if dl and b.get('date') and str(b['date']) > dl: |
| R07 | implemented | opening on_enter tts | on_enter tts: "This is the digital assistant of Kestrel Bank. Please note that this call is recorded. Am I speaking with {{first_name}} {{last_name}}?" |
| R08 | implemented | opening on_enter tts; opening_retry.task_message | Then ask exactly: "Am I speaking with {{first_name}} {{last_name}}?" |
| R09 | implemented | ask_phone.task_message; system prompt | The person confirmed they are {{first_name}} {{last_name}}. From now on address them as {{title}} {{last_name}}. |
| R10 | implemented | opening extraction who1 desc; setup transition -> opening_retry; opening_retry always -> fin_unclear (not_reached/UNC) | unclear = anything else: 'hello', 'go ahead', 'who's asking', 'what is this about?', any question, silence. |
| R11 | implemented | setup transition 5 -> opening_retry; opening_retry transition 6 -> fin_unclear | vars['close_outcome'] = 'not_reached'     vars['close_code'] = 'UNC' |
| R12 | implemented | opening_retry.task_message | This is your second and LAST ask. ... If the person asked a question, answer it first in one sentence: who is this -> you are the digital assistant of Kestrel B *unverified* |
| R13 | implemented | system prompt 'Always' list; opening_retry/ask_phone task_message | - Robot or AI question: say exactly "I am Kestrel Bank's digital assistant." and carry on. |
| R14 | implemented | SYSTEM PROMPT 'Always' list; also opening_retry and ask_phone/ask_dob task_message | - Scam question: they are welcome to hang up and call the number on the back of their card or on their statement; carry on. |
| R15 | implemented | opening_retry / third_party / ask_phone / ask_dob task_message NEVER_SAY; opening task_message | NEVER say, before identity is confirmed: arrears, overdue, late, collections, debt, payment, instalment, or the name of any product (credit card, loan, car loan |
| R16 | implemented | third_party.task_message | In your first reply ALWAYS say that this is a personal banking matter that you can only discuss with {{title}} {{last_name}} (also when they already said when t |
| R17 | superseded | superseded by R111 |  |
| R18 | superseded | superseded by  |  |
| R19 | implemented | third_party tool schedule_callback + transition -> fin_callback (not_reached/CBK) | 1. -> fin_callback  if (schedule_callback_response.data.ok equals "true" OR schedule_callback_response.data.ok equals "True")  ["callback booked"] |
| R20 | implemented | third_party.task_message + transition_to_fin_no_callback -> fin_no_callback (not_reached/NCB) | - Outside the window -> propose ONCE the nearest slot inside the window (a precise day and HH:MM). If they accept, book it. |
| R21 | implemented | third_party transition tp_status=wrong_number -> fin_wrong_number (not_reached/WN) | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R22 | implemented | third_party transition -> fin_deceased; end_deceased terminal spoken_message | terminal: endedReason=not_reached_DEC, spoken_message="Please accept my condolences. Thank you, goodbye." |
| R23 | implemented | third_party.task_message STRICT block | Ask no security question. If they offer to pay, to answer questions, or to help, decline politely (you can only discuss it with {{title}} {{last_name}}) and ask |
| R24 | implemented | ask_phone (verify_identity field phone_last4) -> ask_dob (verify_identity#2 field date_of_birth) | Before anything else you must check identity with two security questions, one at a time. Ask the first now: the last four digits of their phone number. |
| R25 | superseded | superseded by  |  |
| R26 | implemented | ask_dob.task_message | call verify_identity with answer = the date as YYYY-MM-DD, however they said it. A date said only as numbers is day, then month, then year (05/03/1990 = 1990-03 |
| R27 | implemented | ask_phone/ask_dob transition 1 -> fin_failed; verify_identity post_process_code | 1. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "1" OR verify_identity_response.data.wrong_answers_left equals "0")  ["second wron |
| R28 | implemented | verify_identity#2 post_process_code hint branch | d['what_to_do_next'] = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month as a word, for examp |
| R29 | implemented | ask_phone/ask_dob transition 1 -> fin_failed (wrong_answers_left 1/0); verify_identity post_process_code; end_failed terminal spoken_message | terminal: endedReason=not_verified_IDF, spoken_message="For security I cannot continue by phone. You can use the Kestrel mobile app or visit a branch. Thank you |
| R30 | implemented | ask_phone/ask_dob task_message 'Rules for this step'; count_decline_* code (second decline -> fin_declined IDD) | explain that the questions are there to protect their account and that nothing can be discussed without them, and ask the question again. |
| R31 | implemented | ask_phone/ask_dob transition all_verified -> load_account (get_account pre_action) | -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True") |
| R32 | implemented | prepare code: statement_text, spoken by negotiate on_enter tts | I am calling from the arrears team about an overdue payment. Your {words} has an overdue amount of {past_due}, and it is {days_late} days overdue. |
| R33 | implemented | system prompt; negotiate.task_message OTHER | - Never mention consequences (fees, credit file, legal action, collectors). |
| R34 | implemented | prepare code: statement_text (single and many_tail), negotiate on_enter tts | st += _fill('Are you able to clear all of these today?', base) |
| R35 | implemented | negotiate.task_message rule 1 | 1. You propose every amount. NEVER ask how much they can pay, in any wording. |
| R36 | implemented | negotiate.task_message rule 3; prepare code floor (card min(2 x minimum_payment, past_due), loans instalment_amount) | offer that product's floor ONCE and say: the remainder stays overdue and we will be in touch about it. Floor declined = flat refusal. |
| R37 | superseded | superseded by  |  |
| R38 | implemented | negotiate.task_message rule 2 with CALENDAR | 2. A date or an amount the customer names is NEVER a refusal and uses no attempt. Check it: |
| R39 | implemented | negotiate.task_message rules 2 and 4; prepare code BANDS (F 1 attempt, S 2 attempts) | 4. A flat refusal, a non-answer, or a no to paying today with no date and no amount uses ONE persuasion attempt of that product. |
| R40 | implemented | negotiate.task_message rules 4 and 8; finalize code default 'refused' -> fin_refused (no_promise RF) | When that product's attempts are used up, stop: never repeat an offer already turned down; that product is refused. |
| R41 | implemented | negotiate topic=hardship -> hardship node (on_enter tts); support_choice accept -> xfer_support (queue support) -> fin_transferred_support TSP | on_enter tts: "I am sorry to hear that. I can put you through to our customer care team, who can help. Would you like me to do that?" |
| R42 | implemented | hardship transition support_choice=accept -> xfer_support (queue support) -> fin_transferred_support | vars['close_code'] = 'TSP' |
| R43 | implemented | hardship_notes.task_message; finalize -> fin_hardship (HSHP per memo 5 overriding HARD) | Then call add_note with reason hardship for each product still open: {{open_pids}} (ids from PRODUCTS), one per message, with the circumstance in the customer's |
| R44 | implemented | hardship.task_message; finalize -> wrapup -> fin_promise | Only if the customer themselves names a date or an amount for a product: check it against PRODUCTS and the CALENDAR, read it back ending with "Shall I record th |
| R45 | implemented | system prompt; negotiate.task_message OTHER; hardship.task_message | Never offer a discount, waiver, payment holiday, plan or any term you were not given. |
| R46 | implemented | negotiate.task_message item 6 | ending with exactly "Shall I record that?". If they change a date or an amount, check it again and read back again. After a clear yes, call create_promise once  |
| R47 | implemented | create_promise description + post_process_code; negotiate OTHER; wrapup.task_message | They want to change or cancel a recorded promise -> say it cannot be changed or cancelled in this call, then ask if there is anything else. |
| R48 | implemented | negotiate.task_message item 7; create_promise post_process_code | Never say a promise is recorded before create_promise returned ok. |
| R49 | implemented | create_promise post_process_code; negotiate item 7; finalize -> fin_service_error | msg = 'NOT recorded, failed 3 times. Tell the customer you could not record the promise for ' + pid + ', then call add_note for ' + pid + ' with reason service_ |
| R50 | implemented | wrapup on_enter tts (first_only), entered from finalize after all promises | on_enter tts: "We will email you a confirmation of this arrangement. Is there anything else I can help you with?" |
| R51 | implemented | negotiate.task_message item 5; add_note text description; finalize -> fin_paid (AP) | 'I already paid' (a product) -> say exactly "Payments made today show on our side on the next business day.", take no promise for it, ask how and on which day t |
| R52 | implemented | negotiate.task_message item 5; finalize -> fin_dispute (DSP) | 'That is not mine' / 'I never had this' -> do not argue, no promise for it, noted dispute. |
| R53 | partial | negotiate transition topic=new_plan -> xfer_restructuring; wrapup wrap=new_plan -> xfer_restructuring | 4. -> xfer_restructuring  if (topic equals "new_plan")  ["wants a plan / lower instalments / more time"] |
| R54 | implemented | ask_phone/ask_dob/negotiate/hardship tool transfer_to_agent (queue general) + transition -> fin_transferred_human (TRH); wrapup human -> xfer_general | 4. -> fin_transferred_human  if (transfer_to_agent_success_count greater_than 0)  ["transferred"] |
| R55 | implemented | opening_retry refuses -> fin_declined; count_decline_phone/dob -> fin_declined (IDD); negotiate.task_message OTHER + finalize -> fin_refused (RF) | - They say they do not want to talk -> say once this will only take a moment. If they say it again: every product without a promise is refused; call add_note fo |
| R56 | implemented | system_prompt; negotiate.task_message OTHER; wrapup.task_message | - Never invent figures, dates or reasons. A question you cannot answer: "I don't have that information." |
| R57 | implemented | prepare code (per-product band/deadline from days_late, statement_text); negotiate.task_message ORDER OF WORK C | C. Otherwise go through the products ONE BY ONE in PRODUCTS order. Never ask about today again. |
| R58 | implemented | negotiate.task_message ORDER OF WORK C + prepare products_text per-product attempts | Each product starts at its attempt 1, unless the customer already named a date or an amount for it. |
| R59 | implemented | prepare statement_text ('Are you able to clear all of these today?'); negotiate.task_message C | C. Otherwise go through the products ONE BY ONE in PRODUCTS order. Never ask about today again. Each product starts at its attempt 1 |
| R60 | implemented | negotiate.task_message ORDER OF WORK B; create_promise pre_process_code caps date to dl_ and snaps back | A product whose latest date is earlier than the named date goes on ITS OWN latest date (say so in the read-back). A named closure day or weekend moves to the bu |
| R61 | implemented | negotiate.task_message item 6 | ending with exactly "Shall I record that?". If they change a date or an amount, check it again and read back again. After a clear yes, call create_promise once  |
| R62 | implemented | negotiate.task_message item 8; add_note tool enum; hardship_notes | 8. Then for EVERY product without a recorded promise call add_note (reason refused, hardship, dispute, paid, service_error) with the text the note requires; als |
| R63 | implemented | negotiate.task_message items 5 and 7; create_promise post_process_code | 'That is not mine' / 'I never had this' -> do not argue, no promise for it, noted dispute. Then carry on with the other products. |
| R64 | implemented | negotiate.task_message OTHER; add_note description; transfer transitions -> fin_transferred_* (TRH/TRS/TSP) | - They ask for a person -> call transfer_to_agent straight away (no notes after a transfer). |
| R65 | implemented | create_promise post_process_code (fail_<pid> >= 3); negotiate.task_message item 7 | msg = 'NOT recorded, failed 3 times. Tell the customer you could not record the promise for ' + pid + ', then call add_note for ' + pid + ' with reason service_ |
| R66 | implemented | end_* terminals spoken_message (e.g. end_promise, end_refused) | terminal: endedReason=promise_PRM, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R67 | implemented | close_call lifecycle tool (alwaysRunsAt end_of_call) + fin_promise code | vars['close_outcome'] = 'promise'     vars['close_code'] = 'PRM' |
| R68 | implemented | close_call body outcome enum + reason default {{close_code}}; setup code defaults close_code UNC; every fin_* sets a code | body.reason (string): default "{{close_code}}"; The dialler code: PRM, AP, TRS, TRH, TSP, RF, HSHP, DSP, SVC, IDF, IDD, CBK, NCB, WN, DEC, UNC. Never empty. |
| R69 | superseded | superseded by R109 |  |
| R70 | implemented | wrapup transitions -> xfer_restructuring / xfer_general -> fin_transferred_*; negotiate transition -> fin_transferred_human | 1. -> xfer_restructuring  if (wrap equals "new_plan")  ["wants a plan / lower instalments"] |
| R71 | superseded | superseded by R109 |  |
| R72 | implemented | tool add_note description/enum/text; prepare fail -> fin_service_error (no notes); negotiate.task_message item 8 | description: Record why ONE product ends the call without a promise. CALL it once for every product without a recorded promise. Never after a transfer. |
| R73 | implemented | tool add_note body.reason enum and body.text description; hardship_notes task_message | refused -> the number of persuasion attempts made and the last offer (amount and date), e.g. '2 attempts; last offer 440 on 2026-10-21'; hardship -> the circums |
| R74 | superseded | superseded by R110 |  |
| R75 | partial | finalize code -> wrapup -> fin_promise | vars['close_outcome'] = 'no_promise'     vars['close_code'] = 'RF' |
| R76 | implemented | prepare code BANDS per product; setup code s_deadline = addbd(today, 5) | BANDS = [('F', 10, 1, 'f_deadline', None), ('S', None, 2, 's_deadline', None)] |
| R77 | superseded | superseded by R103 |  |
| R78 | superseded | superseded by R106 |  |
| R79 | implemented | negotiate.task_message rule 2; create_promise pre_process_code caps amount at pd_<pid> | Amount from the floor up to the full amount, both included -> accept as proposed. |
| R80 | superseded | superseded by R107 |  |
| R81 | superseded | superseded by R107 |  |
| R82 | implemented | negotiate DATES section + create_promise pre_process_code snaps to previous business day | A promise date must be today or later, a business day (Monday to Friday, not a closure day), and not after THAT product's latest date. |
| R83 | superseded | superseded by R111 |  |
| R84 | implemented | negotiate.task_message rules 1, 2, 3 and A | Full amount too much, cannot pay it all, or 'is there a smaller amount' -> offer that product's floor ONCE and say: the remainder stays overdue and we will be i |
| R85 | implemented | negotiate.task_message ORDER OF WORK A and rule 2 | A. They can clear everything today: each product, full overdue amount, today. Go to READ-BACK. |
| R86 | implemented | negotiate.task_message rule 2 | - Amount from the floor up to the full amount, both included -> accept as proposed. |
| R87 | implemented | negotiate.task_message rule 2 + tool create_promise pre_process_code (amount capped at pd_<pid>) | More than the full amount -> record the full amount. |
| R88 | implemented | negotiate.task_message rule 2 | Below the floor -> say it cannot be recorded and offer the floor once; floor declined = flat refusal. |
| R89 | implemented | negotiate.task_message rule 3 | 3. Full amount too much, cannot pay it all, or 'is there a smaller amount' -> offer that product's floor ONCE and say: the remainder stays overdue and we will b |
| R90 | implemented | negotiate.task_message rule 1 | 1. You propose every amount. NEVER ask how much they can pay, in any wording. If they ask 'how much should I pay?', propose the amount in play. |
| R91 | implemented | negotiate.task_message DATES + rule 2; prepare code calendar_text | - A promise date must be today or later, a business day (Monday to Friday, not a closure day), and not after THAT product's latest date. |
| R92 | implemented | negotiate.task_message rule 2 | - Date allowed for that product in the CALENDAR -> accept it exactly as named. |
| R93 | implemented | negotiate.task_message rule 2 + DATES; setup code vague_iso; prepare code calendar_text | - Weekend or closure day not after the latest date -> say the bank is closed that day and offer the business day BEFORE it shown in the CALENDAR. |
| R94 | implemented | negotiate.task_message rule 2 | - After the product's latest date -> say the latest date is the last day that can be recorded and offer it. If they refuse it, that is a flat refusal. |
| R95 | implemented | negotiate.task_message rule 2 | say that day has passed and cannot be recorded, and ask which day from today onwards they can pay. |
| R96 | implemented | negotiate.task_message rule 2 + DATES; setup code: vague_iso | - Vague period with no exact day after you asked once: propose {{vague_text}} ({{vague_iso}}), or the product's latest date if that is earlier. |
| R97 | implemented | setup code: weekday_table (this_d / next_d) | next_d = today + datetime.timedelta(days=(k if k > 0 else 7)) |
| R98 | implemented | negotiate.task_message RULES PER PRODUCT items 2 and 4; prepare code products_text attempt 1 | 4. A flat refusal, a non-answer, or a no to paying today with no date and no amount uses ONE persuasion attempt of that product. |
| R99 | implemented | prepare code: products_text line (Attempt 1) | Attempt 1: propose the amount in play ({past_due}, or the floor {floor} once the customer said the full amount is too much) on {a1_text} ({a1_iso}). |
| R100 | superseded | superseded by R104 |  |
| R101 | implemented | negotiate.task_message item 4 + item 8 (add_note refused); finalize -> fin_refused | When that product's attempts are used up, stop: never repeat an offer already turned down; that product is refused. |
| R102 | superseded | superseded by R103 |  |
| R103 | implemented | setup code: f_deadline / s_deadline; prepare code BANDS | BANDS = [('F', 10, 1, 'f_deadline', None), ('S', None, 2, 's_deadline', None)] |
| R104 | implemented | setup code: attempt1_date; prepare code attempt templates | Attempt 2: propose the floor {floor} on the latest date {deadline_text} ({deadline_iso}). Persuasion attempts for this product: {attempts}. |
| R105 | implemented | negotiate.task_message item 4 | When that product's attempts are used up, stop: never repeat an offer already turned down; that product is refused. |
| R106 | implemented | prepare code: floor computation | floor = (min(2 * float(p.get('minimum_payment') or 0), amount)) |
| R107 | implemented | setup/prepare code HOL; create_promise pre_process_code _hol; calendar_text | HOL = set(['2026-10-30', '2026-11-20', '2026-12-24', '2026-12-25', '2026-12-28', '2026-12-31']) |
| R108 | superseded | superseded by  |  |
| R109 | implemented | fin_hardship code node -> end_hardship; hardship_notes -> finalize | vars['close_outcome'] = 'no_promise'     vars['close_code'] = 'HSHP' |
| R110 | implemented | finalize code node precedence + transitions; transfers route to fin_transferred_* first | for reason, key in [('service_error', 'service_error'), ('hardship', 'hardship'), ('dispute', 'dispute'), ('refused', 'refused')]: |
| R111 | implemented | setup code: callback_text; schedule_callback field descriptions | lines.append(txt(nbd) + ' (' + nbd.isoformat() + '), from 09:00 up to 18:00 included.') |
| R112 | implemented | opening on_enter tts; ask_phone -> ask_dob; FAILED transition on wrong_answers_left 1/0 | -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "1" OR verify_identity_response.data.wrong_answers_left equals "0") |
| R113 | implemented | tool verify_identity / verify_identity#2 field_descriptions + post_process_code ok=false branch | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R114 | implemented | load_account reached only via all_verified transition in ask_phone/ask_dob; prepare code floor rules | if ptype in ('credit_card',): floor_name = 'twice the minimum payment' ... floor = p.get('instalment_amount') |
| R115 | implemented | tool close_call (alwaysRunsAt end_of_call); setup code default close_code UNC; fin_* nodes set close_code | body.reason (string): default "{{close_code}}"; The dialler code: PRM, AP, TRS, TRH, TSP, RF, HSHP, DSP, SVC, IDF, IDD, CBK, NCB, WN, DEC, UNC. Never empty. |
| R116 | implemented | tool create_promise body + pre_process_code | body.date* (string): default "{{date}}"; The agreed payment date for this product as YYYY-MM-DD. |
| R117 | implemented | tool add_note body (required product_id, reason enum) | body.reason* (string): default "{{reason}}"; enum ["refused", "hardship", "dispute", "paid", "service_error"] |
