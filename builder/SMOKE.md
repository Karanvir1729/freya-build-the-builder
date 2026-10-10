# builder/smoke.py — chat-route smoke tests for a published workflow

`builder/smoke.py` talks to a published Freya workflow over `POST /api/v2/chat/message`, one turn at a time, with no
simulation and no queue (docs/api.md, "Talk to your workflow turn by turn"). A turn answers in seconds, so this is the
fastest way to see what a phone agent says first, whether it routes where it should, and which tools it calls, before a
3–11 minute simulation. It is standard library only, except the optional driven mode. It never edits a workflow.

```bash
source env.sh
# scripted: fixed customer lines plus expectations; exit 1 when an expectation fails
python3 builder/smoke.py <workflow_id|slot> --script builder/smoke_scripts/opening.json
python3 builder/smoke.py brief-a --script builder/smoke_scripts/third_party.json --out results/smoke-third_party.json
# driven: a Claude-played customer follows a persona; no pass/fail, a transcript to read
python3 builder/smoke.py brief-a --customer "You are Daniel Reyes, born 14 March 1988, phone ending 4471. You can pay the full amount today." --max-turns 12
python3 builder/smoke.py brief-a --case PUB-01 --max-turns 12          # persona and variables from a practice case
```

`<workflow_id|slot>` is a workflow id or a slot name from `.freya-agents.json` (`brief-a`, `brief-b`, ...). The
workflow must be published: `freya.save_workflow` publishes, a bare PUT does not.

## What one run prints

```
--- turn 1
customer: Hello?
agent (1.4s): Hello, this is Freya Bank's digital assistant. Please note that we record this call. Am I speaking with Mr Reyes?
   [route] setup -> opening: always always
   [node] setup -> opening (always always)
--- turn 2
customer: Yes, this is me
agent (2.7s): To start, could you please tell me your date of birth, Mr Reyes?
   [extract] who1 = 'customer'
   [route] opening -> ask_dob: the customer confirmed who they are who1 == 'customer'
--- POST /api/v2/chat/end -> {"callId": "...", "ended": true, "endedReason": "customer-ended-call"}
== tool calls (1) from GET /api/v2/call/<callId>
 1. turn 3  schedule_callback  POST https://freya-bank-mock.../v1/schedule_callback body={"customer_id": "c_smoke", "date": "2026-10-15", "time": "11:00"}
    -> HTTP 404 data={"error": "unknown customer"}
== variables after the last routing (6): {"now": ..., "who1": "customer"}
NOTE: the first node 'setup' is a code node that writes deadline, ...; deadline, ... never appeared in the variable table. ...
== expectations (26)
 PASS turn 1 contains_any ["Freya Bank"] -> 'Freya Bank'
 ...
RESULT: PASS | 26/26 checks passed | call <callId>
```

After every turn the harness reads `GET /api/v2/call/{callId}` and prints the engine events of that turn, one line each:
`[node]` node_enter, `[route]` route_evaluated (the matched transition and its reason, or "stays in"), `[extract]`
variable_extracted, `[tool]` function_call_start (method, url, body) and function_call_complete (HTTP status, `data`),
`[error]`. The tool-call summary at the end lists every tool call with its request body and result. `--out` writes
the same record as JSON (turns, events, tool calls, checks, variable table). API keys and the bank team key are
scrubbed from everything printed.

## Script format (scripted mode)

```json
{
 "name": "opening: identity before any debt talk",
 "variables": {"customer_id": "c_smoke", "first_name": "Daniel", "last_name": "Reyes", "title": "Mr", "now": "2026-10-14T11:00"},
 "turns": ["Hello?", "Yes, this is me"],
 "expect": [
  {"after_turn": 1, "contains_any": ["Freya Bank"], "not_contains": ["debt", "collection", "payment", "re:\\blate\\b"]},
  {"after_turn": 2, "cumulative": true, "not_contains": ["debt", "payment"]},
  {"after_turn": 2, "contains_any": ["date of birth", "re:\\bborn\\b", "postcode"], "no_tool_calls": true},
  {"tools_not_called": ["get_account", "create_promise"]},
  {"tools_called_any": ["close_call"]}
 ]
}
```

| Key | Meaning |
|---|---|
| `variables` | The call variables. Merged over the defaults (`c_smoke`, Daniel Reyes, `now` 2026-10-14T11:00); `--case PUB-02` and `--vars '{...}'` merge on top. |
| `turns` | The customer's lines, sent in order. Sending stops when the agent ends the call (`endedByAgent`). |
| `after_turn` | 1-based: check the agent's reply to that customer line. Absent: check all replies together. |
| `cumulative` | With `after_turn`: check all replies up to and including that turn (for "never before identity" rules). |
| `contains_any`, `contains_all`, `not_contains` | Case-insensitive substrings. A term starting with `re:` is a case-insensitive regex, e.g. `re:\\blate\\b` so that "later" does not count. |
| `no_tool_calls`, `tools_called_any`, `tools_not_called` | Tool names from the call's events (`verify_identity`, `close_call`, ...), up to `after_turn` when given. |

