# Coverage audit: brief-c_v3.workflow.json

Rules: `brief-c.rules.json`. Generator: `gen_brief-c_v3.py`. Model claude-opus-5-5, 70 s, $2.54, 7 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 62 | 2 | 0 | 0 | 0 | 64 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R34** (partial): If the customer says the full amount is too much, propose the floor once and say the remainder stays overdue and the account stays in arrears until cleared. Declining the floor is a flat refusal (rule 31). The floor may be named a second time only as attempt 2 (rule 31).
   - why: After the customer says 'too much' and turns down the floor, rung 0 still becomes the floor. So attempt 1 names the floor a second time, which rule 27/31 forbids. It also delays the flat-refusal path, so the closing outcome/reason and the number of offers are wrong in every 'too much, then decline' case.
   - fix: check_offer code, rung(): in the `elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes':` branch, add the condition `and pg(V, pid, 'offered_floor') != 'yes'`. Then the floor replaces the full amount only the first time. Also in check_offer: when offered_floor == 'yes' and the customer declines, set vars['refusal']='flat' and route to the flat-refusal ending (rule 31). The exception is attempt 2: there, allow the floor to be named again only when vars['attempt'] == 2. In negotiate.task_message, add: "You may name the floor amount only once, after the customer says the full amount is too much. Say the remainder stays overdue and the account stays in arrears until cleared. If they decline the floor, treat it as a flat refusal. Do not name the floor again unless this is attempt 2."
2. **R01** (partial): The call is to customers whose payment on a single product is between 1 and 45 days overdue: reach the right person, run the security check, explain the overdue amount, agree a payment where possible, and end with the outcome and reason from section 12. Nothing in the brief may be replaced by the assistant's own judgement.
   - why: prepare code always negotiates prods[0]. It never checks that days_late is between 1 and 45, so a customer with 0 days or more than 45 days late is still negotiated with on green/amber rules, and the call ends with an outcome/reason the brief doesn't allow for that customer.
   - fix: prepare code: after days_late is computed, add `if days_late < 1 or days_late > 45: vars['out_of_scope']='yes'` (otherwise 'no'). Add a first transition on prepare: `out_of_scope equals 'yes'` -> a fin_out_of_scope code node that sets outcome/reason to the section-12 pair for a case the agent can't handle (for example the no-agreement/callback or transfer reason the brief defines). It should lead to an end terminal with a neutral farewell, so the agent doesn't negotiate. Also make sure only one product is handled (POLICY multi=False is already set).

## partial (2)

