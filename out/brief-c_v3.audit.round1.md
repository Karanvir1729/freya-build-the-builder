# Coverage audit: brief-c_v3.workflow.json

Rules: `brief-c.rules.json`. Generator: `gen_brief-c_v3.py`. Model claude-opus-5-5, 72 s, $2.54, 7 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 60 | 4 | 0 | 0 | 0 | 64 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## Top fixes

1. **R34** (partial): If the customer says the full amount is too much, propose the floor once and say the remainder stays overdue and the account stays in arrears until cleared. Declining the floor is a flat refusal (rule 31). The floor may be named a second time only as attempt 2 (rule 31).
   - why: After the customer says the full amount is too much and the floor is offered, rung 0 'full_or_floor' can name the floor again outside attempt 2, so the floor is named an extra time and declining it isn't treated as a flat refusal. Too-much cases fail.
   - fix: Policy code `prepare`: set the rung-0 ladder entry to 'full' (or, when pg(V,pid,'offered_floor')=='yes', use 'full' instead of 'full_or_floor'). In `too_much()`, set `offered_floor='yes'` when `too_much_floor` is spoken, and send a decline of that floor offer to the flat-refusal path (rule 31). Name the floor again only in the attempt-2 rung.
2. **R64** (partial): `close_call` is always the last tool call and nothing is accepted after it; `outcome` is one of the enum values; `reason` is required by the API for every outcome except `promise` and `paid` (the brief still assigns `full`/`partial` and `self_reported`).
   - why: If the customer hangs up before any fin_* node runs, `close_call` (end_of_call) sends an empty `{{outcome}}`/`{{reason}}`, which is an invalid enum value or a missing required reason, so the close_call check fails.
   - fix: Setup code node: add `vars['outcome']='not_verified'; vars['reason']='unconfirmed'` (or not_reached/unconfirmed, whichever the brief pairs for an early hang-up). In the post-verification `prepare` code, set `vars['outcome']='no_promise'; vars['reason']='declined_offer'`. The fin_* nodes then overwrite these defaults as they do now.
3. **R50** (partial): Request for a person: do not ask whether you can help first; call `transfer_to_agent` queue `general` and close `transferred` / `agent_request`. Applies before and after the security check.
   - why: A request for a person made during the hardship flow goes to the care team instead of calling `transfer_to_agent` (queue general) and closing transferred/agent_request.
   - fix: Hardship node: add the value 'human' to its extraction enum (description: 'customer asks for a person/agent/human'). Add a first-priority transition `-> xfer_general if <field> equals "human"`, ahead of the care-team route, so it reaches fin_agent_request (transferred/agent_request) without asking whether the agent can help first.
4. **R29** (partial): "This <weekday>" and "next <weekday>" both mean the first such weekday after today (said on a Wednesday, both "this Friday" and "next Friday" are the coming Friday).
   - why: 'This Friday' said on a Friday resolves to today instead of the following Friday, so the promise date is wrong.
   - fix: Policy code `resolve_when`, weekday branch: change `delta = (wd - today.weekday()) % 7` to `delta = (wd - today.weekday()) % 7 or 7` for both 'this' and 'next' (and a bare weekday) when weekday_rule == 'first_after'.

## partial (4)

- **R29** (_brief-c.md rule 22_): "This <weekday>" and "next <weekday>" both mean the first such weekday after today (said on a Wednesday, both "this Friday" and "next Friday" are the coming Friday).
  - where: policy code resolve_when weekday branch; offer_date extraction description
  - evidence: `delta = (wd - today.weekday()) % 7`
  - fix: In resolve_when, also use '% 7 or 7' for 'this'/bare weekday when weekday_rule == 'first_after'. Without it, 'this Friday' said on a Friday resolves to today, not the next Friday.
