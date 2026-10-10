# Brief C on the v3 architecture (policy as code): transfer test report

Run: cloud worker, Sat 10 Oct 2026, 20:50–23:00 UTC, branch `cloud/brief-c-v3`. The builder's procedure
(`.claude/skills/build-phone-agent/SKILL.md`) was followed by hand, as the automatic builder would follow it. Inputs:
`tests/synthetic/brief-c.md`, `tools/openapi.json`, `out/brief-c.rules.json` (64 rules). No `brief-c.spec.json` and no
`brief-c.rules.conflicts.md` exist. The structure came from `out/gen_brief-a_v3.py` and every value from Brief C.
`out/gen_brief-c.py` (the old v2 generator) was used only to check Brief C's values afterwards, as the task allowed.
`tests/synthetic/brief-c.rationale.md` and `tests/cases/brief-c-extended.rationale.md` were not read.

## Result

| | |
|---|---|
| slot | `brief-c-v3` |
| workflow_id | `239c5d00-d0cc-4202-83a2-71794aff95c6` (version 3, published) |
| agent_id | `e5343a6b-e5c3-4097-b0e5-2a9534def898` |
| nodes | 71 (initial node `opening` is a conversation node; 18 policy code nodes; 16 fin/end pairs; 4 transfer `api_request` nodes; `plan_offer`) |
| tools | verify_identity ×2 (normalise + Brief C wrong-answer counter), schedule_callback, get_account, create_promise (in `record_promise`, an `api_request` node), transfer_to_agent ×4 (engine-run), `close_call` as the `end_of_call` lifecycle tool. No `add_note` (R47) |
| test_variables | none shipped |
| lint | `0 error(s), 10 warning(s), 14 info` (`out/brief-c_v3.lint.txt`) |
| practice set (10) | round 1: 8/10 · round 2: 8/10 · round 3 (`--only PUB-07`): 1/1. Every remaining failure is a judge or simulator artefact (below) |
| extended set (30) | ext1: 26/30 · ext2: 27/30 · ext3 (`--only EXT-C-09`): 0/1. One case is still open: EXT-C-09, where the customer model keeps rejecting the read-back (below) |
| audit | first: 60 implemented / 4 partial / 0 missing / 0 contradicted. Final: **62 / 2 / 0 / 0** |

Files:
- Generator and agent: `out/gen_brief-c_v3.py`, `out/brief-c_v3.workflow.json`.
- Audits: `out/brief-c_v3.audit.{json,md,log}` (final) and `out/brief-c_v3.audit.round1.*`.
- Simulator runs: `out/sim/brief-c-v3/{round1,round2,round3,ext1,ext2,ext3}.{json,log}` plus a transcript folder for each.
- Smoke tests: `out/smoke/brief-c-v3/*.json|log`.

## How long the port took, and what the skill made easy or hard

**Time.** I started at 20:50. The first agent was linted (0 errors), saved and through all three smoke scripts at
21:01, about 11 minutes later. Reading took most of that time. The repair rounds, the library fixes and the tooling
fixes took the rest of the two hours. Most of that time was spent waiting for the simulator: about 18 minutes per
practice round and about 33 minutes per extended round at concurrency 2.

**What the skill made easy:**
- The opening, the third-party node and the identity questions follow `gen_brief-a_v3.py` almost line for line.
- `Policy(texts=...)` refuses to build without the brief's own sentences, so no Brief A wording could slip through.
- The date logic carried over directly to a Monday-to-Saturday calendar with a Friday holiday: the deadline as the
  Nth business day, the next business day, Saturday as a business day, and Sunday or a holiday moved to the next
  business day.
- The three verbatim lines (R1, R4, R39) became tts or code-built text; lint's `--rules` check caught the one I had
  split in two.
- Asides answered robot, scam and discount questions on turns that went through code.

All of the following hand checks agreed with the brief:

| Check | Result |
|---|---|
| Green deadline (9th business day after Wed 14 Oct) | Mon 26 Oct |
| Amber deadline (4th business day) | Tue 20 Oct |
| Card floor, 40% of 2126.50 rounded up | 851 |
| "this Friday" / "next Friday" | Fri 16 Oct, a holiday, so the agent proposes Sat 17 Oct |
| Callback window | today after 11:00, Thu 15 Oct, Sat 17 Oct (Fri 16 is skipped) |

