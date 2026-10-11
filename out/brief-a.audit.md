# Coverage audit: brief-a.workflow.json

Rules: `brief-a.rules.json`. Generator: `gen_brief-a.py`. Model claude-fable-5-1, 65 s, $6.99, 6 call(s).

| implemented | partial | missing | contradicted | superseded | total |
|---|---|---|---|---|---|
| 61 | 0 | 0 | 0 | 0 | 61 |

1 evidence quote(s) were not found verbatim in the digest or the generator (marked *unverified* below).

## All rules

| id | status | where | evidence |
|---|---|---|---|
| R01 | implemented | opening -> ask_dob/ask_phone -> load_account -> prepare statement -> negotiate -> fin_* / end_* terminals | statement = ('Thank you, ' + str(vars.get('title') or '') + ' ' + str(vars.get('last_name') or '') + '. I am calling from the collections team about a late paym |
| R02 | implemented | tool definitions body.customer_id default; setup code reads vars['now']; opening tts uses title/last_name; WHO_DESC uses first_name | body.customer_id (string): default "{{customer_id}}" |
| R03 | implemented | system prompt | Address the customer as {{title}} {{last_name}}. |
| R04 | implemented | setup code: today from vars['now']; policy resolve_when uses today_of(V) | raw = str(vars.get('now') or '').strip() |
| R05 | implemented | opening on_enter tts | on_enter tts: "Hello, this is a digital assistant calling from Freya Bank, and we record this call. Am I speaking with {{title}} {{last_name}}?" |
| R06 | implemented | opening_retry task_message, third_party task_message STRICT line, ask_dob/ask_phone ID_COMMON rule 1 | - Do not mention the reason for the call, collections, a debt, a payment, a product or an amount. If asked what the call is about or how much they owe, say you  |
| R07 | implemented | opening on_enter tts; opening_retry task_message 'Then ask exactly' | Then ask exactly: "Am I speaking with {{title}} {{last_name}}?" |
| R08 | implemented | who1/who2 extraction description; setup transition 5 -> opening_retry; opening_retry transition 6 -> fin_unclear | 6. -> fin_unclear  if always  ["always"] |
| R09 | implemented | opening_retry task_message | If the person asked a question, answer it briefly first: who you are -> you are Freya Bank's digital assistant; a robot or AI -> 'Yes, I am Freya Bank's digital |
| R10 | implemented | system prompt Always bullet 1; opening_retry, negotiate COMMON, asides['robot'] | - If asked whether you are a robot or an AI: say "Yes, I am Freya Bank's digital assistant.", then continue. |
| R11 | implemented | third_party task_message STRICT line and 'Your only job' line | Your only job: ask when {{title}} {{last_name}} can be reached, then book a callback. |
| R12 | implemented | setup code callback_text (today after now up to 19:00, next business day 10:00-19:00 included); third_party tool schedule_callback; transition 1 -> fin_callback (not_reached/callback) | lines.append(txt(nbd) + ' (' + nbd.isoformat() + '), from 10:00 up to 19:00 included.') |
| R13 | implemented | third_party.task_message + transition -> fin_no_callback (not_reached / no_callback) | - If the second answer is also outside the window, or they cannot say when, do not book: call transition_to_fin_no_callback. |
| R14 | implemented | third_party transition 3 -> fin_wrong_number (also opening/opening_retry who=wrong_number); fin_wrong_number sets not_reached/wrong_number | 3. -> fin_wrong_number  if (tp_status equals "wrong_number")  ["wrong number"] |
| R15 | implemented | third_party / opening / opening_retry transitions -> fin_deceased; end_deceased terminal spoken_message | terminal: endedReason=not_reached_deceased, spoken_message="I am sorry for your loss. Thank you, goodbye." |
| R16 | implemented | third_party.task_message STRICT line | STRICT: Never say why you are calling. Never mention the bank account, a product, a debt, an amount, a payment or collections, even if they ask or offer to pay  |
| R17 | implemented | ask_dob.task_message + verify_identity baked field date_of_birth; ask_phone + verify_identity#2 baked field phone_last4 | When they give it, call verify_identity with answer = the date as YYYY-MM-DD, whatever way they said it. A date said only as numbers is day, then month, then ye |
| R18 | implemented | ask_dob / ask_phone transitions on wrong_answers_left == 0 -> fin_failed; verify_identity post_process_code 'Wrong answer ... ask again' | 1. -> fin_failed  if (verify_identity_response.data.wrong_answers_left equals "0")  ["three wrong answers"] |
| R19 | implemented | tool verify_identity post_process_code hint branch | d['what_to_do_next'] = 'Day and month look swapped. This is NOT a wrong answer. Ask the customer to say the date of birth again with the month as a word, for ex |
| R20 | implemented | fin_failed code (not_verified/failed) + end_failed terminal spoken_message; verify_identity post 'Say nothing about the account.' | spoken_message="I am sorry, I could not verify your identity, so I cannot continue. Please use the Freya Bank mobile app or visit a branch. Thank you, goodbye." |
| R21 | implemented | ask_dob/ask_phone ID_COMMON + refusal extraction (what-is-it-about counts as refused) + count_decline_* code (decline_count >= 2 -> fin_declined) | vars['decline_route'] = 'close' if n >= 2 else 'retry' |
| R22 | implemented | ask_phone transition 1 -> load_account; load_account pre_action tool get_account | 1. -> load_account  if (verify_identity_response.data.all_verified equals "true" OR verify_identity_response.data.all_verified equals "True")  ["identity verifi |
| R23 | implemented | prepare code: statement + words ('credit card ending <last4>' / ptype with underscores replaced); spoken by negotiate on_enter tts {{say_next}} | '. I am calling from the collections team about a late payment on your ' + words + '. The past-due amount is ' + fmt(past_due) + ', and it is ' + str(days_late) |
| R24 | implemented | setup code (and prepare/check_offer code): HOL set + BWD weekdays 0-4, isbd() | HOL = set(['2026-10-26', '2026-11-11', '2026-11-26', '2026-12-25', '2027-01-01']) |
| R25 | implemented | setup code: early_deadline/late_deadline; prepare code: days_late <= 7 band and rungs | vars['early_deadline'] = addbd(today, 12).isoformat() |
| R26 | implemented | check_offer code: check_one (before_today / after_deadline / weekend_or_holiday issues) | if nd < t: |
| R27 | implemented | check_offer code: check_one, elif not isbd(nd) branch (after the nd > dl branch) | "weekend_or_holiday": "[named] is not a business day, so I cannot record it. The next business day is [date]." |
| R28 | implemented | check_offer code: check_one vague branch (vague_asked once, then vague_deadline + offer_question) | set_prop(V, pid, pa, dl) |
| R29 | implemented | check_offer code: resolve_when weekday branch; negotiate extract offer_date description | delta = (7 - today.weekday()) + wd |
| R30 | implemented | check_offer code: check_one after_deadline issue -> set_prop(na, dl) and offer; refuse of it goes to refuse() ladder | "after_deadline": "The latest date I can record is [deadline]." |
| R31 | implemented | tools verify_identity / verify_identity#2 (baked field, answer description) and post_process_code ok=false branch | d['what_to_do_next'] = 'The answer could not be read. It does not count as wrong. Ask again: What are the last four digits of the phone number on file?' |
| R32 | implemented | tool schedule_callback body fields customer_id, date, time | body.time* (string): default "{{time}}"; Callback time as HH:MM, 24 hour, between 10:00 and 19:00. |
| R33 | implemented | prepare code: statement (full past_due asked first); negotiate.task_message | - Never propose, compute or change an amount or a date yourself, and never ask how much they can pay. The only offer you may make is the current offer in STATE, |
| R34 | implemented | prepare code: floor selection by ptype | floor = p.get('minimum_payment') |
| R35 | implemented | too_much code: too_much() offers floor once with too_much_floor text; refuse() ladder; prepare rungs [('full_or_floor', a1), ('floor', deadline)] | "too_much_floor": "I understand. The lowest amount I can accept is [floor], your [floor_name]. The rest stays overdue." |
| R36 | implemented | check_offer code: check_one below_floor / above_full branches, agree() when no issues | if pg(V, pid, 'offered_floor') == 'yes' and g(V, 'mode') != 'hardship': |
| R37 | implemented | prepare code: statement (spoken by negotiate on_enter tts {{say_next}}) | + words + '. The past-due amount is ' + fmt(past_due) + ', and it is ' + str(days_late) + ' days late. Can you make this payment today?') |
| R38 | implemented | negotiate extraction stance + transition 7 -> check_offer (before count_refusal); check_one guard | offer = names their own date, amount or period: a date or an amount the customer proposes is NEVER a refusal. |
| R39 | implemented | setup code: attempt1_date; prepare code: rungs; policy rung()/refuse() | rungs = [('full_or_floor', a1), ('floor', deadline)] |
| R40 | implemented | policy refuse(): refused_offers skip, state refused -> finalize -> fin_refused; state_line 'never offer them again' | if k >= len(L):                 pset(V, pid, 'state', 'refused') |
| R41 | implemented | negotiate transition 1 -> pol_hardship; hardship node (tts 'hardship' text, task_message); xfer_support (queue support) -> fin_transferred_support; hs_decline -> fin_hardship; hardship transition 2 -> check_offer | "hardship": "I am sorry to hear that. Would you like me to connect you with our customer support team?",      # R32 |
| R42 | implemented | system prompt + COMMON in negotiate/confirm/hardship/wrapup task_message | - Never offer a discount, waiver, payment plan or any term you were not given. |
| R43 | implemented | policy readback() (confirm on_enter tts {{readback_line}}); confirm transition 2 (confirm equals yes) -> rec_next -> record_promise | "readback_item": "[words], [amount], [when]", ... "readback_tail": ". Do you confirm?" *unverified* |
| R44 | implemented | confirm transition 1 -> change_offer; policy ev_change() -> check_one() -> agree() -> advance() -> readback -> confirm | 1. -> change_offer  if (confirm equals "change")  ["the customer changes the date or the amount"] |
| R45 | implemented | policy recorded_guard()/ev_wrap_change() wrap_change text; wrapup task_message | "wrap_change": "A recorded promise cannot be changed or cancelled on this call, but you can change it in the Freya Bank mobile app.",  # R36 |
| R46 | implemented | record_promise -> rec_after: ev_rec_after (fail_max=2 retry, state service_error) -> finalize -> fin_service_error; enter_wrapup says 'recorded' only when state recorded; end_service_error terminal | if f < int(P['fail_max']):                         V['rec_ok'] = 'pending'                         V['route'] = 'record' |
| R47 | implemented | policy enter_wrapup(): after_recorded appended to wrap_line (wrapup on_enter tts) | "after_recorded": "You will receive a text message confirming this promise.",                                 # R38 |
| R48 | implemented | negotiate extraction topic already_paid -> pol_paid -> ev_settle('paid') -> finalize -> fin_paid; end_paid terminal spoken_message | spoken_message="Thank you for letting me know. Payments can take one business day to appear, so I will not take a promise today. Thank you for your time, {{titl |
| R49 | implemented | negotiate transition 6 -> pol_dispute; policy ev_settle('dispute') -> finalize -> fin_dispute; end_dispute terminal | 6. -> pol_dispute  if (topic equals "dispute")  ["topic dispute"] |
| R50 | implemented | negotiate/confirm/wrapup transitions -> xfer_restructuring (transfer_to_agent#2 queue restructuring) -> fin_transferred_restructuring | on_enter tts: "I cannot set up a new plan myself, but I will transfer you to the team that can help with that." |
| R51 | implemented | ask_dob/ask_phone task_message (ID_COMMON) + transfer_to_agent queue general -> fin_transferred_human; negotiate -> pol_human (human_limit=2, human_first line) -> xfer_general -> fin_transferred_human | - If the customer asks for a human: the first time, ask whether you can help them yourself. If they insist, call transfer_to_agent. |
| R52 | implemented | system prompt; COMMON block in negotiate/confirm/hardship/wrapup; policy asides.scam | - If asked whether this is a scam: say they can verify this call by phoning Freya Bank's customer service number, then continue. |
| R53 | implemented | system prompt + COMMON block in negotiate/confirm/hardship/wrapup task_message | - A question these facts do not answer: say you do not have that information. |
| R54 | implemented | negotiate -> pol_notalk (notalk_limit=2 -> state refused -> fin_refused); ask_dob/ask_phone refusal_* 'do not want to talk' -> count_decline_* (n>=2) -> fin_declined; opening_retry who2 refuses -> fin_declined | refused if they refuse to answer the security question, say they do not want to talk, or ask what the call is about INSTEAD of answering |
| R55 | implemented | tool close_call (alwaysRunsAt end_of_call) reading outcome/reason set by the 16 fin_* code nodes | config: {"maxRetries": 0, "alwaysRunsAt": ["end_of_call"]} |
| R56 | implemented | FINS table -> fin_* code nodes (outcome/reason) + close_call pre_process_code drops reason for promise/paid | reason_desc="transferred: restructuring/human/support. no_promise: refused/hardship/dispute/service_error. not_verified: failed/declined. not_reached: callback/ |
| R57 | implemented | wrapup transitions -> wrap_human -> xfer_general -> fin_transferred_human / -> xfer_restructuring -> fin_transferred_restructuring (overwrite outcome='promise' set by enter_wrapup) | 2. -> wrap_human  if (wrap equals "human")  ["asks for a human"] |
| R58 | implemented | generator Policy(... notes=False); no add_note tool in TOOL DEFINITIONS | multi=False, notes=False,                                   # one product; Brief A never uses add_note |
| R59 | implemented | all end_* terminal spoken_message (every FINS farewell thanks and says goodbye; close_call runs after at end_of_call) | terminal: endedReason=promise, spoken_message="Thank you for your time, {{title}} {{last_name}}. Goodbye." |
| R60 | implemented | tool close_call pre_process_code + fin_* nodes setting non-empty reason for every outcome except promise/paid; lifecycle end_of_call so nothing follows | if b.get('outcome') in ('promise', 'paid') or not b.get('reason'): |
| R61 | implemented | tool create_promise body fields + pre_process_code (record_promise api_request node; rec_pid/rec_amount/rec_date set by rec_next in policy code) | body.amount (number): default "{{rec_amount}}" |
