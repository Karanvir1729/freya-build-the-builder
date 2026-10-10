---
name: build-phone-agent
description: Build a Freya phone agent from a bank's brief and tool API with builder/freyalib, check it (lint, dry run, smoke, rule-coverage audit, practice cases when they exist) and fix what fails. Use when asked to build or improve a phone agent from a brief.
---

# Build a phone agent from a brief

You are the builder. Input: one or more brief files, a tool API file (OpenAPI JSON), a slot name, and sometimes a cases file for practice. Output: `out/gen_<slot>.py` (your generator), `out/<slot>.workflow.json` (what it emits), saved on Freya under the slot. Work from the repo root.

Use ONLY what the given brief(s) and tool API file say. Never copy a rule, value, date, name, enum or sentence from another brief, from the reference generators, or from memory. Hidden briefs differ from the kit's in every dimension: identity questions, wrong-answer limits, calendars and holidays, bands and deadline formulas, floors, attempt counts and proposals, outcome/reason tables, verbatim sentences, callback windows, tool fields and enum values. Customers can have one to three products. A brief can be raw material (a mail, a policy extract, a memo that changes it, a code list): a later document overrides an earlier one; apply the rule in force.

## Procedure

1. **Read everything.** The brief(s) in full, then the tool API file (every path, field, enum, description, required list), then the rule inventory `out/<slot>.rules.json` and `.md` (made before you started; if absent run `python3 builder/rules.py <briefs> --api <api> --out out/<slot>.rules.json`). Every rule `in_force` must end up implemented somewhere.
2. **Read the references.** `builder/FREYALIB.md` (the library), `out/gen_brief-a_lib.py` (reference generator for a one-product brief, 10/10 on its practice cases), `builder/MULTIPRODUCT.md` and `out/gen_brief-b_lib.py` (reference for up to three products: per-product state in hooks, add_note, finalize). They encode ANOTHER bank's rules: take the structure, never the content.
3. **Design the mapping.** For every rule decide where it lives, and write `# R12`-style comments next to the code:
   - **code node** for anything computable: business days, holidays, deadlines per band, floors, attempt proposals, callback windows, weekday words, counters (wrong answers, refusals, attempts). Do all arithmetic in code and hand the model finished facts as text (`{{facts}}`), including a day-by-day calendar with allowed/not allowed per product.
   - **tool definition** from the API: every body field as a leaf with the spec's type/description/enum; bake what the workflow knows (`customer_id`, `field`, `queue`, `outcome`), let the model fill the rest; descriptions say WHEN to call the tool.
   - **transition** for every state change: route on tool results (`ok_true`, counters, `wrong_answers_left`), on extracted enums (`who`, `topic`, `support_choice`), never on prompt text; deterministic conditions first, `intent_tool` as the fallback exit.
   - **hook** (`what_next_post`, `verify_post`, `promise_post`) so every tool result carries a `what_to_do_next` line in the brief's terms.
   - **prompt sentence** for conduct rules; verbatim sentences go into `on_enter` tts text or the terminal farewell, quoted exactly as the brief writes them.
