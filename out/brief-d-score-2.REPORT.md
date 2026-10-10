# Brief D: scoring run 2 (first simulator rounds on Kestrel Bank)

Run: 2026-10-10, ~20:15–22:40 UTC, branch `cloud/brief-d-score-2` (from origin/main 4e286e3). Slot `brief-d` = workflow
`de5f944a-d43d-4a7e-80fc-405ee4c53649`, agent `49ba465f-6ca5-4240-b4a7-c81502d3a8d8` (the workflow made by the previous
run, updated in place: `.freya-agents.json` was seeded with its id rather than creating a new workflow). Published versions
2 → 6. `OPENAI_API_KEY` empty: customer and judge ran on the Claude CLI. `tools/run_cases.py` was never run. Concurrency 2.

## Headline

| Round | Agent | Cases | Result |
|---|---|---|---|
| round 0 (`round1-haiku/`) | v2 | 13 public, default customer `claude-haiku-5-5` | stopped at 9/13 run, 0 pass: **7 of 9 failures were the customer model leaving its script** (unusable) |
| round 1 | v3 | 13 public, customer `claude-sonnet-5-5` | **13/13** |
| ext1 | v3 | 30 extended | **26/30** (2 agent bugs, 1 platform rollback exposing a hook weakness, 1 judge artefact) |
| round 2 | v4 | 13 public | 10/13 (all 3 misses platform/simulator artefacts: two 504 state rollbacks, one close-log timing) |
| ext2 | v4 | 6 extended (the 4 ext1 failures + 2 neighbours) | 5/6 (EXT-D-16: parallel add_note race after a 504) |
| round 3 | v5 | 13 public | **13/13** |
| ext3 | v5 | EXT-D-12, 16, 19 (note-heavy) | **3/3** |

Final agent: v6 (v5 + the R68 close-code fallback, checked by unit execution and two smoke scripts, not by a sim round).
Final audit: **100 implemented, 1 partial (R53), 0 missing, 0 contradicted, 16 superseded** (of 117 rules).

## Step 1: generate, lint, dry run, save, smoke

- `python3 out/gen_brief-d.py` → 53 nodes. Lint (`--call-vars … --rules … --budget`): **0 errors, 7 WARNs** (known: 3 mid-conversation verbatim lines in prompts, transfer before identity is deliberate, setup CAL_HELPERS outside try, negotiate prompt 5.3k chars).
- `validate_workflow`: valid on every version. `save_workflow('brief-d')`: v2 (same content as the earlier publish), then v3–v6.
- Smoke (`out/smoke/brief-d/score2/`, v6 re-check in `score2-v6/`): opening 31/32, third_party 39/40, wrong_number 28/29. The **only** failing check in each is the generic scripts' hard-coded `contains_any ["Freya Bank"]` on the first line (the agent correctly says "Kestrel Bank"): a **script artefact**. Behaviour: no debt words before identity, phone question first, third party gets only the personal-banking line and `schedule_callback 2026-10-15 11:00`, wrong number closes `not_reached/WN`.

## Round 0: the default Haiku customer is not usable (v2)

`sim.py` first failed outright: `CLAUDE_CLI` was hard-coded to `~/.local/bin/claude`, absent here (fixed, see below). The
re-run with the default customer `claude-haiku-5-5` produced:

| Case | Class | What happened |
|---|---|---|
| PUB-01 | simulator (customer) | Script "pays the full amount today"; customer asked for a payment plan → correct TRS transfer |
| PUB-02 | **agent bug** + judge artefact | "I'm not Maria Costa. Who's calling?" was extracted `unclear`, so the personal-banking sentence was never said (fixed in v3). Judge also counted the mock's `ok:false` on CBK against the agent (fixed in `sim.py`) |
| PUB-03 | simulator (customer) | Gave the real DOB from the persona's identity block on the 2nd try instead of the script's wrong one |
| PUB-04 | simulator (customer) | Script "accepts the latest date"; customer refused it twice and never asked the robot question. Agent handling was per 4.6/4.8 |
| PUB-05 | simulator (customer) | Script "does not want to be transferred"; customer accepted the TSP transfer |
| PUB-06 | **agent bug** | "I can't clear the full amount today. Is there a smaller amount I could pay?" → `new_plan` → restructuring transfer. Brief 4.5: "says the full amount is too much → offer the floor once"; "asks how much should I pay → the assistant proposes" (fixed in v3) |
| PUB-07, PUB-10 | simulator (customer) | Customer refused the security questions twice ("I'm not going to give those digits") → correct IDD |
| PUB-08 | judge artefact | Ledger correct (paid/AP); judge failed it only on the mock's `ok:false` for AP |

From round 1 on, the customer model is `claude-sonnet-5-5` (`--customer-model`). Same persona text, same judge.

## Round 1 (v3): 13/13

