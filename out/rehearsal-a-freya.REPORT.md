# Rehearsal: Brief A, organisers' simulator as the practice runner (11 Oct 2026, 01:47–01:59 UTC)

Command (unchanged, no intervention while it ran):

```
( time python3 builder/build.py briefs/brief-a.md tools/openapi.json --runner freya ) 2>&1 | tee traces/rehearsal-a-freya.console.log
```

Environment, fixed before the run (no restart needed):
- `claude_agent_sdk` was not installed in the container: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (claude-agent-sdk 0.2.165). The nested CLI answered `OK`; `freya.workspace_id()` answered.
- `OPENAI_API_KEY` was still set in the environment but is revoked: the run was started with it **unset**, so nothing could call OpenAI (sim.py falls back to the Claude CLI; it was not used in this run anyway).
- No `env.sh` in the container (keys come from the environment). The build agent ran `source env.sh` once; it failed silently and cost nothing.

Freya: workflow `218f59ac-47b1-48c5-ad3c-feb2d2ad8d81`, agent `e1d8367c-740e-4f64-af0f-4eb30a13df9a`, published version 1, 69 steps, 6 tools. Simulation `accc6f9f-153c-4da1-b130-d431430e371a`.

## Timing

Total **697 s (11 min 37 s)**, `real 11m37.6s`. Budget `--minutes 29`: nothing was cut off; **17.4 minutes unused**. The build agent was given about 20.7 minutes and ended after 9.2.

| Phase | From → to (s) | Seconds | Model calls | Cost |
|---|---|---|---|---|
| rules (`rules.py`: 6 extract, 1 merge, 1 verify) | 0 → 77 | 76 | 8 × claude-opus-5-5 | $1.49 |
| cases (`cases.py`) | — | 0 | not run: the kit's practice set exists for Brief A | — |
| build agent: load skill, read conflicts | 77 → 88 | 11 | | |
| build agent: generator (copied `out/gen_brief-a_v3.py` → `out/gen_brief-a.py`), generate + lint | 88 → 93 | 5 | | |
| build agent: save on Freya (`save_workflow`, publishes) | 94 → 98 | 4 | | |
| build agent: dry run / smoke over the chat route | — | 0 | **not run** | |
| build agent: in-loop audit | — | 0 | **not run** | |
| build agent: practice run (`tools/run_cases.py`, 10 cases × 1) | 100 → 613 | 513 (simulation 496) | organisers' simulator | Freya credits, ~$0.22 of calls |
| build agent: read results, stop | 615 → 627 | 12 | | |
| build agent total | 77 → 627 | 549 | 11 turns, claude-opus-5-5 | $0.50 |
| fixes | — | 0 | none attempted | |
| final lint (`lint.py --budget --call-vars …`) | 628 → 631 | 3 | 0 | |
| audit (`audit.py`, 6 batches + ranking) | 631 → 696 | 65 | 7 × claude-opus-5-5 | $4.38 |
| export + trace | 696 → 697 | 1 | 0 | |
| **total** | | **697** | **16 builder calls + 11 agent turns** | **$6.37** |

Inside the practice run: the simulation started 01:49:04; the last call ended 01:54:58; the iteration completed 01:57:22. About **144 s** was the platform's post-call analysis, and it still came back without a verdict for 7 of 10 calls.

## Practice result

`run_cases.py` printed **2 / 10**, and that figure is what the trace records. The real result is **10 / 10**: every ledger check passed, and every call's own analysis (`get_call(id)['analysis']['successEvaluation']`, read after the run) is `success: True`. The 8 "failures" are all on the judge side: the iteration row said `inconclusive` with reason `None` (7 cases), or run_cases gave up waiting at 300 s while the verdict was still on its way (PUB-03; the iteration row later said `pass`). The iteration reports `passedRuns 3, failedRuns 0, inconclusiveRuns 7`.

| Case | Family | Ledger (tools) | run_cases verdict | Iteration row (re-read) | Call analysis | Slowest turn | Real |
|---|---|---|---|---|---|---|---|
| PUB-01 | Happy path | verify, verify, get_account, promise, close_call ✓ | no verdict | inconclusive | success | 3.8 s | pass |
| PUB-02 | Third party | schedule_callback, close_call ✓ | pass | pass | — | 0.9 s | pass |
| PUB-03 | Identity | verify ×3, close_call ✓ | analysis never arrived (300 s) | pass | success | — | pass |
| PUB-04 | Dates | verify, verify, get_account, promise, close_call ✓ | no verdict | inconclusive | success | 9.3 s | pass |
| PUB-05 | Hardship | verify, verify, get_account, close_call ✓ | no verdict | inconclusive | success | 2.4 s | pass |
| PUB-06 | Amounts | verify, verify, get_account, promise, close_call ✓ | pass | pass | success | 3.0 s | pass |
| PUB-07 | Dates | verify, verify, get_account, promise, close_call ✓ | no verdict | inconclusive | success | 2.6 s | pass |
| PUB-08 | Already paid | verify, verify, get_account, close_call ✓ | no verdict | inconclusive | success | 2.7 s | pass |
| PUB-09 | Restructuring | verify, verify, get_account, transfer, close_call ✓ | no verdict | inconclusive | success | 3.9 s | pass |
| PUB-10 | Tool failure | verify, verify, get_account, promise ×2, close_call ✓ | no verdict | inconclusive | success | 3.9 s | pass |

## Checks

