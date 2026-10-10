# Rule inventory and coverage audit

Two Claude-powered helpers for the builder. Both run on the Claude Agent SDK in `.venv` (no tools, structured JSON output,
model `claude-opus-5-5`), work as a CLI and as a function, write their output file plus a Markdown rendering next to it,
and print a one-line summary on stdout. Progress and every model call go to stderr as
`model call: <model> | purpose: ...`, so a caller can copy them into a trace.

```
source .venv/bin/activate          # or prefix the commands with .venv/bin/python
```

## 1. `builder/rules.py`: rule inventory of a brief

```
python3 builder/rules.py <brief.md> [<brief2.md> ...] --api <tool_api.json> --out out/<slot>.rules.json
python3 builder/rules.py briefs/brief-a.md --api tools/openapi.json --out out/brief-a.rules.json
python3 builder/rules.py briefs/brief-a.md briefs/brief-b.md --api tools/openapi.json --out out/brief-b.rules.json
```

```python
import sys; sys.path.insert(0, "builder")
from rules import extract_rules
rules = extract_rules(["briefs/brief-a.md"], "tools/openapi.json", "out/brief-a.rules.json")   # returns the list
```

Output `out/<slot>.rules.json`: a JSON list, one entry per rule:

| field | meaning |
|---|---|
| `id` | `R01`, `R02`, ... in document order (renumbered after validation) |
| `source` | where it comes from: `brief-a.md rule 6`, `brief-a.md section 7 definition`, `memo 2026-10-12`, `openapi.json /close_call` |
| `category` | one of `opening, third_party, identity, disclosure, dates, amounts, persuasion, hardship, confirmation, recording, special, multi_product, closing, wording, other` |
| `text` | the rule in force, one or two sentences, numbers / dates / enum values quoted exactly |
| `verbatim` | sentences the agent must say word for word (`[]` if none) |
| `values` | structured values when present: holidays, bands `[{min_days, max_days, deadline_rule, attempts}]`, floor rules, callback window, outcome/reason mapping, identity fields order, max wrong answers, ... |
| `overrides` | id of the earlier rule this one replaces (memos that change a policy), else `""` |
| `in_force` | `false` when a later rule overrides this one; `superseded_by` then names it |

`out/<slot>.rules.md` is the same inventory grouped by category.

What the script does:
1. One model call with the brief file(s) (concatenated with a `DOCUMENT FILE:` header each) and a compact digest of the tool
   API (paths, body fields, enums, formats, required). The system prompt asks for every numbered rule, every table row,
   every definition / "never" sentence, every mandatory sentence (into `verbatim`), API constraints the brief does not state,
   and for multi-document briefs (mail + policy extract + memo + code list, or Brief A + Brief B) the new rule with
   `overrides` pointing at the old one. Output is validated against a JSON schema; invalid JSON is retried once.
2. A deterministic self-check: every numbered rule of every brief must be cited by at least one `source`, and every ISO date
   and every `` `backticked` `` token of the brief must appear somewhere in the inventory. Anything missing triggers one
   gap-fill call that returns only the rules to add (or completed `values` for an existing id), which are merged and renumbered.
3. Normalisation: ids renumbered, categories validated, `overrides` resolved, `in_force` / `superseded_by` set.

Measured on Brief A (47 numbered rules, three tables): **64 rules, 2 model calls, 73 s, $0.29** (the second call was a
gap-fill triggered by a self-check false positive that is fixed now; a clean run is one call, about 60 s, about $0.25).
Brief A + Brief B together: **74 rules (64 in force, 10 superseded), 1 call, 86 s, $0.28**; the 10 Brief B rules that change a Brief A rule carry `overrides` and restate the complete rule in force (e.g. B rule 8 `add_note` overrides "Brief A never uses `add_note`", B rule 4 overrides A rule 28, B rule 11 overrides A rule 37 and keeps its "recorded only after ok: true, retry once" part).

## 2. `builder/audit.py`: coverage audit of a workflow against the inventory

```
python3 builder/audit.py --rules out/<slot>.rules.json --workflow out/<slot>.workflow.json --generator out/gen_<slot>.py --out out/<slot>.audit.json
python3 builder/audit.py --rules out/brief-a.rules.json --workflow out/brief-a.workflow.json --generator out/gen_brief-a.py --out out/brief-a.audit.json
python3 builder/audit.py ... --digest-only            # print the workflow digest that is sent to Claude, no model call
```