4. **Write `out/gen_<slot>.py`** with `builder/freyalib.py` (`sys.path.insert(0, 'builder')`). Architecture rules:
   - The **initial node is a conversation node** (the opening). The chat route (used by the local simulator and the smoke tests) skips a first code node; simulations do not. Compute facts in code nodes entered after the first customer turn: `opening` (extract who answered) → `setup` (code, passthrough, routes on `who`) → `ask_<q1>` / `third_party` / `fin_*`. Every code node must be safe to run with partial state (`vars.get`, fallbacks).
   - One `ask_<field>` node per identity question, in the brief's order, `api_tool(api, "verify_identity", baked={"field": ...})`, `verify_post` with the API's hint values and the brief's wrong-answer limit. If the brief's limit is stricter than the service's, count wrong answers in a hook or code and route on your own counter.
   - `get_account` in an `api_node`; a `prepare` code node computes per-product facts; the statement of the debt is a tts `on_enter` built in code from the brief's wording.
   - **Multi-product whenever the brief allows more than one product**: per-product band/deadline/floor/attempts, one-by-one handling in the brief's order, read-back rules as the brief says (one for all, or per product), `add_note` when the brief uses it with the API's reason enum, a `finalize` code node choosing the closing outcome by the brief's precedence. Build it even when the practice cases happen to have one product.
   - One `end_pair(key, outcome, reason, farewell)` per row of the brief's outcome/reason table, farewell with the brief's verbatim closing words; `close_call_tool(api, ...)` as the `end_of_call` lifecycle tool, enum from the API.
   - Say "recorded" only after `ok` true; retries exactly as the brief says; never end a turn without speaking or calling the next tool (put this in the system prompt).
   - **Never emit `test_variables`** (`assemble(..., test_variables=None)` or leave it out). On the chat route the tool bodies of conversation nodes take `customer_id` from `test_variables` instead of the call, so every bank call fails; without `test_variables` the real id is used (verified) and simulations are unaffected.
   - `assemble()` must pass; no `null`, no `{{` in code, booleans tested both spellings, every passthrough ends with `always`, every path reaches an end node.
5. **Generate and check locally.** `python3 out/gen_<slot>.py <api>`; `python3 builder/lint.py out/<slot>.workflow.json --api <api>` (fix every ERROR, read every WARN). Unit-test the date/amount code: execute the setup and prepare snippets locally with `vars` for two or three example products and the brief's `now`, print the facts, and compare with your own hand calculation from the brief (deadline per band, floor, attempt dates, callback window). Fix until they agree.
6. **Dry-run and save.** `python3 -c "import freya,json,sys; wf=json.load(open(sys.argv[2])); freya.validate_workflow(sys.argv[1], wf); print(json.dumps(freya.save_workflow(sys.argv[1], wf)))" <slot> out/<slot>.workflow.json` prints `workflow_id` and `agent_id`. The same slot updates the same workflow.
7. **Smoke.** Sequentially: `python3 builder/smoke.py <slot> --script builder/smoke_scripts/opening.json`, then `third_party.json`, then `wrong_number.json` (generic checks any collections brief must pass; adapt expectations only where this brief's wording differs). Fix failures in the generator.
8. **Audit.** `python3 builder/audit.py --rules out/<slot>.rules.json --workflow out/<slot>.workflow.json --generator out/gen_<slot>.py --out out/<slot>.audit.json`. Fix every `contradicted` and `missing` rule and the `top_fixes`; regenerate, lint, save. Audit again if time allows.
9. **Practice cases, only when a cases file was given.** `python3 builder/sim.py <slot> --cases <file> --concurrency 5` (local, parallel, needs OPENAI_API_KEY or falls back to the Claude CLI), or `python3 tools/run_cases.py <agent_id> --cases <file>` when the prompt says to use the organisers' simulation (one at a time, 3-11 minutes, run in the foreground and wait). Read every FAIL reason and the transcript; fix the generator (never the platform by hand); regenerate, save, rerun. At most three rounds. Stay inside the time budget given in the prompt.
10. **Finish** with one line: `workflow_id`, `agent_id`, number of nodes and tools, the last test result, and any rule you could not implement (say which and why).

## Rules

- Never edit the agent on the platform by hand. Change the generator and save.
- When a tool call fails, the agent must say so. It must never tell the customer something is recorded when it is not.
- A customer that passes once can fail the next time. Prefer rules in routes and code over rules in prompts.
- Keep tool definitions faithful to the API file: a field or enum value the brief mentions but the API lacks does not exist; one the API has but the brief does not mention still must be filled correctly.
- Time: the whole build must finish within the budget in the prompt. Save a working agent early (after step 6), then improve it.
