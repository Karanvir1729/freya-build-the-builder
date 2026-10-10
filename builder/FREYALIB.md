# freyalib — a brief-agnostic library for Freya phone-agent workflows

`builder/freyalib.py` (standard library, Python 3.10+) holds everything **platform-specific** about a Freya
workflow: tool JSON shapes, node shapes, transition forms, hooks, the lifecycle `close_call` tool, the code-node
templates and the final checks. Everything **bank-specific** — holidays, bands, floors, wording, outcome table,
identity fields, prompts — is a parameter the generator for one brief passes in. The shapes are those of the
organisers' proven generator (`out/gen_brief-a.py`, 10/10 practice cases). `out/gen_brief-a_lib.py` is that
generator ported onto the library; `out/compare_brief-a_lib.py` proves the two outputs equivalent.

## API

| Area | Function | What it gives |
|---|---|---|
| OpenAPI | `load_api(path)` | the tool API file as a dict |
| | `base_url(api)` | server URL; tool `name` is `POST <base_url>/<name>` |
| | `tool_spec(api, name)` | `{"fields": {f: {type, description, enum, required}}, "required": [...], "summary", "response_props": {...}}` from `paths["/<name>"]["post"]` |
| | `tool_names(api)` | every tool in the file |
| Tools | `api_tool(api, name, baked=None, description="", required=None, retries=0, pre=None, post=None, mapping=None, field_descriptions=None, omit=None, var_map=None)` | the `api_call` tool. url/method/headers baked; `body.properties` = every spec field as a leaf; `customer_id` baked from `{{customer_id}}`; `baked` fields get a literal default (hidden from the model, checked against the enum; `"{{var}}"` bakes from a variable an earlier node always sets); all other fields are model-filled with `default: "{{<field>}}"` and the spec's type/description/enum (`field_descriptions` overrides). **A model-filled field must not share its name with an existing variable.** `required` = spec required − customer_id − baked. `post` defaults to `STRIP_HEADER` |
| | `close_call_tool(api, outcome_desc, reason_desc, no_reason_outcomes=None)` | the workflow-level `end_of_call` lifecycle tool reading `{{outcome}}`/`{{reason}}`; enum from the spec; pre-hook drops an empty reason (and the reason of `no_reason_outcomes`) |
| Nodes | `conv(name, task, on_enter=None, tools=None, extraction=None, transitions=None, first_only=False, max_turns=60)` | conversation node |
| | `code_node(name, code, transitions)` | passthrough code node (`code_exec`, 10 s); `ValueError` naming the node when `transitions` is empty |
| | `api_node(name, tool, transitions, mapping=None, on_enter=None)` | passthrough `api_request` node with node-level `response_mapping`; `ValueError` when `transitions` is empty |
| | `end_node(name, ended_reason, farewell)` | `end_call` node: silent entry, farewell in the terminal |
| | `end_pair(key, outcome, reason, farewell, nodes)` | adds `fin_<key>` (code: sets `outcome`/`reason`) + `end_<key>` (terminal named `<outcome>_<reason>`) |
| | `conversation_first(opening, setup_code, route_var, routes, default_target, nodes, setup_name="setup")` | the initial-node pattern (see "Initial node"): `opening` → always → passthrough `setup` code node routing on `route_var`; returns the initial node name |
| Transitions | `always(t)`, `eq(var, val, t, desc)`, `neq`, `is_set`, `is_true(var, t, desc)` ("true" and "True"), `count_gt(var, n, t, desc)`, `intent(t, desc, intent)`, `intent_tool(t, desc, intent)` (tool-call transition `transition_to_<t>`), `ok_true(tool, t, desc)`, `transferred(t, desc)`, `tool_failed_twice(tool, t, desc)` | ready-made transitions |
| | `cond(var, op, operand)`, `and_group(*conds)`, `tr(target, desc, *conds)`, `not_true(var)` | build any OR-of-ANDs condition |
| | `ext(name, values, desc, conf=0.6)` | an enum extraction entry |
| Hooks | `STRIP_HEADER` | drop the response headers |
| | `what_next_post(branches, else_text, prelude=None)` | strips headers and sets `result['data']['what_to_do_next']` from ordered `(python_condition_on_d, text)` pairs; with no branches, no else and no prelude it is `STRIP_HEADER` |
| | `ok_post(ok_text, fail_text)`, `promise_post()`, `promise_pre()` | write-tool hooks: say "recorded" only on `ok` true, retry once; amount→float, date→`[:10]` |
| | `verify_post(question, hints, max_wrong_text, ...)` | identity-question hook: hint (not a wrong answer) → all verified → verified → unreadable → counter at 0 → wrong. The default texts are generic: pass the brief's own wording (`all_verified_text=...` etc.) |
| | `truthy(field)`, `falsy(field)` | condition expressions on `d` that accept booleans and strings |
| Code | `CAL_HELPERS(holidays, business_weekdays)` | source defining `isbd, txt, txt_short, addbd, next_bd, lastbd_of_week, weekday_table, calendar_text, fmt` |
| | `SETUP_CODE(holidays, business_weekdays, callback_rule, extra="", fallbacks=None)` | first code node: parses `now`, always sets `today_iso, today_text, now_time, weekday_table, setup_state` (+ `callback_text` from `{"open","close","same_day","days_ahead"}`); `extra` is brief-specific source run inside the try |
| | `products_from_vars()` | reads the mapped product list (list / JSON string / flattened keys) |
| | `guarded(body, state_var, fallbacks)` | try/except wrapper with `vars.setdefault` fallbacks |
| | `counter_code(counter, limit, route_var, reset)` | count-and-route snippet (e.g. second refusal closes) |
| Assembly | `assemble(initial_node, nodes, system_prompt, tools, test_variables)` | the workflow dict, after `check()` |
| | `check(wf)` | raises `ValueError` listing: nulls, unknown targets, passthrough without `always`, tools/pre_actions on the wrong node type, code or hook that does not compile or has `{{`/`}}`, end_call without terminal, a node from which no end_call is reachable; global nodes without a condition, with an unknown target (`__previous__` allowed) or passthrough without a final `always`. Returns warnings (unreachable nodes, model-filled field named like a known variable) |
| | `write_workflow(wf, path)` | JSON with indent 1 |

