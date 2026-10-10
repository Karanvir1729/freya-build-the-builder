# Build the Builder (Freya × YC hackathon) — solo entry

## What this repo is
A **builder**: a program that reads a bank's brief (Markdown) plus a tool API file (OpenAPI JSON) and creates a **phone agent** (a Freya workflow) with no manual edits. Only the phone agents are scored, on two hidden briefs published Sunday 11 Oct 2026 17:00 UTC, by simulated customers (score = cases passed / 60, 3 runs per case must all pass). Submission closes Sunday 20:00 UTC.

Read in this order: `README.md`, `docs/hackathon-site.md` (the event site), `docs/kit-README.md` (the organisers' kit README), `briefs/brief-a.md`, `briefs/brief-b.md`, `tools/openapi.json`, `docs/workflow-format.md`, `docs/tools-and-code.md`, `docs/api.md`, `examples/base-agent.json`.

## Layout
- `briefs/`, `tools/openapi.json`, `public-test-set.json` — kit data. Do not edit.
- `docs/` — Freya workflow format, tools/code/hooks, REST API, the kit README and the event site. Reference, written for a program to read.
- `freya.py` — API client (stdlib). `save_workflow(slot, wf)` creates a workflow once per slot and updates it in place + publishes on later runs (state in `.freya-agents.json`, gitignored). `export_workflow(id, path)` writes the file that gets submitted. `AGENT_LLM` is the phone agent's model: never change it.
- `tools/run_cases.py` — practice scorer (ledger via the mock bank + judge model on the transcript). `tools/score.py` — the ledger check. `--reps 3`, `--style <pieces|corrects|talkative|asks_back|in_words>`, `--only PUB-01,PUB-02`, `--out results/run.json`.
- `examples/` — the organisers' base agent (`base-agent.json`, 2 steps, 4 tools) and example builder (`agent_builder.py`). Reference only.
- `builder/build.py` — OUR builder, the submission entry point: `python3 builder/build.py <brief.md> [<brief2.md>] <tool_api.json> [--cases f] [--runner sim|freya] [--minutes 29]`. Pipeline: `rules.py` (rule inventory) → Claude with the skill below (writes `out/gen_<slot>.py` on the library, lints, dry-runs, saves, smoke-tests, audits, runs practice cases when any) → final lint + audit → export to `submission/<slot>.workflow.json` → `traces/<slot>.log` (+ `.jsonl`). Keys are scrubbed from traces.
- `builder/freyalib.py` (+ `FREYALIB.md`) — brief-agnostic workflow library distilled from the 10/10 generator; `builder/multiproduct.py` (+ `MULTIPRODUCT.md`) — per-product state hooks and finalize for 1–3 products. `out/gen_brief-a_lib.py`, `out/gen_brief-b_lib.py` — reference generators (another bank's rules: structure only).
- `builder/lint.py <wf> --api <api>` — static checker for every platform rule in the docs. `builder/rules.py` — rule inventory of a brief (Claude). `builder/audit.py` — rule-coverage audit of a workflow against the inventory (Claude). `builder/smoke.py` — chat-route scripts/driven transcripts. `builder/sim.py` — local parallel simulator (OpenAI customer + judge over the chat route, ledger from the mock), the default practice runner; `tools/run_cases.py` is the organisers' simulation (costs Freya credits, one at a time; cap in `results/credits.log`).
- `tests/synthetic/` — transfer-test briefs C (clean), D (raw material, multi-product), E (changed tool API) with recomputed cases; never read by the builder at run time.
- `.claude/skills/build-phone-agent/SKILL.md` — the skill the builder runs Claude with. This is where the builder's knowledge lives. Improve it (or add skills/code) to improve every agent it builds.
- `out/` — workflow JSON the builder writes. `submission/` — exported agents (scored). `traces/` — committed. `results/` — gitignored run outputs; `results/log.jsonl` is the score history.
- `env.sh` (gitignored) — `FREYA_API_KEY`, `FREYA_API_URL`, `FREYA_BANK_TEAM_KEY`. `source env.sh` before anything. `tools/check_secrets.sh` runs as the pre-commit hook.

## Commands
```bash
source env.sh && source .venv/bin/activate
python3 -c "import freya,json; print(freya.save_workflow('base', json.load(open('examples/base-agent.json'))))"
python3 tools/run_cases.py <agent_id> --brief A            # 3–11 min. One simulation at a time per workspace
python3 builder/build.py briefs/brief-a.md tools/openapi.json
python3 builder/build.py briefs/brief-a.md briefs/brief-b.md tools/openapi.json
python3 -c "import freya; print(freya.get_call('<call_id>')['messages'])"   # transcript + tool calls + route_evaluated events
```
Never start `run_cases.py` in the background and walk away: it must be read. A 10-case run is 3–11 minutes. Use a long Bash timeout.

## Hard rules (organisers)
- One command, no manual step, never edit a phone agent on the platform by hand. The top entries are rebuilt from the commit and the trace is reviewed against the code.
- **Nothing from a hidden brief may be written into the builder**: no rule, value, name, holiday date, outcome name. After 17:00 UTC Sunday only crash/bug fixes. The builder must read a brief it has never seen: whatever can be taken from the brief must be taken from the brief, not hard-coded from Brief A/B.
- The phone agent may call only the bank's tool API (`tools/openapi.json` / the hidden brief's own file). Seven tool names stay the same; fields and allowed values can change.
- 30 minutes build time per brief including self-tests. 200 workflows per workspace: update in place. One Freya key.
- Traces must have: start/end time, every model call (model + one-line purpose), what was created on Freya (workflow id, agent id, steps, tools), tests run and results. Plain text. Remove API keys before committing.

## Things that bite (from the docs, the kit README and our own runs)
- **The chat route skips a first code node** (confirmed on the Brief A agent): the initial node must be a conversation node; compute facts in code nodes entered after the first customer turn. Simulations run the first node; the chat route (smoke tests, local simulator) does not.
- An agent built for Brief A+B fails Brief A's practice cases that expect no `add_note` (B requires notes): the practice set mixes two rule sets; hidden briefs have one. Score the A+B agent on B's cases.
- Three model calls per turn: extraction → routing → dialogue. Routing reads only transition descriptions/conditions, never `task_message`. Deterministic conditions (`equals`, `is_set`, counters) run in code and need no model.
- `tools` only on `conversation` nodes, `pre_actions` only on `api_request`/`code` nodes; the platform silently strips the wrong one. `response_mapping` on the tool for `tools`, on the node for `pre_actions`. Mapping paths start with `data.`.
- Fixed values use `default` (baked), never `const`. A model-filled body field is a leaf under `body.properties.<field>` with `default: "{{<field>}}"` where no such variable exists. `customer_id` is baked from the call variable.
- Booleans arrive as strings: test both `"true"` and `"True"`, or route on string flags written by code. Never put `null` in a workflow.
- Routing runs again after a tool result; a transition on a tool-result variable fires in the same turn. Counters: `<tool>_success_count`, `<tool>_failure_count`.
- After a tool call the model may say nothing (customer hangs up) or ignore a negative result: add a `post_process_code` hook that writes a `what_to_do_next` line into `result['data']`, and say in the prompt: after every tool result, speak or call the next tool.
- Code nodes: read/write `vars`, never raise (wrap in try/except), no `{{`/`}}` in code, `json`/`re`/`datetime` available. Do date maths (business days, deadlines, "next Friday") in code and hand the model finished facts as text. `now` is a call variable; never use the real clock.
- Every passthrough node ends with an `always` transition. Every path reaches an `end_call` node. `end_call` nodes: `on_enter` silent, farewell in the terminal's `spoken_message`, `endedReason` = the terminal's `function.name`.
- `close_call` must be the last tool call of every call, exactly once. `create_promise` only after a clear yes; say "recorded" only after `ok: true`; retry once on failure, then `service_error`.
- `freya.save_workflow` publishes; a bare PUT does not, and simulations run the published version. Leave `agent_config` out of the workflow you send.
- Product ids come from `get_account` (`p1`, `p2`, ...); the model makes ids up unless they are in the tool result or filled by code.
- Chat route `POST /api/v2/chat/message` is the fast way to see the first turns without a simulation (needed for hidden briefs, which have no practice cases).
- Scores vary run to run; a slow model (median slowest turn > 10 s) lowers a score. Prefer rules in routes and code over rules in prompts.

## Conventions
- Python 3.10+, standard library in anything the organisers run; the Claude Agent SDK only inside `builder/`.
- Commit traces and `submission/*.workflow.json`; never `env.sh`, `.freya-agents.json`, `.personas.json`, `results/`.
- Keep the kit files (`briefs/`, `tools/openapi.json`, `public-test-set.json`, `docs/*.md`, `freya.py`, `tools/run_cases.py`, `tools/score.py`, `examples/`) as shipped so a newer kit version can be diffed in. The original zip is in `kit-archive/`.
