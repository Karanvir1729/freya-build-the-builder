#!/usr/bin/env python3
"""Builder entry point for the Build the Builder hackathon. One command, a brief in, a phone agent out.

    source env.sh
    python3 builder/build.py briefs/brief-a.md tools/openapi.json
    python3 builder/build.py briefs/brief-a.md briefs/brief-b.md tools/openapi.json    # Brief B builds on A: pass both
    python3 builder/build.py briefs/hidden-1.md briefs/hidden-1.openapi.json 2>&1 | tee traces/hidden-1.console.log

Every argument ending in .md is a brief; the argument ending in .json is the bank's tool API file.
The slot (and the name of every output file) is the file name of the last brief without .md.

What one run does, with no manual step:
  1. runs Claude through the Claude Agent SDK with the `build-phone-agent` skill on the brief(s) and the tool API file.
     Claude writes out/<slot>.workflow.json, saves it on Freya with freya.save_workflow(<slot>, ...), runs the practice
     cases when the brief has any, and fixes what fails.
  2. exports the phone agent as it is on Freya to submission/<slot>.workflow.json (what gets scored).
  3. writes the trace: traces/<slot>.log (plain text: start/end time, every model turn and tool call in one line, test
     results, what was created on Freya) and traces/<slot>.jsonl (every SDK message). API keys are scrubbed from both.

Needs FREYA_API_KEY and FREYA_BANK_TEAM_KEY (env.sh) and a Claude login or ANTHROPIC_API_KEY.
BUILDER_MODEL sets the builder's own model (default claude-opus-5-5). The phone agent's model is fixed in freya.py.
"""
import asyncio, dataclasses, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SKILL = "build-phone-agent"
BUILD_TIME_LIMIT_S = 29 * 60          # the rules allow 30 minutes per brief, self-tests included
DEFAULT_BUILDER_MODEL = "claude-opus-5-5"


def scrub(text):
    """Remove API keys and the team key from anything that goes into a trace."""
    text = re.sub(r"fak_[A-Za-z0-9_\-]{8,}", "fak_***", text)
    for name in ("FREYA_API_KEY", "FREYA_BANK_TEAM_KEY", "ANTHROPIC_API_KEY"):
        v = os.environ.get(name)
        if v and len(v) >= 8:
            text = text.replace(v, "<" + name + ">")
    return text


class Trace:
    def __init__(self, slot):
        d = ROOT / "traces"; d.mkdir(exist_ok=True)
        self.t0 = time.time()
        self.log = (d / (slot + ".log")).open("w")
        self.jsonl = (d / (slot + ".jsonl")).open("w")

    def line(self, msg):
        s = "[%s +%5.0fs] %s" % (time.strftime("%H:%M:%S"), time.time() - self.t0, scrub(msg))
        self.log.write(s + "\n"); self.log.flush(); print(s, flush=True)

    def raw(self, obj):
        self.jsonl.write(scrub(json.dumps(obj, default=str)) + "\n"); self.jsonl.flush()

    def close(self):
        self.log.close(); self.jsonl.close()