**What the skill made hard: what the automatic builder would have missed.** This is the real finding. These are listed
from most to least serious.

1. **The Policy parameters held Brief A's choices, and several of Brief C's choices did not exist at all.**
   Copying the structure of `gen_brief-a_v3.py` meant silently copying Brief A's values:
   - `human_limit=2` asks "anything I can help with first?", but Brief C R43 says never ask first.
   - `notalk_limit=2` insists once, but Brief C R46 says end at once.
   - `fail_max=2` retries once, but Brief C R38 allows two more tries.

   Three Brief C rules had no parameter, so a builder could only get them wrong or push them into prompts:
   - A second vague answer: Brief C R23 counts it as a non-answer that uses an attempt, where the library always
     proposed the deadline.
   - An amount above the full amount: Brief C R28 says record the full amount, where the library always asked again.
   - The promise reason `full` or `partial`, and "the promise decides" over a later transfer (R47): the library wrote
     an empty reason.

   The skill named none of these parameters. Fixed in `builder/policy.py`:
   - new parameters `vague_again`, `above_full`, `promise_reasons`;
   - new methods `ending_code` and `end_pair`;
   - optional text `above_full_again`.

   The skill now says "read every Policy parameter off the brief" and lists them. A `fin_keys` value may also name a
   transfer node (Brief C's dispute is a transfer).
2. **The audit step could not run on any v3 workflow.** The digest repeats the ~40 KB policy core in each of 18 code
   nodes and the ~20 KB normalisation hook on every tool. The v3 digests were 1 MB for Brief C and 880 KB for Brief A.
   The Claude CLI received this as one `--system-prompt` argument, so it failed with `Argument list too long` (Linux
   caps one argument at 128 KiB). On Sunday the builder's audit step would have crashed for every hidden brief. Fixed
   in two places:
   - `builder/audit.py`: a code block similar to an earlier one is printed as a unified diff against the closest
     match, which brings the Brief C digest down to 172 KB.
   - `builder/rules.py`: a system prompt over 100 KB goes through `--system-prompt-file`.

   Both audits in this report ran after the fix.
3. **A hang-up before any ending sent a wrong outcome.** In ext1 EXT-C-09 the call ended in the read-back loop with
   no ending node reached. `close_call` then went out as `promise/full` with no promise recorded, which is a false
   record. Fixed in the generator: `setup` writes `not_verified/withheld` (customer confirmed) or
   `not_reached/unconfirmed`, and `prepare` writes `no_promise/declined_offer`. The skill now says to write a default
   outcome per phase.
4. **Generic date-resolution bugs in `policy.resolve_when`.**
   - "Monday the 26th" and "Sunday the 25th" resolved to the coming Monday or Sunday (19 or 18 Oct) instead of the
     26th or 25th. Any brief, and any customer who names both a weekday and a date, would hit this. The day of the
     month now wins.
   - Under `first_after`, "this Friday" said on a Friday resolved to today; it now gives the next Friday. The audit
     found this one.
5. **The read-back change loop had no exit.** `ev_change` reset the per-product check counter, so a customer who
   repeated the same correction looped confirm → change → confirm without end (10 times in ext1 EXT-C-09).
   `max_checks` is now the exit for changes too.
6. **`QUESTION_ENUM_CLAUSE` contradicts Brief C.** The clause tells the extractor that "what this is about" is a
   harmless question. Brief C R16 names exactly that question as the deflection that counts (twice closes `withheld`).
   A builder appending the clause, as the skill said, would never have closed EXT-C-07. The skill now says to put the
   brief's counted question under the refusal value and write the `question` value without it.
7. **Smaller gaps:**
   - `hardship_node` had no human-request route; Brief C's R43 applies during hardship too. Added `human=True`.
   - `normalise_pre` had no reading for "ask for the month as a word". Added `date_order='none'`: an ambiguous
     numbers-only date is left as said, so the service rejects it unread and it does not count as a wrong answer.
   - The smoke scripts hard-code "Freya Bank" in the opening check. The skill now says to copy them with the brief's
     bank name, and that `unknown customer_id` on the smoke's fake id is expected.

Tests added:
- `builder/tests/test_policy.py` (now 37 tests):
  - `vague_again`
  - `above_full` and `above_full_again`
  - `promise_reasons`/`ending_code`
  - weekday plus day of the month
  - `first_after` on the same weekday
  - the hardship human route
  - the bounded change loop
- `builder/tests/test_normalise.py`: a `date_order='none'` table.

Results, all passing:

| Check | Result |
|---|---|
| `test_lint.py` | 29/29 |
| `test_normalise.py` | 148/148 |
| `test_policy.py` | 37/37 |
| `gen_brief-a_v3`, `gen_brief-b_v3`, `gen_brief-a_lib`, `gen_brief-b_lib`, `gen_brief-a_v2` | all still build |
| `compare_brief-a_lib` | 0 uncovered |
| `compare_brief-b_lib` | 0 uncovered |
| `compare_brief-a_v2` | 9 unexpected differences, identical on `origin/main` (pre-existing, not from these changes) |

## Simulator rounds

All rounds used `builder/sim.py` with the gpt-5-mini customer, the gpt-5 judge, `--close-from-args` and concurrency 2.
Failure classes:
- **agent**: an agent bug.
- **judge**: a judge artefact.
- **sim**: a simulator, customer-model or chat-route artefact.
- **case**: a case error.

### Practice set (`tests/synthetic/brief-c.cases.json`)

| case | round 1 (agent v1) | round 2 (agent v2) | round 3 (agent v3) |
|---|---|---|---|
| PUB-01 happy path | PASS | PASS | |
| PUB-02 third party | FAIL **sim**: ledger right (`not_reached/scheduled`, callback 15 Oct 11:00), but `close_call` was missing from the call log fetched for the judge | PASS (after the sim fix) | |
| PUB-03 identity, 2 wrong | PASS | PASS | |
| PUB-04 date after deadline | PASS | PASS | |
| PUB-05 hardship + discount | PASS | PASS | |
| PUB-06 too much → floor, Friday holiday | PASS (851 on Sat 17 Oct, `partial`) | PASS | |
| PUB-07 vague → Monday the 26th | PASS | FAIL **sim**: after three 504s the chat route resumed the call from the date-of-birth message (`conversation_resumed isBranch=true`), so the payment answer was routed from `ask_dob` | PASS |
| PUB-08 already paid | FAIL **judge**: counts the statement's mandatory R29 question as a persuasion attempt | FAIL **judge**: same | |
| PUB-09 plan review | PASS | PASS | |
| PUB-10 tool failure, holiday | PASS (retry, then recorded) | PASS | |
| **total** | 8/10 (9/10 with the sim fix) | 8/10 | 1/1 |

### Extended set (`tests/cases/brief-c-extended.cases.json`, 30 cases)

| case | ext1 (agent v1) | ext2 (agent v2) | ext3 (agent v3) |
|---|---|---|---|
| EXT-C-01..08, 10..16, 18, 20, 22..30 (25 cases) | PASS | PASS | |
| EXT-C-09 pays 320 > full 310.50 on Sat 17 Oct | FAIL **agent**: the customer answered every read-back of 310.50 with "No, it's 320". The agent looped 10× (no loop exit) and `close_call` sent `promise/full` without a promise | FAIL **sim**: loop now bounded (6 checks → `declined_offer`, a correct record of what happened); the customer still rejected every read-back | FAIL **sim**: same customer behaviour with the plainer second sentence (`above_full_again`) |
| EXT-C-17 hardship → care team | FAIL **judge**: R29 question read as persuasion; the agent made none (transcript checked) | FAIL **judge**: same | |
| EXT-C-19 dispute → contested | FAIL **judge**: same | FAIL **judge**: same | |
| EXT-C-21 person at first question | FAIL **sim**: the customer answered the first question and asked for a person at the second; the agent then transferred correctly | PASS | |
| **total** | 26/30 | 27/30 | 0/1 |

Fixes between rounds:
- **After round 1 / ext1:**
  - generic (policy): bounded change loop, "this <weekday>" under `first_after`, hardship human route;
  - tooling (sim): the judge gets the ledger's `close_call` when the call log has none yet;
  - tooling (audit): code dedup, system prompt from file;
  - skill: Policy parameters, hang-up defaults;
  - generator: per-phase default outcome, hardship `human=True`, clearer above-full sentence, `max_checks=6`.
- **After round 2 / ext2:**
  - generic: `above_full_again`;
  - sim: flags chat-route branches (`isBranch`) in the row and the output line.

**On EXT-C-09.** Brief C R28 says "Above the full amount: record the full amount and say so". R35 says read back the
amount, then ask "Shall I record this?", and record only after a clear yes. The agent does exactly that. The
gpt-5-mini customer reads "Confirm at the read-back" as "confirm only if it says 320" and never says yes, in three runs
out of three. I did not make the agent record without a yes, because that would break R35. If the organisers' customer
model is equally literal, the brief's own rules make this case unpassable for any agent that reads back.

**On PUB-08, EXT-C-17 and EXT-C-19.** The brief fixes the statement (R18) and the negotiation opening (R29,
word for word) before the customer says anything about payment, hardship or a dispute. The judge reads that question
as a request or a persuasion attempt. The v2 agent met the same judge reading (`out/brief-c.REPORT.md`). Changing the
agent would break R29.

## Audit (`builder/audit.py`, claude-opus-5-5)

| run | implemented | partial | missing | contradicted |
|---|---|---|---|---|
| round 1 (agent v1) | 60 | 4 (R29, R34, R50, R64) | 0 | 0 |
| final (agent v2/v3; v3 changed one optional sentence) | **62** | 2 (R01, R34) | 0 | 0 |

- R29 ("this Friday" said on a Friday), R50 (person requested during hardship) and R64 (hang-up with no outcome) were
  fixed after round 1.
- **R34 is left partial on purpose.** R27 says the floor "may be named a second time only as attempt 2". R31 says
  attempts are "for the floor if the customer has already said the full amount is too much", so after "too much" and a
  declined floor, attempt 1 names the floor again. The agent follows R31's explicit ladder (`full_or_floor`). The v2
  report found the same contradiction. No case decides it: EXT-C-10 and EXT-C-11 pass either way.
- **R01 is left partial.** `days_late` outside 1–45 is outside the call population, and the brief gives no outcome for
  it.

## What I could not do / open items

- **EXT-C-09** is still red: the customer model never confirms a read-back of the capped amount (see above). The open
  question for the team: should "record the full amount and say so" skip the confirmation question? I kept R35.
- **Judge artefacts** on PUB-08, EXT-C-17 and EXT-C-19 are left as they are, because the agent behaviour is mandated
  by R18 and R29.
- **Not run on the organisers' simulation.** `tools/run_cases.py` was forbidden. Its mock would also reject Brief C's
  reason names (see `out/brief-c.REPORT.md`).
- **One run per case.** The organisers require 3 out of 3. With concurrency 2 and about 33 minutes per extended
  round, I did not repeat the cases.
- **Lint warnings I read and left:**
  - `id_route` and `hint_day_month_swapped` are written by post hooks; lint does not see hook writes.
  - `setup` defines functions outside try.
  - The library's `PERSONA_CONDUCT` mentions "payment plan" in the system prompt before verification. It is an
    instruction to the model, not speech, but lint is right that the pre-verification prompt contains the word. A
    library-level fix would reword the conduct line.
  - Three nodes have more than 4 extraction variables (the policy design).
- **R26 for loans:** the instalment is rounded up to whole units (103.50 becomes 104), the same reading as v2. No case
  covers it.

## Changed files (brief-agnostic unless noted)

- `builder/policy.py`:
  - parameters `vague_again`, `above_full`, `promise_reasons`; text `above_full_again`;
  - methods `ending_code`, `end_pair`; `hardship_node(human=)`;
  - `resolve_when`: day of the month wins over the weekday, and `first_after` for "this <weekday>";
  - `ev_change` no longer resets the loop counter.
- `builder/freyalib.py`: `normalise_pre(date_order='none')`.
- `builder/audit.py`: code dedup in the digest.
- `builder/rules.py`: a long system prompt goes through `--system-prompt-file`.
- `builder/sim.py`: the ledger's `close_call` is given to the judge; chat-route branches are flagged.
- Tests: `builder/tests/test_policy.py`, `builder/tests/test_normalise.py`.
- Docs: `builder/FREYALIB.md`; `.claude/skills/build-phone-agent/SKILL.md` (Policy parameters read off the brief,
  question/deflection clause, `date_order='none'`, hang-up default outcome, smoke-script bank name).
- Brief C only: `out/gen_brief-c_v3.py`, `out/brief-c_v3.workflow.json`, `out/brief-c_v3.*`, `out/sim/brief-c-v3/**`,
  `out/smoke/brief-c-v3/**`.