All 13 pass. PUB-05 shows `close_call` twice in the ledger but once in the call log: the engine re-sending after the kit mock answered `ok:false` to HSHP (mock artefact; with a mock that knows Brief D's codes the first close is `ok`).

## ext1 (v3): 26/30

| Case | Class | Detail and Brief D rule |
|---|---|---|
| EXT-D-16 | judge artefact | Judge said the three products were "one combined sentence"; the transcript has one sentence per product ("Your credit card ending 9015 has … Your personal loan has …"). Ledger correct |
| EXT-D-18 | **agent bug** | Read-back "the full amounts on Friday 16 October" without 220 / 640. Rule: "Read back the product, the amount and the date". Fixed v4 (prompt rule 6: every amount as a number, example given) |
| EXT-D-23 | **agent bug** | "I could have paid it on Monday the 12th" treated as a refusal (attempt 1 proposed). Rule 4.6: "a day before today: cannot be recorded; ask for a day from today onwards". Ledger passed only because the customer then named the 20th. Fixed v4 |
| EXT-D-26 | platform rollback → **hook weakness** | The confirm turn got a 504; the engine's state reverted to before `create_promise` (post hook later reported "Recorded promises: none"), the model read back and recorded again, the mock answered "this product already has a promise" three times, the hook counted 3 failures → `service_error` note + SVC. Fixed generically (library change 2) |

Passed 26 incl. every memo case (EXT-D-01..04: 5th business day, 2 × minimum payment, 18:00 window, Founders' Day → 29 Oct), identity (IDF on the 2nd wrong answer, IDD), F/S attempt ladders, dispute/paid/hardship notes, TRS after a promise, and the calendar cases (EXT-D-27..30).

## Round 2 (v4): 10/13; ext2 (v4): 5/6

| Case | Class | Detail |
|---|---|---|
| PUB-05 | simulator (timing) | Ledger correct (HSHP); the call log was fetched before `close_call` landed, so the judge saw no close |
| PUB-06, PUB-07 | platform (504 rollback) | The DOB turn (which runs `get_account`) answered 504 after 67 s; the engine's next turns ran from `ask_dob` again with the statement already spoken, so the agent could only offer a transfer (PUB-06 → TRH). The chat gateway was slow at the time (30–60 s turns) |
| ext2 EXT-D-18, 23, 26 | pass | the three v4 fixes confirmed |
| ext2 EXT-D-16 | **agent bug (generic) amplified by a 504** | The model sent the three `add_note` calls **in parallel in one message**. Each post hook saw only its own note in `note_log` (status "Notes: p2:refused. Still open: p1, p3" from every hook), so `all_done` never fired; after a 504 turn the model noted all three again → 6 notes, ledger expects 3. In ext1 and ext3 the same parallel notes happened without the extra turn and passed. **Not fixed** (see "Could not do") |

## Round 3 (v5): 13/13; ext3 (v5): 3/3

Public 13/13 again; EXT-D-12 (Band F refused), EXT-D-16 (3 products refused), EXT-D-19 (3 products hardship) all pass with exactly 3 notes.

## Agent fixes (out/gen_brief-d.py)

1. v3: `who` extraction: saying "I am not {name}" / a relative / the customer is not here is `someone_else` even with a question in the same line; the retry's answer to "what is this about" is the personal-banking sentence; `third_party` always says it first (PUB-02).
2. v3: `topic` `new_plan` only for explicit plan / instalments / spreading / general more time; "too much", "a smaller amount", "how much should I pay" go to the floor path (PUB-06).
3. v4: read-back names every product's amount as a number (EXT-D-18).
4. v4: a past day is not a refusal; say it passed and ask for a day from today (EXT-D-23).
5. v4: `promise_post_code(..., duplicate_is_recorded=True)` (EXT-D-26).
6. v5: promise post hook sets `close_outcome/close_code = promise/PRM` as soon as a promise is recorded (audit R75: a hang-up between the record and `fin_promise` closed no_promise/RF).
7. v6: close_call pre hook: no code yet (hang-up before `setup`) → `not_reached/UNC` (audit R68; the Haiku PUB-01 run showed a model-filled `not_verified/UNC` close there).

## Library / tool changes and why they transfer

1. **`builder/sim.py`**:
   - `CLAUDE_CLI` falls back to `shutil.which("claude")` when `~/.local/bin/claude` is missing. Without it every customer and judge call failed in this container.
   - With `--close-from-args`, the judge prompt now carries a note: the test bank rejects this brief's close codes, so judge the outcome and reason the agent sent. It also says `close_call` after `end_call` is the normal order. This applies to any synthetic brief whose codes differ from the kit's (Brief C, D). Before the change the judge failed correct calls on the mock's `ok:false`.
2. **`builder/multiproduct.py` `promise_post_code(duplicate_is_recorded=False)`**: new opt-in flag. When True, an `ok:false` whose `error` says the product "already" has a promise counts as recorded, not as a failed try.
   - Why it transfers: any brief with a retry rule can hit the 504 rollback. The bank holding the promise is the truth, and turning it into a service_error close is wrong in every brief.
   - The default emits byte-identical code (asserted).
   - Checks after the change: `multiproduct.py` 31/31; `builder/tests/*.py` (lint 29/29, normalise 144/144, policy 32/32); `compare_brief-a_lib` 193 pass, 0 fail; `compare_brief-a_v2` 5/5 (same 2 unexpected paths as main); `compare_brief-b_lib` 545 pass, 0 fail.
   - Documented in `MULTIPRODUCT.md`.

## Audit (`builder/audit.py`, final, on v6)

`implemented 100, partial 1, missing 0, contradicted 0, superseded 16 (117 rules)` → `out/brief-d.audit.{json,md}`.
- Run before the R75 fix (`out/sim/brief-d/audit-before-R75.md`): 99 / 2 (R53, R75). After R75: 99 / 2 (R53, R68). After R68: 100 / 1.
- Open: **R53**, a plan request *inside* hardship is not transferred to restructuring. The brief's hardship paragraph says "Nothing else is on the table: no discount, waiver, payment holiday, plan…", while the general rule sends any plan request to restructuring. This is the same brief ambiguity the first build report left open. I did not change it on the auditor's word alone: the hardship flow has its own transfer offer (support), and no case covers it.

## Is porting gen_brief-d.py to builder/policy.py worth it?

**Yes, but not before the hidden briefs, and not for Brief D's score on these cases.** On the multiproduct flow Brief D now passes 13/13 public (twice) and 29/30 extended across rounds. Every remaining failure is a platform artefact, except one:

- **Parallel tool calls racing the hooks (EXT-D-16, ext2).** The model sends several `add_note` (or `create_promise`) calls in one message, and the per-call post hooks do not see each other's state. `policy.py` writes notes and promises from code-driven `api_request` loops (`record_note`, `rec_next`), so there is no model tool call and no race. This is the strongest reason to port, and it applies to every multi-product brief built on `multiproduct.py`.
- **Prompt-carried rules that failed here and are code in policy.py:**
  - the read-back amounts (EXT-D-18): `readback()` builds the line in code;
  - the past-day reply (EXT-D-23): `check_one` handles a past day;
  - the attempt ladder and the "smaller amount" path (PUB-06): `too_much` and `refuse` in code.
  The prompt fixes hold in these runs, but a code path cannot regress with the model.
- **Against porting now:**
  - Brief D needs features the A/B v3 generators never exercised on policy.py: the closed day moved *before*, three tries on `create_promise`, required note texts (attempt count + last offer), HSHP/PRM codes on every close, and the 18:00 callback window. That is a fresh generator plus a full set of rounds.
  - Brief D's dates are resolved by the model from code-built tables (WEEKDAY WORDS, CALENDAR), not by a `date`-type extraction, so the real-clock hazard does not apply to this flow.
  - Recommendation: make `policy.py` the default for the next new brief (the skill already says so), and port Brief D only as the transfer test of `policy.py`'s multi-product path.

## Platform observations (for CLAUDE.md "Things that bite")

- **A 504 on a chat turn can roll the engine's state back to before that turn**, even though the reply was spoken. Seen 3 times: EXT-D-26 (after `create_promise` ok), PUB-06 and PUB-07 (after `get_account`). The post hook later reported pre-turn variables. Writes that already reached the bank stay. Hooks should treat "already exists" answers as success, which the new library flag does.
- The model sends parallel tool calls despite "one tool per message" in the system prompt and in every `what_to_do_next`.
- `claude-haiku-5-5` as the simulated customer leaves the script often: it refuses security questions and ignores "declines"/"accepts" lines. Use `--customer-model claude-sonnet-5-5` with the CLI provider.

## Could not do / not done

- **The parallel add_note race is not fixed.** A hook-only fix depends on how the platform merges `vars` written by concurrent hooks. That is unknown and would need a platform probe, which this run must not do. The deterministic fix is the policy.py note loop. Proposed for `multiproduct.py`: per-product state keys (`noted_<pid>`) instead of one `note_log` list; this would change A/B output and the compare scripts.
- R53 left as is (see the audit section).
- v6 (the R68 close fallback) had no sim round. It has an executed unit check of the hook (empty / placeholder / set) and two v6 smoke scripts (UNC on a cut call, WN on a wrong number).
- `submission/brief-d.workflow.json` was not exported (Brief D is a synthetic transfer test, not a submission).
- `tools/run_cases.py` was not run, as instructed. All numbers are `builder/sim.py` chat-route practice scores with Claude as customer and judge. They are not organiser scores.
- `.venv` was created locally (gitignored) to run `audit.py`, which needs `claude_agent_sdk`. The system pip could not install it (Debian PyJWT).

## Files

`out/sim/brief-d/{round1-haiku,round1,ext1,round2,ext2,round3,ext3}/` (+ `.json`, `.stdout`), `out/sim/brief-d/audit-before-R75.md`,
`out/smoke/brief-d/score2/`, `out/smoke/brief-d/score2-v6/`, `out/gen_brief-d.py`, `out/brief-d.workflow.json`,
`out/brief-d.audit.{json,md,stdout,stderr}`, `builder/sim.py`, `builder/multiproduct.py`, `builder/MULTIPRODUCT.md`, this report.