async def run_claude(briefs, tool_api, slot, trace):
    from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, ToolResultBlock,
                                  ToolUseBlock, UserMessage, query)
    model = os.environ.get("BUILDER_MODEL", DEFAULT_BUILDER_MODEL)
    options = ClaudeAgentOptions(
        cwd=str(ROOT),
        model=model,
        skills=[SKILL],                        # .claude/skills/build-phone-agent
        setting_sources=["project"],           # only this repo's settings, not the user's
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="dontAsk",             # anything not listed above is refused
        max_turns=150,
        # A test run takes up to 11 minutes. Let a command run that long, in the foreground: the builder stops when
        # Claude ends its turn, so a test left in the background is never read.
        env={"BASH_DEFAULT_TIMEOUT_MS": "900000", "BASH_MAX_TIMEOUT_MS": "1200000", "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"},
    )
    prompt = ("Use the %s skill to build a phone agent. Brief file(s): %s. Tool API file: %s. Slot name: %s."
              % (SKILL, " ".join(briefs), tool_api, slot))
    trace.line("model call: %s | purpose: build, test and fix the phone agent from the brief | prompt: %s" % (model, prompt))
    async for message in query(prompt=prompt, options=options):
        trace.raw({"type": type(message).__name__, **dataclasses.asdict(message)})
        if isinstance(message, AssistantMessage):
            m = getattr(message, "model", None) or model
            for block in message.content:
                if isinstance(block, TextBlock):
                    text = block.text.strip()
                    first = text.splitlines()[0] if text else ""
                    if first: trace.line("model call: %s | says: %s" % (m, first[:220]))
                elif isinstance(block, ToolUseBlock):
                    arg = block.input.get("command") or block.input.get("file_path") or block.input.get("pattern") or ""
                    trace.line("model call: %s | tool %s | %s" % (m, block.name, " ".join(str(arg).split())[:220]))
        elif isinstance(message, UserMessage) and isinstance(message.content, list):
            for block in message.content:
                if isinstance(block, ToolResultBlock):
                    text = block.content if isinstance(block.content, str) else json.dumps(block.content, default=str)
                    hits = [l.strip() for l in text.splitlines() if re.match(r"\s*(PASS|FAIL)\b", l) or " passed" in l or "workflow_id" in l]
                    if hits: trace.line("test/tool result: " + " | ".join(h[:160] for h in hits[:24]))
        elif isinstance(message, ResultMessage):
            trace.line("agent run done: %s turns, %.0f s, $%.2f" % (message.num_turns, message.duration_ms / 1000, message.total_cost_usd or 0))


def export(slot, trace):
    """Export the phone agent exactly as it is on Freya. This file is what gets scored."""
    import freya
    f = ROOT / ".freya-agents.json"
    state = json.loads(f.read_text()) if f.exists() else {}
    if slot not in state:
        trace.line("ERROR: no workflow saved for slot %r (not in .freya-agents.json). Nothing exported." % slot)
        return None
    wid, aid = state[slot]["workflow_id"], state[slot]["agent_id"]
    out = ROOT / "submission" / (slot + ".workflow.json"); out.parent.mkdir(exist_ok=True)
    freya.export_workflow(wid, str(out))
    wf = json.loads(out.read_text())["workflow"]
    nodes = wf.get("nodes") or {}
    n_tools = sum(len(n.get("tools") or []) for n in nodes.values()) + len(wf.get("tools") or [])
    trace.line("created on Freya: workflow_id=%s agent_id=%s published_version=%s | %d steps (%s), %d global nodes, %d tools | exported to %s"
               % (wid, aid, state[slot].get("version", 1), len(nodes), ", ".join(nodes), len(wf.get("global_nodes") or {}), n_tools, out.relative_to(ROOT)))
    return out


async def main(argv):
    briefs = [a for a in argv if a.lower().endswith(".md")]
    apis = [a for a in argv if a.lower().endswith(".json")]
    if len(apis) == 1:
        tool_api = apis[0]
    elif not apis and len(argv) >= 2:
        briefs, tool_api = argv[:-1], argv[-1]
    else:
        sys.exit(__doc__)
    if not briefs:
        sys.exit(__doc__)
    for p in briefs + [tool_api]:
        if not pathlib.Path(p).exists(): sys.exit("not found: " + p)
    for k in ("FREYA_API_KEY", "FREYA_BANK_TEAM_KEY"):
        if not os.environ.get(k) or os.environ[k].endswith("your_key_here"): sys.exit(k + " is not set. source env.sh first.")
    slot = pathlib.Path(briefs[-1]).stem
    trace = Trace(slot)
    trace.line("build start %s | briefs=%s tool_api=%s slot=%s | builder model=%s"
               % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), briefs, tool_api, slot, os.environ.get("BUILDER_MODEL", DEFAULT_BUILDER_MODEL)))
    try:
        await asyncio.wait_for(run_claude(briefs, tool_api, slot, trace), timeout=BUILD_TIME_LIMIT_S)
    except asyncio.TimeoutError:
        trace.line("STOPPED: the %d-minute build limit was reached. Exporting whatever is saved on Freya." % (BUILD_TIME_LIMIT_S // 60))
    except Exception as e:
        trace.line("ERROR in the agent run: %r" % (e,))
    try:
        export(slot, trace)
    except Exception as e:
        trace.line("ERROR exporting the workflow: %r" % (e,))
    trace.line("build end %s | total %.0f s" % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), time.time() - trace.t0))
    trace.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