Rules the helpers encode: fixed values use `default`, never `const`; booleans from results are tested as both
spellings; routing flags written by code are strings; code never raises and reads everything from `vars`; every
passthrough node ends with `always`; the farewell comes from the terminal and `endedReason` is its function name;
`close_call` runs once per call as a lifecycle tool, from the `outcome`/`reason` the `fin_*` node wrote.

## Speech normalisation (T21, T8)

Customers say numbers in parts ("463..." then "51"), correct themselves and say dates, amounts and times in words;
the model often passes the words through. These helpers fix that in code, before the request:

| Function | What it gives |
|---|---|
| `normalise_pre(fields, date_order='dmy', now_var='now', relative_var=None, pm_hours=(1..7))` | `pre_process_code` that rewrites the listed `config['body']` fields. `fields` = `{field: kind}` or a list (kind guessed from the name). Kinds: `digits` ("forty-four seventy-one", "double four", "oh" → `4471`), `dob` / `date` (month names, ordinals, spoken years, `14/03/88` in `date_order`, swapped only when the other order is impossible; two-digit years by a century rule against `now`; a year-less `date` takes the next occurrence), `amount` ("four hundred and twenty point five" → 420.5, "twelve fifty" → 1250.0, "1,250.00" → 1250.0), `time` ("half past two" → `14:30`, "11am" → `11:00`), `answer` (dob when the body's `field` names a date/birth, else digits). The last value after "no / sorry / I mean / actually" wins. Idempotent, never raises, leaves the value as is on any doubt. Concatenate with another pre hook (`promise_pre()`) if needed |
| `relative_days_code(now_var, out_var, next_means_week_after=False)` | code-node snippet writing a phrase → ISO table ("tomorrow", "this/next friday"); pass `relative_var=out_var` to resolve relative days. Without it they are left alone (the extractor's own date rules apply) |
| `latest_value_note(n_digits)` | prompt sentence: wait for all N digits given in parts and join them; after a correction use the LAST value |
| `digit_extraction(name, n_digits, description)` | extraction entry with `validation_pattern '^[0-9]{N}$'`, `max_retries 2`, `min_confidence 0.6` |

`date_order` and the relative-day reading come from the brief, never from Brief A/B. Tests:
`python3 builder/tests/test_normalise.py` (table of utterances executed as the platform runs a pre hook).

## Initial node

**The chat route (`POST /api/v2/chat/message`, used by `builder/smoke.py` and `builder/sim.py`) skips a first
code node**, confirmed on the Brief A agent; simulations run it. A workflow whose `initial_node` is a code node
therefore behaves differently in our smoke tests than in the scored simulations. Start every workflow with a
conversation node and run the setup code right after the customer's first turn:

```python
nodes["opening"] = fl.conv("opening", "You have just introduced yourself ... Do not call any tool.",
                           on_enter={"type": "tts", "text": "Hello, this is ... Am I speaking with {{title}} {{last_name}}?"},
                           extraction=[fl.ext("who1", WHO_VALUES, WHO_DESC)], first_only=True)
initial = fl.conversation_first("opening", SETUP, "who1",
                                [("customer", "ask_dob", "the customer confirmed who they are"),
                                 ("deceased", "fin_deceased", "the customer has died"),
                                 ("wrong_number", "fin_wrong_number", "wrong number"),
                                 ("someone_else", "third_party", "someone else answered")],
                                "opening_retry", nodes)
wf = fl.assemble(initial, nodes, SYSTEM, [close_call], TEST_VARS)
```

`opening` gets a single `always` transition to `setup`; `setup` is a passthrough code node that computes the
date facts and routes on the extracted variable, everything unmatched going to the default target. The opening
line and prompt may use only call variables (`test_variables`: names, `now`), never a value `setup` computes.
`out/gen_brief-a_v2.py` is the Brief A reference generator in this shape; `out/compare_brief-a_v2.py` shows it
differs from `out/brief-a.lib.workflow.json` only in `initial_node` and the `opening`/`setup` transitions.

## Reference architecture (gen_brief-a.py, 46 nodes)

```
setup (code: dates, callback window, attempt/deadline dates)
  └─> opening (tts greeting; extract who1)
        ├─ customer     ─> ask_<q1> (verify_identity field=q1; transfer_to_agent)
        ├─ someone_else ─> third_party (schedule_callback) ─> fin_callback | fin_no_callback | fin_deceased | fin_wrong_number
        ├─ deceased / wrong_number ─> fin_deceased | fin_wrong_number
        └─ else ─> opening_retry (who2) ─> ask_<q1> | third_party | fin_declined | fin_unclear | ...
ask_<q1> ─ verified ─> ask_<q2> ─ all_verified ─> load_account (api_request get_account, maps data.products)
   │ refused ─> count_decline_<q> (code) ─> back to ask_<q> | fin_declined          └─> prepare (code: product facts,
   │ 3 wrong ─> fin_failed ; transferred ─> fin_transferred_human                        band, floor, deadline, calendar)
                                                                                           └─> negotiate (tts statement;
negotiate ─ ok true ─> fin_promise ; failed twice ─> fin_service_error                          create_promise, transfer_to_agent)
   ├─ topic=hardship ─> hardship (create_promise) ─> xfer_support | fin_hardship | fin_promise
   ├─ topic=already_paid ─> fin_paid ; topic=dispute ─> fin_dispute
   ├─ topic=new_plan ─> xfer_restructuring (api_request transfer_to_agent queue=restructuring) ─> fin_transferred_restructuring
   ├─ transferred ─> fin_transferred_human
   └─ transition_to_fin_refused (tool-call) ─> fin_refused
fin_<key> (code: outcome, reason) ─> end_<key> (end_call, farewell)      × 16 outcomes
workflow tools: close_call (end_of_call lifecycle, reads {{outcome}}/{{reason}})
```

What goes where when a new brief arrives: the outcome table → `end_pair` calls; holidays, windows and deadline
rules → `SETUP_CODE(..., extra=...)`; bands, floors and product wording → the prepare body (with
`products_from_vars()` and the `CAL_HELPERS` functions); identity questions → one `ask_<q>` node per question with
`api_tool(api, "verify_identity", baked={"field": q})` and `verify_post`; prompts and extraction descriptions →
the `conv` calls. Nothing in the library names a holiday, an amount, a band or an outcome.

## Proof of equivalence

`python3 out/gen_brief-a_lib.py && python3 out/compare_brief-a_lib.py` — 46 nodes both, 3 differing paths
(setup code, prepare code, the schedule_callback post hook), each executed on the same inputs with identical
results; no other path differs. `freya.validate_workflow('lib-port-check', wf)` dry-run accepted the port.
