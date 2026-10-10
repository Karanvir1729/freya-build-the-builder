# multiproduct — per-product promises and notes for one-to-three-product briefs

`builder/multiproduct.py` (standard library, Python 3.10+) generalises what the organisers' example builder added
in `out/gen_brief-b.py` (3/3 on the Brief B practice cases) on top of `builder/freyalib.py`: the customer can be
late on several products, every product gets its own band, floor, deadline and attempt counter, promises are
recorded one tool call per product, and every product without a promise gets a note. The module produces Python
source for the hooks and the two code nodes; freyalib produces the JSON shapes. Nothing in it names a bank value:
bands, floors, product wording, the spoken statement, tool names and note reasons are parameters read from the
brief and the tool API file. `out/gen_brief-b_lib.py` is gen_brief-b.py ported onto freyalib + multiproduct and
`out/compare_brief-b_lib.py` proves the two outputs equivalent.

## The per-product state machine

Every product is in exactly one of three states, kept in workflow variables (all strings, written by code):

```
open ──(create_promise ok)──> recorded          rec_pids   += pid
open ──(add_note ok)────────> noted             note_log   += "pid:reason"
```

| Variable | Written by | Meaning |
|---|---|---|
| `pids_csv` | prepare | every product id in `get_account` order, comma separated (`p1,p2`) |
| `n_products` | prepare | their number, as text |
| `dl_<pid>` | prepare | that product's deadline, `YYYY-MM-DD`; `promise_pre` caps a later date to it |
| `pd_<pid>` | prepare | that product's past-due amount, `str(float)`; `promise_pre` caps a larger amount to it |
| `products_text`, `statement_text`, `calendar_text` | prepare | the facts block, the opening statement (tts), the tagged calendar |
| `rec_pids` | promise_post | ids with a recorded promise |
| `note_log` | note_post | `<pid>:<reason>` per noted product (one note per product) |
| `open_pids` | prepare, every hook | ids with neither a promise nor a note; shown in prompts (`{{open_pids}}`) |
| `all_done` | prepare, every hook | `"yes"` once `open_pids` is empty, else `"no"`: the ALL_DONE transition routes on it |
| `pending_pid` | promise_pre | the product of the promise call in flight (the post hook reads it) |
| `pending_note` | note_pre | `<pid>:<reason>` of the note call in flight |
| `fail_<pid>` | promise_post | failed promise calls for that product; at `max_fails` the model is told to note `fail_reason` |
| `final_route` | finalize | the fin key chosen for the close |

The hooks share `state_fn_code()`: `_getv()` returns the `vars` dict (or None when the hook has none) and
`_status(V)` recomputes `open_pids` / `all_done` and returns the "Recorded promises: … Notes: … Still open: …"
sentence that every `what_to_do_next` ends with. Because the post hook refreshes `all_done` before routing runs,
the deterministic ALL_DONE transition fires in the same turn as the last tool result.

## API

| Function | Gives |
|---|---|
| `state_fn_code(promise_tool, note_tool, still_open_text=None)` | the shared `_getv` / `_status` source |
| `promise_pre_code(cap_to_deadline=True, cap_to_amount=True, id_prefix="p", pid_field, amount_field, date_field)` | promise tool pre hook: id normalised (`'1'` -> `'p1'`), amount -> float, date -> `[:10]`, `pending_pid`, date capped to `dl_<pid>`, amount capped to `pd_<pid>` |
| `promise_post_code(max_fails=2, fail_reason="service_error", promise_tool, note_tool, ok_field="ok")` | promise tool post hook: "recorded" only on ok true (-> `rec_pids`), else retry once, at `max_fails` note `fail_reason`; `+ _status` |
| `note_pre_code(id_prefix, pid_field, reason_field)` | note tool pre hook: id normalised, `pending_note` |
| `note_post_code(promise_tool, note_tool, ok_field)` | note tool post hook: `note_log` on ok true, else retry; `+ _status` |
| `all_done_tr(target="finalize", desc)` | `eq("all_done", "yes", target)` |
| `done_intent_tr(target, desc, intent_desc)` | the tool-call fallback `transition_to_<target>` for the same event |
| `finalize_code(precedence, promise_key, paid_key, default_key, paid_reason=None, order="product", promise_tool, route_var)` | the finalize code node: writes `final_route` (see below) |
| `finalize_transitions(precedence, promise_key, paid_key, default_key, route_var, fin_prefix="fin_")` | `eq(final_route, key, fin_<key>)` for promise, paid and every precedence key, then `always(fin_<default_key>)` |
| `products_facts_code(bands, floor_rules, wording, statement, attempt1_var, id_prefix, unknown_type_words, line_template, attempt2_template, one_attempt_template, calendar_extra_days)` | the prepare body (after `freyalib.products_from_vars()`, inside `guarded()`) |
| `products_facts_fallbacks(statement_fallback, id_prefix)` | the `guarded()` fallbacks of the prepare node |
| `prepare_code(holidays, statement_fallback, business_weekdays, state_var, products_var, **facts)` | the complete prepare node source: `CAL_HELPERS + guarded(products_from_vars() + products_facts_code(**facts))` |