- **R01** (_brief-c.md section 1_): The call is to customers whose payment on a single product is between 1 and 45 days overdue: reach the right person, run the security check, explain the overdue amount, agree a payment where possible, and end with the outcome and reason from section 12. Nothing in the brief may be replaced by the assistant's own judgement.
  - where: prepare code (single product prods[0]); POLICY multi=False; fin_* nodes set outcome/reason
  - evidence: `if days_late <= 10:                        # R19 green: the 9th business day after today, 2 attempts`
  - fix: In prepare code, add a guard for days_late < 1 or > 45 (outside the brief's population) that routes to a defined ending instead of negotiating.
- **R34** (_brief-c.md rule 27_): If the customer says the full amount is too much, propose the floor once and say the remainder stays overdue and the account stays in arrears until cleared. Declining the floor is a flat refusal (rule 31). The floor may be named a second time only as attempt 2 (rule 31).
  - where: check_offer code: too_much(); texts.too_much_floor; rung() full_or_floor
  - evidence: `elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes':`
  - fix: In rung(), stop rung 0 from turning into the floor when the floor was already offered (offered_floor == 'yes'), so that after 'too much' and a declined floor, attempt 1 does not name the floor again; the floor may be named a second time only as attempt 2.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | partial | prepare code (single product prods[0]); POLICY multi=False; fin_* nodes set outcome/reason | if days_late <= 10:                        # R19 green: the 9th business day after today, 2 attempts |
| R02 | implemented | tool bodies customer_id default; system prompt {{title}} {{last_name}}; setup code reads vars['now'] | raw = str(vars.get('now') or '').strip() |
| R03 | implemented | every tool definition body.customer_id | body.customer_id (string): default "{{customer_id}}" |
| R04 | implemented | system prompt; prepare statement 'Thank you, ' + title + last_name | After the security check, address the customer as {{title}} {{last_name}}. |
| R05 | implemented | setup code (today from now); prepare resolve_when uses today_of(V) | # (date, kind) from the customer's OWN WORDS, relative to the call's today (never the real clock |
| R06 | implemented | opening on_enter tts | on_enter tts: "Good day, this is the virtual assistant of Nordvik Savings Bank, and this call is recorded. Am I speaking with {{first_name}} {{last_name}}?" |
| R07 | implemented | system prompt; opening_retry, third_party, ask_phone/ask_dob task_message | - Until the security check is complete, never use the words overdue, arrears, collections, payment or debt, and never name a product, to anyone. |
| R08 | implemented | opening on_enter tts | Am I speaking with {{first_name}} {{last_name}}? |
| R09 | implemented | opening who1 extraction; setup transitions -> opening_retry; opening_retry always -> fin_unconfirmed | Then ask exactly: "Am I speaking with {{first_name}} {{last_name}}?" This is the second and last time you ask. |
| R10 | implemented | system prompt; opening_retry, ask_phone, third_party, negotiate task_message; aside extraction | - If asked whether you are a robot, an AI or a machine: say exactly "I am an automated assistant of Nordvik Savings Bank, and this conversation is recorded." an |
| R11 | implemented | third_party.task_message | If they ask what it is about, offer to pay, or offer to take a message, repeat that you can discuss it only with the customer. |
| R12 | implemented | setup code callback_text; third_party tool schedule_callback; transition -> fin_scheduled | lines.append(txt(nbd) + ' (' + nbd.isoformat() + '), from 09:00 up to 18:00 included.') |
| R13 | implemented | third_party.task_message + transition_to_fin_no_slot -> fin_no_slot (not_reached/no_slot) | - If the second slot is also outside the window, or they cannot say when, book nothing: call transition_to_fin_no_slot. |
| R14 | implemented | third_party transition tp_status=wrong_number -> fin_wrong_party; end_wrong_party terminal | terminal: endedReason=not_reached_wrong_party, spoken_message="I apologise for the disturbance. Thank you for your time. Goodbye from Nordvik Savings Bank." |
| R15 | implemented | third_party transition tp_status=deceased -> fin_estate; end_estate terminal spoken_message | terminal: endedReason=not_reached_estate, spoken_message="Please accept my condolences. Thank you for your time. Goodbye from Nordvik Savings Bank." |
| R16 | implemented | third_party.task_message STRICT block | Never ask them a security question and arrange nothing with them except a callback. |
| R17 | implemented | ask_phone (verify_identity field phone_last4) -> ask_dob (verify_identity#2 field date_of_birth) | When they give four digits, call verify_identity with answer = the four digits only. Do not ask the date of birth before this question has passed. |
| R18 | implemented | ask_dob.task_message; verify_identity post_process_code ok:false branch | If the customer gives the date ONLY in numbers (for example 3/7/85), do not call the tool: ask them to say the month as a word, then call it. |
| R19 | implemented | verify_identity post_process_code (shared id_wrong counter, id_route) + ask_phone/ask_dob transition id_route=exhausted -> fin_exhausted | done = nw >= 2 or str(left) == '0' |
| R20 | implemented | verify_identity post_process_code hint_day_month_swapped counter | msg = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month said as a word, for example 14 March  |
| R21 | implemented | fin_exhausted (not_verified/exhausted) + end_exhausted terminal spoken_message | A colleague can complete the check if you call the number on the back of your card or on your latest statement. |
| R22 | implemented | ask_phone/ask_dob task_message + refusal_* -> count_decline_* (decline_count >= 2 -> fin_withheld) | vars['decline_route'] = 'close' if n >= 2 else 'retry' |
| R23 | implemented | ask_dob transition all_verified -> load_account (get_account); system prompt | After the security check, address the customer as {{title}} {{last_name}}. |
| R24 | implemented | prepare code: statement + product words; system prompt forbids collections | I am calling from the payments team of Nordvik Savings Bank about an overdue amount on your ' + words + '. The overdue amount is ' + fmt(past_due) + ', and it i |
| R25 | implemented | setup code: HOL, BWD, isbd (also prepare/check_offer code) | HOL = set(['2026-10-16', '2026-11-02', '2026-11-21', '2026-12-08', '2026-12-24', '2026-12-25', '2026-12-26', '2026-12-31']) |
| R26 | implemented | prepare code: deadline and rungs by days_late | if days_late <= 10:                        # R19 green: the 9th business day after today, 2 attempts |
| R27 | implemented | check_offer code: check_one (before_today / after_deadline / not isbd) | if nd < t: |
| R28 | implemented | check_offer code: check_one weekend_or_holiday branch; texts.weekend_or_holiday | "weekend_or_holiday": "[named] is not a business day. The next business day is [date]." |
| R29 | implemented | check_offer code: resolve_when weekday_rule first_after; offer_date extraction description | delta = (wd - today.weekday()) % 7 or 7   # the first such weekday AFTER today, also when said on that weekday |
| R30 | implemented | check_offer code: check_one vague branch with vague_again='refuse' | if P.get('vague_again') == 'refuse':   # the brief: no exact day after one ask = a non-answer (one attempt) |
| R31 | implemented | check_offer code: check_one after_deadline branch (nd = dl, offer question); stance refuse -> count_refusal | "after_deadline": "The latest date the bank can record is [deadline]." |
| R32 | implemented | prepare code: init_negotiation/prop_of full amount today; negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask what they can pay or how much they can afford. |
| R33 | implemented | prepare code: floor computation | floor = float(math.ceil(round(past_due * 0.4, 2) - 1e-9))   # R26: 40%, rounded up to the next whole unit |
| R34 | partial | check_offer code: too_much(); texts.too_much_floor; rung() full_or_floor | elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes': |
| R35 | implemented | check_offer code: check_one below_floor / above_full branches, above_full='agree' | "below_floor": "The smallest amount the bank can record is [floor]." |
| R36 | implemented | prepare code: statement -> negotiate on_enter tts {{say_next}} | days overdue. Are you able to settle the full overdue amount today?')   # R18, R29 |
| R37 | implemented | negotiate extraction stance/offer_kind + transition 7 -> check_offer (before count_refusal) | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R38 | implemented | prepare code: rungs (green 2, amber 1) + policy refuse()/rung() using attempts_used and too_much | rungs = [('full_or_floor', a1), ('floor', deadline)]   # R31 attempt 2 (green only): the floor on the deadline |
| R39 | implemented | policy refuse(): exhausted -> state refused -> finalize fin_keys refused -> fin_declined_offer | if okey(a, d) not in rl: |
| R40 | implemented | policy texts hardship + hardship node transitions -> xfer_support (queue support) -> fin_care_team; hs_decline -> fin_financial_distress / end_financial_distress | "hardship": "I am sorry to hear that. I will not ask you for a payment today. The bank's care team can review your situation. May I connect you with them now?" |
| R41 | implemented | negotiate/confirm/hardship/wrapup task_message COMMON + aside 'reduction' | - Never offer or agree to a discount, a waiver, a fee reversal, an instalment plan or any date later than the latest date. If asked for one, say "I cannot offer |
| R42 | implemented | policy readback() -> confirm on_enter tts {{readback_line}}; confirm transition yes -> rec_next -> record_promise | "readback_item": "[amount] [when] for your [words]", ... "readback_tail": ". Shall I record this?" *unverified* |
| R43 | implemented | confirm transition change -> change_offer; ev_change -> check_one -> agree -> advance -> confirm | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R44 | implemented | Policy multi=False (one product); wrapup wrap=change -> wrap_change with wrap_change text | "wrap_change": "A recorded promise is not changed or cancelled during this call. The payments line can change it." |
| R45 | implemented | record_promise rec_ok mapping + ev_rec_after (fail_max 3) -> service_error -> fin_system_fault / end_system_fault | if f < int(P['fail_max']): |
| R46 | implemented | policy enter_wrapup -> wrapup on_enter tts {{wrap_line}} | "recorded": "I have noted your promise. A confirmation will be sent to your registered email address." |
| R47 | implemented | topic already_paid -> pol_paid -> finalize -> fin_paid (paid/self_reported) / end_paid spoken_message | spoken_message="Thank you for letting me know. The bank will check for the payment within two business days and will not call you again before then. |
| R48 | implemented | topic dispute -> pol_dispute -> fin_contested_xfer (transfer_to_agent#3 queue general) -> fin_contested (transferred/contested) | on_enter tts: "I understand. A colleague will look into it. I will connect you now." |
| R49 | implemented | plan_offer on_enter tts + task_message; transitions plan_choice accept -> xfer_plan (queue restructuring) -> fin_plan_review; decline -> fin_declined_offer | on_enter tts: "The plan review team handles these requests. May I connect you with them now?" |
| R50 | implemented | setup/opening_retry wants_agent -> xfer_general; ask_phone/ask_dob refusal human -> xfer_general; pol_human (human_limit=1) and wrap_human -> xfer_general; plan_offer plan_human -> xfer_general; fin_agent_request | 6. -> xfer_general  if (who1 equals "wants_agent")  ["asks for a person (R43)"] |
| R51 | implemented | SYSTEM PROMPT scam line; ask_phone/ask_dob/opening_retry/negotiate task_message; aside extraction | - If asked whether this is a scam: say "You may hang up and call the number on the back of your card or on your latest statement to confirm this call.", then co |
| R52 | implemented | SYSTEM PROMPT; negotiate/confirm/hardship/wrapup task_message COMMON | - Never invent a figure, a date or a reason. If you do not have the information, say so and that the payments team can answer it. |
| R53 | implemented | setup refuses -> fin_withheld; ask_phone/ask_dob end_call -> fin_withheld; negotiate/confirm topic no_talk -> pol_notalk (notalk_limit=1) -> fin_declined_offer | 5. -> fin_withheld  if (refusal_phone equals "end_call")  ["wants to end the call (R46)"] |
| R54 | implemented | tool close_call (alwaysRunsAt end_of_call) reading outcome/reason set by fin_* code nodes, setup default and prepare default | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R55 | implemented | every fin_* code node: recorded_pids check sets outcome promise with promise_reason (full/partial from promise_reason()) | if True and rec and rec.lower() not in ('none', 'null'):             vars['outcome'] = 'promise' |
| R56 | implemented | POLICY notes=False; no add_note tool defined in workflow | multi=False, notes=False,                     # R1 one product; R47 Brief C never calls add_note |
| R57 | implemented | all end_* terminal spoken_message (e.g. end_promise) | spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye from Nordvik Savings Bank." |
| R58 | implemented | all tool definitions (POST, body.customer_id default {{customer_id}}); retries: get_account maxRetries 2, transfer maxRetries 1, create_promise fail_max=3 loop, schedule_callback post retry line | url: POST https://freya-bank-mock.freyavoice.workers.dev/v1/get_account     body.customer_id (string): default "{{customer_id}}" |
| R59 | implemented | ask_dob all_verified -> load_account (get_account, mapping data.products); prepare code reads type, card_last4, past_due, days_late, instalment_amount | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True") |
| R60 | implemented | tools verify_identity / verify_identity#2 (baked field, answer descriptions, pre_process normaliser, post_process id_wrong >= 2 -> exhausted, ok false not counted) | msg = 'The answer could not be read. It does not count as wrong. Ask again: What are the last four digits of the mobile number registered with the bank?' |
| R61 | implemented | tool create_promise body + pre_process_code; rec_next code (one record per agreed product) | want = [('product_id', str(vars.get('rec_pid') or '')), ('amount', str(vars.get('rec_amount') or '')), ('date', str(vars.get('rec_date') or '')[:10])] |
| R62 | implemented | tool schedule_callback body fields + pre_process_code (time normalised to HH:MM) | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, from 09:00 to 18:00 inclusive, later than now. |
| R63 | implemented | tools transfer_to_agent / #2 / #3 baked queue defaults (xfer_plan, xfer_support, xfer_general, fin_contested_xfer) | body.queue (string): default "restructuring" |
| R64 | implemented | global tool close_call (alwaysRunsAt end_of_call) outcome enum; fin_* code nodes set outcome/reason | body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"] |