Options: `--batch N` rules per model call (default 12), `--parallel N` calls in flight (default 3), `--model`,
`--generator ""` to audit a workflow without its generator. `--workflow` accepts the plain workflow or the export format
(`{"workflow": {...}}`, i.e. `submission/<slot>.workflow.json`).

```python
from audit import audit
report = audit("out/brief-a.rules.json", "out/brief-a.workflow.json", "out/gen_brief-a.py", "out/brief-a.audit.json")
```

Output `out/<slot>.audit.json`:

```
{"rules": [{"id": "R13", "status": "implemented|partial|missing|contradicted|superseded",
            "where": "third_party.task_message + setup code: callback_text", "evidence": "<one line quoted from the prompt/code>",
            "fix_hint": "<one concrete change, '' when implemented>"}, ...],
 "summary": {"implemented": n, "partial": n, "missing": n, "contradicted": n, "superseded": n, "total": n},
 "top_fixes": [{"id", "status", "rule", "why", "fix"}],        # the 5 most important gaps, most important first
 "meta": {"model", "seconds", "cost_usd", "calls", "batches", ...}}
```

`out/<slot>.audit.md` renders the summary table, the top fixes, the contradicted / missing / partial rules with evidence,
and a table of all rules.

What the script does:
1. Builds a **workflow digest** instead of sending the raw JSON (93 KB for Brief A, mostly repeated tool definitions):
   system prompt, deduplicated tool definitions (description, body fields with defaults / enums / descriptions,
   pre/post-process code, response mapping), then every node with its on_enter line, task_message, tools, code, extraction
   enums with descriptions, transitions in order with their conditions rendered as text, and terminal farewell. 46 KB for
   Brief A. The generator source (41 KB) is sent as well, so the auditor sees how values are computed.
2. Sends the rules in force in batches of 12, each batch one model call with the same context (primer on how a Freya
   workflow works + generator + digest in the system prompt, the batch of rules in the user prompt), up to 3 in parallel.
   Each judgement must point at a line (`evidence`), and a `fix_hint` is required for anything not implemented. Superseded
   rules are not audited; they are listed with status `superseded`.
3. One small call ranks the gaps (contradicted > missing > partial) into `top_fixes` with a concrete fix each. No gaps,
   no call.

Measured on Brief A (64 rules, 46-step workflow, the 10/10 generator): **run 1: 58 implemented, 6 partial, 0 missing, 0 contradicted (7 calls, 69 s, $0.95); run 2: 60 implemented, 4 partial (7 calls, 57 s, $0.34)**; 62 of 64 judgements identical between the runs, and all evidence quotes were found verbatim in the digest or generator. The partials are real but minor gaps of `gen_brief-a.py`: the hardship node has no human-transfer tool (R52, found both runs), no restructuring route and no "said twice they do not want to talk" exit (R51, R55, found in run 1 only; R51 is arguably what Brief A rule 32 wants, "this rule comes before rules 30 and 41"), a recorded promise ends the call at once so no transfer can follow it (R57), the deceased farewell has no thank-you (R59), and nothing forbids the model from calling the global `close_call` tool itself (R64).

## Cost and time per run

| run | model calls | wall time | cost |
|---|---|---|---|
| `rules.py` Brief A (47 numbered rules) | 1 (+1 gap-fill when the self-check finds a hole) | ~60-75 s | ~$0.25-0.30 |
| `rules.py` Brief A + Brief B (74 rules, 10 of them overrides of Brief A rules) | 1 | 86 s | $0.28 |
| `audit.py` Brief A (64 rules, 6 batches of 12, 3 in parallel, + 1 ranking call), first run | 7 | 69 s | $0.95 |
| `audit.py` Brief A, second run minutes later (prompt-cache hits on the shared context) | 7 | 57 s | $0.34 |

Costs are what the SDK reports (`ResultMessage.total_cost_usd`), billed to the Claude login on this machine or to
`ANTHROPIC_API_KEY` when it is set in the environment. Both scripts cap each model call at $6 (`max_budget_usd`).
Running the audit with `--parallel 1` is slower (about 3x) but the shared system prompt then hits the prompt cache,
which lowers the cost of the later batches.

## Using them inside a build

Within the 30-minute build budget, a sensible order is: `rules.py` right after reading the brief (about 1 minute), build the
workflow, then `audit.py` (about 3-4 minutes) and fix the `top_fixes` before the practice run. The audit is a static
check: it finds rules the prompts, routes and code do not cover; it does not replace a simulation.