`finalize_code` rules, in order: a recorded promise -> `promise_key`; every product noted with `paid_reason` ->
`paid_key`; else the fin key of a non-paid note, picked by `order`: `"product"` = the first product in
`get_account` order whose note is not paid (Brief B's closing rule), `"precedence"` = the first `(reason, key)`
pair of `precedence` that some product carries; an unknown reason or no note gives `default_key`; and when the
hooks had no `vars` at all, `<promise_tool>_success_count > 0` with ok true gives `promise_key`.

`products_facts_code` parameters (every one from the brief): `bands` = ordered `{"name", "max_days_late"
(None = catch-all last), "attempts", "deadline_var" | "deadline_bdays"}`; `floor_rules` = ordered `{"types" |
None, "field", "name"}`; `wording` = ordered `{"types" | None, "template"}` with the product's fields and
`{type_words}` as placeholders; `statement` = `{"one", "many_head", "many_item", "many_tail"}` templates over
`{title} {last_name} {first_name} {n}` and the per-product facts `{pid} {words} {past_due} {days_late} {band}
{floor} {floor_name} {deadline_text} {deadline_iso} {a1_text} {a1_iso} {attempts}`. The line templates default to
the organisers' wording of the Brief A/B ladder (attempt 1 = full amount or floor on the attempt-1 date, attempt 2
= floor on the deadline); override them when a brief's ladder differs.

## How a generator wires it (gen_brief-b_lib.py, 48 nodes)

```
setup (SETUP_CODE: dates, callback window, attempt-1 date, per-band deadlines)
  └─> opening / opening_retry / third_party / ask_<q1> / ask_<q2> / count_decline_<q>   (as in FREYALIB.md)
        └─> load_account (get_account -> products) ─> prepare (prepare_code: per-product facts + state init)
              └─> negotiate (tts {{statement_text}}; tools: promise_tool + note_tool + transfer_to_agent)
                    ├─ ALL_DONE (all_done == yes)            ─> finalize
                    ├─ transferred                           ─> fin_transferred_human
                    ├─ topic = hardship                      ─> hardship (promise_tool; ALL_DONE -> finalize)
                    │       ├─ support accepted              ─> xfer_support ─> fin_transferred_support
                    │       └─ support declined              ─> hardship_notes (note_tool, reason hardship for {{open_pids}}; ALL_DONE -> finalize)
                    ├─ topic = new_plan                      ─> xfer_restructuring ─> fin_transferred_restructuring
                    └─ transition_to_finalize (tool call)    ─> finalize
finalize (finalize_code) ─ final_route ─> fin_promise | fin_paid | fin_<precedence keys> | always fin_<default>
fin_<key> ─> end_<key>  (freyalib.end_pair, one per row of the brief's outcome table)
```

Tools: `promise_tool = api_tool(api, "create_promise", pre=promise_pre_code(), post=promise_post_code(...))` with
`product_id` model-filled ("exactly as in PRODUCTS"); `note_tool = api_tool(api, "add_note", omit=[optional
free-text fields], pre=note_pre_code(), post=note_post_code())` with the reason enum and its description read
from the API file; the prompt lists the reasons from the same enum. The prepare node reads the per-band deadline
variables the setup node wrote (`SETUP_CODE(..., extra=...)`), so date rules stay in one place.

Proof: `python3 out/gen_brief-b_lib.py && python3 out/compare_brief-b_lib.py` — 48 nodes both; the differing
paths are the setup and prepare code (library helpers), the finalize code (reason -> fin key mapping), the
promise pre hook (consistent id normalisation, no unused import) and the schedule_callback post hook (string
"false" handled), each executed on the same inputs with the same effect; `freya.validate_workflow` dry run
accepted the port.