- **R34** (_brief-c.md rule 27_): If the customer says the full amount is too much, propose the floor once and say the remainder stays overdue and the account stays in arrears until cleared. Declining the floor is a flat refusal (rule 31). The floor may be named a second time only as attempt 2 (rule 31).
  - where: policy code too_much() + texts too_much_floor; ladder rung 'full_or_floor'
  - evidence: `elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes':`
  - fix: In prepare, change rung 0 from 'full_or_floor' to 'full' (or skip floor in rung 0 once offered_floor is yes). Then after the too-much floor offer, the floor is named again only as attempt 2.
- **R50** (_brief-c.md rule 43_): Request for a person: do not ask whether you can help first; call `transfer_to_agent` queue `general` and close `transferred` / `agent_request`. Applies before and after the security check.
  - where: setup/opening_retry who=wants_agent -> xfer_general; ask_phone/ask_dob refusal=human -> xfer_general; pol_human (human_limit 1) -> xfer_general -> fin_agent_request
  - evidence: `6. -> xfer_general  if (who1 equals "wants_agent")  ["asks for a person (R43)"]`
  - fix: Add a human value (or topic extraction) to the hardship node with a transition to xfer_general, so a request for a person during hardship closes transferred/agent_request instead of going to the care team.
- **R64** (_openapi.json /close_call_): `close_call` is always the last tool call and nothing is accepted after it; `outcome` is one of the enum values; `reason` is required by the API for every outcome except `promise` and `paid` (the brief still assigns `full`/`partial` and `self_reported`).
  - where: tool close_call (alwaysRunsAt end_of_call, outcome enum, pre_process_code drops empty reason); fin_* code nodes
  - evidence: `body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"]`
  - fix: In the setup code node, set default vars['outcome'] and vars['reason'] (e.g. not_reached/unconfirmed before verification, then no_promise/declined_offer after verification in prepare), so a call that ends by hang-up before any fin_* node still sends a valid enum outcome with a reason.

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | generator POLICY multi=False; prepare code (prods[0]); fin_* nodes with section-12 outcome/reason pairs; SYSTEM prompt | multi=False, notes=False,                     # R1 one product; R47 Brief C never calls add_note |
| R02 | implemented | every tool body customer_id default; opening tts {{first_name}} {{last_name}}; system prompt {{title}} {{last_name}}; setup code reads vars['now'] | raw = str(vars.get('now') or '').strip() |
| R03 | implemented | all tool definitions (transfer_to_agent, schedule_callback, verify_identity, get_account, create_promise, close_call) body.customer_id | body.customer_id (string): default "{{customer_id}}" |
| R04 | implemented | system prompt; prepare statement; post-check terminal spoken_messages | After the security check, address the customer as {{title}} {{last_name}}. |
| R05 | implemented | setup code (today from vars['now']); prepare resolve_when; schedule_callback pre_process_code NOW_VAR | # (date, kind) from the customer's OWN WORDS, relative to the call's today (never the real clock |
| R06 | implemented | opening on_enter tts (first_only) and task_message | on_enter tts: "Good day, this is the virtual assistant of Nordvik Savings Bank, and this call is recorded. Am I speaking with {{first_name}} {{last_name}}?" |
| R07 | implemented | system prompt; opening_retry.task_message; third_party.task_message; ask_phone/ask_dob ID_COMMON | Until the security check is complete, never use the words overdue, arrears, collections, payment or debt, and never name a product, to anyone. |
| R08 | implemented | opening on_enter tts; opening_retry.task_message | Then ask exactly: "Am I speaking with {{first_name}} {{last_name}}?" This is the second and last time you ask. |
| R09 | implemented | opening extraction who1; setup transitions -> opening_retry; opening_retry transition 7 -> fin_unconfirmed (not_reached/unconfirmed) | customer = ONLY 'yes', 'speaking', 'that's me', or they say the customer's own name ({{first_name}} {{last_name}}). |
| R10 | implemented | system prompt; opening_retry, third_party, ask_phone/ask_dob, negotiate/confirm/hardship/wrapup task_messages; aside 'robot' | If asked whether you are a robot, an AI or a machine: say exactly "I am an automated assistant of Nordvik Savings Bank, and this conversation is recorded." and  |
| R11 | implemented | third_party.task_message STRICT block | If they ask what it is about, offer to pay, or offer to take a message, repeat that you can discuss it only with the customer. |
| R12 | implemented | setup code callback_text; third_party.task_message; schedule_callback tool; third_party transition 1 -> fin_scheduled (not_reached/scheduled) | - If they give a day and time inside the window, call schedule_callback with date YYYY-MM-DD (from the list above) and time HH:MM. |
| R13 | implemented | third_party.task_message window bullets; transition_to_fin_no_slot -> fin_no_slot (not_reached/no_slot) | - If the second slot is also outside the window, or they cannot say when, book nothing: call transition_to_fin_no_slot. |
| R14 | implemented | third_party transition tp_status=wrong_number -> fin_wrong_party; end_wrong_party terminal | terminal: endedReason=not_reached_wrong_party, spoken_message="I apologise for the disturbance. Thank you for your time. Goodbye from Nordvik Savings Bank." |
| R15 | implemented | third_party/setup transitions deceased -> fin_estate; end_estate terminal spoken_message | terminal: endedReason=not_reached_estate, spoken_message="Please accept my condolences. Thank you for your time. Goodbye from Nordvik Savings Bank." |
| R16 | implemented | third_party.task_message STRICT block | If they ask what it is about, offer to pay, or offer to take a message, repeat that you can discuss it only with the customer. Never ask them a security questio |
| R17 | implemented | ask_phone (verify_identity field phone_last4) -> ask_dob (verify_identity#2 field date_of_birth) on verified=true | When they give four digits, call verify_identity with answer = the four digits only. Do not ask the date of birth before this question has passed. |
| R18 | implemented | ask_dob.task_message; verify_identity#2 post_process_code ok=false branch | Call verify_identity with the date as YYYY-MM-DD. If the customer gives the date ONLY in numbers (for example 3/7/85), do not call the tool: ask them to say the |
| R19 | implemented | verify_identity post_process_code (shared id_wrong counter, done = nw >= 2) + ask_phone/ask_dob transition id_route=exhausted -> fin_exhausted | done = nw >= 2 or str(left) == '0' |
| R20 | implemented | verify_identity post_process_code hint_day_month_swapped counter | msg = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to repeat the date of birth with the month said as a word, for example 14 March  |
| R21 | implemented | verify_identity post_process_code LIMIT message; fin_exhausted (not_verified/exhausted); end_exhausted terminal | A colleague can complete the check if you call the number on the back of your card or on your latest statement. |
| R22 | implemented | ask_phone/ask_dob task_message + refusal_* extraction -> count_decline_* (decline_count >= 2 -> fin_withheld) | - If the customer refuses to answer, or asks what the call is about instead of answering: say that the bank cannot discuss anything until the security check is  |
| R23 | implemented | ask_dob transition all_verified -> load_account (get_account); system prompt address rule | After the security check, address the customer as {{title}} {{last_name}}. |
| R24 | implemented | prepare code: statement / words; system prompt forbids collections | I am calling from the payments team of Nordvik Savings Bank about an overdue amount on your ' + words + '. The overdue amount is ' + fmt(past_due) + ', and it i |
| R25 | implemented | setup code: HOL, BWD, isbd (same in prepare/policy code) | HOL = set(['2026-10-16', '2026-11-02', '2026-11-21', '2026-12-08', '2026-12-24', '2026-12-25', '2026-12-26', '2026-12-31']) |
| R26 | implemented | prepare code: deadline/rungs by days_late | if days_late <= 10:                        # R19 green: the 9th business day after today, 2 attempts |
| R27 | implemented | policy code check_one: before_today / after_deadline / not isbd checks | elif nd > dl: |
| R28 | implemented | policy texts weekend_or_holiday + check_one closed_day_move 'after'; BWD includes Saturday | "weekend_or_holiday": "[named] is not a business day. The next business day is [date]." |
| R29 | partial | policy code resolve_when weekday branch; offer_date extraction description | delta = (wd - today.weekday()) % 7 |
| R30 | implemented | policy code check_one vague branch (vague_again='refuse') | if P.get('vague_again') == 'refuse':   # the brief: no exact day after one ask = a non-answer (one attempt) |
| R31 | implemented | policy code check_one after_deadline issue + texts after_deadline; refusal via refuse() | "after_deadline": "The latest date the bank can record is [deadline]." |
| R32 | implemented | prepare statement + init_negotiation prop_of full; negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask what they can pay or how much they can afford. |
| R33 | implemented | prepare code: floor per product type | floor = float(math.ceil(round(past_due * 0.4, 2) - 1e-9))   # R26: 40%, rounded up to the next whole unit |
| R34 | partial | policy code too_much() + texts too_much_floor; ladder rung 'full_or_floor' | elif rule == 'full_or_floor' and pg(V, pid, 'too_much') == 'yes': |
| R35 | implemented | policy code check_one below_floor/above_full + above_full='agree' | agree(V, pid, na, nd, prefix=issues[0][1])   # the brief: above the full amount, record the full amount and say so |
| R36 | implemented | prepare statement -> say_next -> negotiate on_enter tts | days overdue. Are you able to settle the full overdue amount today?')   # R18, R29 |
| R37 | implemented | negotiate extraction stance + transition 7 -> check_offer (before count_refusal) | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R38 | implemented | prepare code: rungs (green 2 attempts, amber 1); stance 'refuse' -> count_refusal -> refuse() | rungs = [('full_or_floor', a1), ('floor', deadline)]   # R31 attempt 2 (green only): the floor on the deadline |
| R39 | implemented | policy refuse(): refused_list + state refused -> finalize fin_keys refused=declined_offer -> fin_declined_offer | vars['outcome'] = 'no_promise'             vars['reason'] = 'declined_offer' |
| R40 | implemented | negotiate transition 1 -> pol_hardship (texts.hardship); hardship node -> xfer_support (queue support) -> fin_care_team; hs_decline -> fin_financial_distress | "hardship": "I am sorry to hear that. I will not ask you for a payment today. The bank's care team can review your situation. May I connect you with them now?" |
| R41 | implemented | negotiate/confirm/hardship/wrapup task_message COMMON; check_one clamps dates after the deadline | - Never offer or agree to a discount, a waiver, a fee reversal, an instalment plan or any date later than the latest date. If asked for one, say "I cannot offer |
| R42 | implemented | policy readback() -> confirm on_enter tts {{readback_line}}; confirm yes -> rec_next -> record_promise | "readback_item": "[amount] [when] for your [words]", ... "readback_tail": ". Shall I record this?" *unverified* |
| R43 | implemented | confirm transition 1 -> change_offer (ev_change -> check_one -> advance -> confirm) | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R44 | implemented | multi=False single product; wrapup wrap=change -> wrap_change (texts.wrap_change) | "wrap_change": "A recorded promise is not changed or cancelled during this call. The payments line can change it." |
| R45 | implemented | record_promise rec_ok mapping; ev_rec_after with fail_max 3; finalize service_error -> fin_system_fault | if f < int(P['fail_max']):                         V['rec_ok'] = 'pending'                         V['route'] = 'record' |
| R46 | implemented | enter_wrapup -> wrapup on_enter tts {{wrap_line}} (texts.recorded) | "recorded": "I have noted your promise. A confirmation will be sent to your registered email address." |
| R47 | implemented | topic already_paid -> pol_paid -> fin_paid -> end_paid spoken_message | terminal: endedReason=paid_self_reported, spoken_message="Thank you for letting me know. The bank will check for the payment within two business days and will n |
| R48 | implemented | topic dispute -> pol_dispute -> fin_contested_xfer (transfer_to_agent#3 queue general) -> fin_contested | on_enter tts: "I understand. A colleague will look into it. I will connect you now." |
| R49 | implemented | plan_offer on_enter tts + transitions -> xfer_plan (transfer_to_agent queue restructuring) -> fin_plan_review; decline -> fin_declined_offer | on_enter tts: "The plan review team handles these requests. May I connect you with them now?" |
| R50 | partial | setup/opening_retry who=wants_agent -> xfer_general; ask_phone/ask_dob refusal=human -> xfer_general; pol_human (human_limit 1) -> xfer_general -> fin_agent_request | 6. -> xfer_general  if (who1 equals "wants_agent")  ["asks for a person (R43)"] |
| R51 | implemented | system prompt 'If asked whether this is a scam' + ask_phone/ask_dob/negotiate task_message | - If asked whether this is a scam: say "You may hang up and call the number on the back of your card or on your latest statement to confirm this call.", then co |
| R52 | implemented | system prompt + negotiate/confirm/hardship/wrapup task_message COMMON | - A question these facts do not answer: say you do not have that information and that the payments team can answer it. Never invent a figure, a date or a reason |
| R53 | implemented | setup who1=refuses -> fin_withheld; ask_phone/ask_dob end_call -> fin_withheld; negotiate topic no_talk -> pol_notalk (notalk_limit 1) -> fin_declined_offer | 5. -> fin_withheld  if (refusal_phone equals "end_call")  ["wants to end the call (R46)"] |
| R54 | implemented | tool close_call (alwaysRunsAt end_of_call) with outcome/reason written by fin_* code nodes | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R55 | implemented | every fin_* code node: recorded_pids set -> outcome promise, reason promise_reason (full/partial from enter_wrapup) | if True and rec and rec.lower() not in ('none', 'null'):             vars['outcome'] = 'promise' |
| R56 | implemented | Policy notes=False; no add_note tool in TOOL DEFINITIONS | multi=False, notes=False,                     # R1 one product; R47 Brief C never calls add_note |
| R57 | implemented | all end_* terminal spoken_message | spoken_message="I understand. Thank you for your time, {{title}} {{last_name}}. Goodbye from Nordvik Savings Bank." |
| R58 | implemented | all tool definitions (POST, body.customer_id default {{customer_id}}); get_account maxRetries 2, transfer maxRetries 1, create_promise retried via fail_max 3 | url: POST https://freya-bank-mock.freyavoice.workers.dev/v1/get_account     body.customer_id (string): default "{{customer_id}}" |
| R59 | implemented | ask_dob transition all_verified -> load_account (get_account); prepare code reads product_id/type/card_last4/past_due/days_late/instalment_amount | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True") |
| R60 | implemented | tools verify_identity / verify_identity#2: baked field, answer descriptions, post_process_code (ok=false not counted, nw >= 2 ends) | msg = 'The answer could not be read. It does not count as wrong. Ask again: What is your date of birth?' |
| R61 | implemented | tool create_promise body defaults + pre_process_code; record_promise node; policy rec_next | want = [('product_id', str(vars.get('rec_pid') or '')), ('amount', str(vars.get('rec_amount') or '')), ('date', str(vars.get('rec_date') or '')[:10])] |
| R62 | implemented | tool schedule_callback body fields + pre_process_code (to_time) | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, from 09:00 to 18:00 inclusive, later than now. |
| R63 | implemented | tools transfer_to_agent / #2 / #3 baked queue (xfer_plan, xfer_support, xfer_general, fin_contested_xfer) | body.queue (string): default "restructuring" |
| R64 | partial | tool close_call (alwaysRunsAt end_of_call, outcome enum, pre_process_code drops empty reason); fin_* code nodes | body.outcome* (string): default "{{outcome}}"; enum ["promise", "paid", "transferred", "no_promise", "not_verified", "not_reached"] |