Exit codes: 0 every check passed, 1 a check failed (a turn with no reply fails its checks), 2 the call could not be
run (a 500, no answer, or a 504 on the first turn after two retries).

The three scripts in `builder/smoke_scripts/` are generic: any collections brief must pass them, nothing in them
comes from a brief.

| Script | Customer lines | Checks |
|---|---|---|
| `opening.json` | "Hello?", "Yes, this is me" | Names Freya Bank and the customer; no debt/collections/payment/amount/product words before identity; asks a security question; no tool call yet. |
| `third_party.json` | "Hello?", "This is her husband, she is not here. What is this about?", "She should be back tomorrow morning, around eleven." (PUB-02 variables) | Nothing about the account or why it calls; asks when she can be reached; `verify_identity`, `get_account`, `create_promise` never called. The third line usually makes the agent call `schedule_callback`, so the tool-call path is exercised too. |
| `wrong_number.json` | "Hello?", "I think you have the wrong number, nobody by that name here." | No debt words; closes politely; `close_call` is called and no identity or promise tool is. |

## The mock bank and `c_smoke`

The scripts use `customer_id` `c_smoke`, which the mock bank does not know, so every tool call the agent makes is
rejected by the mock (printed as `[tool] <name> -> HTTP 4xx ...`). That is fine for the opening turns: the point is the
conversation before any bank call. To test tool calls for real, start a practice session and pass its variables:

```bash
python3 -c "import sys; sys.path.insert(0, 'tools'); from score import http; import json; print(json.dumps(http('/v1/practice/sessions', {'case': 'PUB-01'})['variables']))"
python3 builder/smoke.py brief-a --script my_script.json --vars '<that JSON>'
```

`tools/score.py http('/v1/practice/ledger/<customer_id>')` then shows what the bank recorded.

## Driven mode

`--customer "<persona text>"` lets a Claude-played customer talk to the agent for up to `--max-turns` lines
(default 12, first line `--opening`, default "Hello?"). The customer model is `--model` (default `claude-haiku-5-5`)
through the Claude Agent SDK (`.venv`), or `claude -p` when the SDK is not importable; it needs a Claude login or
`ANTHROPIC_API_KEY`. The customer gets the persona, the transcript so far, and the rule to answer only what is asked;
it says `[HANGUP]` when the call is over. There is no judge and no pass/fail: the output is a transcript with tool
calls for a human or an auditor to read. With a real practice customer (see above) a driven run is a complete
end-to-end call: `--case PUB-01 --vars '<session variables>'`.

## What the chat route can and cannot test

Can:
- Whether the published workflow starts a call at all, what it says first, and how the opening turns go.
- Routing (`route_evaluated` shows every branch, the matched one and the reason), extraction (`variable_extracted`),
  node entry, and the variable table after each routing.
- Tool calls with their exact request body and the mock's answer, when a real practice `customer_id` is used.
- Phrasing rules on single turns (what is said before identity, security questions, third-party handling).

Cannot, or not reliably:
- **A first code node may be skipped.** Seen on the Brief A workflow: its initial node `setup` is a code node, and
  none of the variables it writes appeared in the variable table of the chat call; in a simulation they do. Values that
  the first step computes (deadlines, dates) are empty on the chat route, so anything that depends on them (date rules,
  prompts that read them) cannot be judged here. The harness prints a NOTE when it sees this. A workflow whose first
  node is a conversation node is not affected.
- **504 under load.** The gateway waits about 60 seconds. When the model is busy (a simulation running in the
  workspace, several chat calls at once) a turn returns 504 while the engine still finishes it. The harness then polls
  the call log for up to 60 s and uses the reply it finds there ("reply recovered from the call log"). A 504 on the
  first turn leaves no `callId`; the harness retries that turn twice, then stops with exit 2. A bare 500 on the first
  turn means the workflow cannot start a call at all (check `agent_config.llmConfig`; `freya.update_workflow` sets it).
- Run three scripts one after the other, not in parallel: parallel chat calls provoked the 504s above.
- No judge, no success criteria, no ledger scoring: the pass/fail here is substring checks on the agent's words and
  tool names. `tools/run_cases.py` remains the score.
- Timing is not representative: the chat route has no persona model and no audio, and a busy platform makes a 2 s
  turn take 15 s. Do not read speed from it.
- Call metadata differs from a simulation: `channel`/`direction` are `web`, `endedReason` after `POST /chat/end`
  is `customer-ended-call` even when the agent reached its end node, and `successCriteriaResult` is empty.
- It runs the published version only. After an update without publish you are still testing the old agent.
- The chat route uses the agent's configured model (`agent_config.llmConfig`, which `freya.update_workflow` keeps
  at `freya.AGENT_LLM`), not the per-simulation overrides.

## Files

- `builder/smoke.py` — the harness.
- `builder/smoke_scripts/opening.json`, `third_party.json`, `wrong_number.json` — generic scripts.
- `results/smoke-*.json` — `--out` records (gitignored with the rest of `results/`).