- **Final lint** (`out/brief-a.workflow.json`, as build.py ran it): **0 errors, 7 warnings, 14 info**. The warnings: a setup code node with statements outside try/except; `payment` in the system prompt before verification; `transfer_to_agent` on `ask_dob`/`ask_phone` before verification (R41/R50/R51); 7–8 extraction variables on `confirm`, `hardship` and `negotiate`. The agent saw the first two at +91 s and did not act on them.
- **Audit**: implemented 58, partial 3, missing 0, contradicted 0, of 61. The partials: R22 (one shared refusal/question counter across both identity stages), R31 ('this <weekday>' resolves into next week), R59 (the deceased farewell has no thank-you). These are real gaps in the reference generator, but the audit runs after the agent has ended, so nothing could act on them.
- **Export** `submission/brief-a.workflow.json`: loads as JSON. `initial_node` = `opening`, `node_type: conversation`. `test_variables` = `{}`. The previously committed export carried `c_test`, so this is better. The file holds the platform's round-trip (nulls, `agent_config`), so `lint.py` on the export shows 118 null "errors". That is expected: lint is for `out/`. Size 1.48 MB, against 123 KB before: the ~67 KB policy module is embedded in each of ~20 policy code nodes. The platform accepted it and turns stayed ≤ 9.3 s.
- **Trace** `traces/brief-a.log` (+ `.jsonl`, timestamped copies, console log). It has start and end time, all 16 builder model calls with model and purpose, the agent's 11 turns with every tool call, what was created on Freya (workflow id, agent id, version, 69 steps by name, 6 tools), the lint and audit results, and the practice result line. Gaps:
  - The practice result line records the misleading 2/10 and truncates after PUB-04.
  - There is no per-case table and no total-cost line; the costs are spread over three lines.
- **Keys**: no value of FREYA_API_KEY, FREYA_BANK_TEAM_KEY, OPENAI_API_KEY or ANTHROPIC_API_KEY, and no `fak_`/`sk-` pattern, appears in any trace or console file. `tools/check_secrets.sh` passes.

## Pipeline findings

No practice case failed on the agent's behaviour, so no transcript points to a rule fix. The failures are in the pipeline:

1. **No verdict means unknown, not failed, and the builder has no way to recover it.** Neither `run_cases.py` (kit file, unchanged) nor `builder/freya_cases.py` nor the skill looks at `get_call(call_id)['analysis']['successEvaluation']` when the iteration row is `inconclusive` or missing. The agent stopped and reported "2/10, can't say how the other 8 would score". Fix in the builder, not the kit:
   - a small `builder/` wrapper (or a step in `freya_cases.py`) that re-reads the iteration once after about 60 s and then each call's `analysis` for no-verdict rows, and prints a corrected table;
   - one skill line under step 9: "a `no verdict`/`inconclusive`/`analysis never arrived` row is not a failure: run the recovery before you fix anything".
   This also makes the trace show the real result.
2. **The rehearsal on Brief A does not exercise the hidden path.** The agent copied the reference generator for this same brief (`out/gen_brief-a_v3.py`), so the generator was in place by +93 s. On a hidden brief, the generator writing (rehearsal 2: ~21 min on brief G) is the long pole. This run validates the mechanics (rules, save, organisers' runner, lint, audit, export, trace) but not build time or quality on an unseen brief. The `--runner freya` path with *generated* cases (`cases.py` → `freya_cases.py`) was not exercised either, because Brief A has a practice set.
3. **The agent ended with 11.5 minutes of its own budget left** and skipped steps the skill lists: smoke over the chat route, in-loop audit, and acting on the two lint warnings. The skill should say what to do with the time left after a practice round: audit, fix the partials, re-save, and re-run the failing cases only.
4. **The audit runs after the agent, so its findings are evidence only.** It cost 65 s and $4.38 (69 % of the builder's spend) and found 3 actionable partials that nobody could act on. When there is more than 8 minutes left, run `audit.py` inside the agent loop (the skill already allows it) or start it in parallel with the practice run, so the agent can fix the top items.
5. **The trace's practice line truncates** (`hits[:24]` and 160 characters per hit leave PUB-05..10 out). After the agent ends, build.py should append the parsed results JSON (one line per case) and a total cost line.

## Time wasted

| Where | Seconds | Note |
|---|---|---|
| Platform post-call analysis inside the practice run | ~144 | Unavoidable, and the verdicts still did not arrive |
| run_cases waiting on PUB-03's analysis (300 s cap) | overlapped in the 144 s | |
| Agent stopping early instead of using the budget | ~690 unused (agent), 1,043 unused (total) | Not wasted wall time, but wasted opportunity: no smoke, no fixes |
| Audit with no consumer | 65 ($4.38) | Run it in the loop instead |
| `source env.sh` in the agent's commands (file absent in the cloud) | ~0 | Harmless |

## Verdict

**Not yet ready for Sunday.** The mechanics work: one command, 11.6 minutes, a valid export, a complete trace and no leaked keys. The scored agent itself is 10/10 on the ledger and on the call analyses. Before Sunday:

1. Add no-verdict recovery for the organisers' simulator (finding 1). Without it, a `--runner freya` build on a hidden brief can "fix" an agent that is already right, or stop early, and the trace understates the result.
2. Rehearse the hidden path with `--runner freya` on a brief with no reference generator and no practice set (synthetic C/D/E), to measure the real build time and the generated-cases runner (finding 2).
3. Tell the agent what to do with the remaining budget, and move the audit inside the loop (findings 3–4).
4. Write the per-case practice results and the total cost into the trace (finding 5).

If (1) cannot land in time, use `--runner sim` (with the Claude CLI customer and judge, since OpenAI is revoked) for hidden briefs.
