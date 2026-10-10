#!/usr/bin/env python3
"""Builder entry point for the Build the Builder hackathon. One command, a brief in, a phone agent out.

    source env.sh
    python3 builder/build.py briefs/brief-a.md tools/openapi.json
    python3 builder/build.py briefs/brief-a.md briefs/brief-b.md tools/openapi.json     # Brief B builds on A: pass both
    python3 builder/build.py briefs/hidden-1.md briefs/hidden-1.openapi.json 2>&1 | tee traces/hidden-1.console.log

Every argument ending in .md is a brief; the argument ending in .json is the bank's tool API file.
The slot (and the name of every output file) is the file name of the last brief without .md.
Options: --cases <file> (practice cases to test against; auto-detected for the kit and synthetic briefs, none for
hidden briefs), --runner sim|freya (local simulator or the organisers' simulation; default sim), --minutes N (budget,
default 29), --no-rules / --no-audit / --no-gen-cases to skip those steps, --gen-cases to generate rule-branch cases
even when a cases file exists (they are then an extra set; the given file stays the practice set).

One run, with no manual step:
  1. rules:    builder/rules.py extracts the rule inventory of the brief(s) -> out/<slot>.rules.json, .spec.json, .rules.conflicts.md
              (3 samples x 2 parallel calls, a merge, dated decisions and verification: about 1.5-3 minutes)
     cases:    at the same time (thread), when the brief has no practice cases: builder/cases.py, an independent case
               writer, generates 12-20 rule-branch cases -> out/<slot>.cases.json (the building agent never writes its
               own tests; it never reads the .rationale.md). Brief rule numbers in the cases are mapped to inventory ids
               once both are done.
  2. build:    Claude (Claude Agent SDK) with the `build-phone-agent` skill writes out/gen_<slot>.py on builder/freyalib,
               generates out/<slot>.workflow.json, lints, dry-runs, saves it on Freya (freya.save_workflow), smoke-tests it
               over the chat route, audits rule coverage, runs the practice cases when there are any, and fixes what fails
  3. verify:   builder/lint.py on the final workflow, builder/audit.py coverage summary (evidence for the trace)
  4. export:   freya.export_workflow -> submission/<slot>.workflow.json (what gets scored)
  5. trace:    traces/<slot>.log (plain text: start/end, every model call, tests, what was created) + traces/<slot>.jsonl

Needs FREYA_API_KEY and FREYA_BANK_TEAM_KEY (env.sh), a Claude login or ANTHROPIC_API_KEY; OPENAI_API_KEY for the
local simulator's customer/judge models (otherwise it falls back to the Claude CLI).
BUILDER_MODEL sets the builder's own model (default claude-opus-5-5). The phone agent's model is fixed in freya.py.
"""
import asyncio, dataclasses, json, os, pathlib, re, subprocess, sys, threading, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SKILL = "build-phone-agent"
DEFAULT_BUILDER_MODEL = "claude-opus-5-5"
PY = sys.executable


def scrub(text):
    """Remove API keys and the team key from anything that goes into a trace."""
    text = re.sub(r"fak_[A-Za-z0-9_\-]{8,}", "fak_***", text)
    text = re.sub(r"sk-[A-Za-z0-9_\-]{12,}", "sk-***", text)
    for name in ("FREYA_API_KEY", "FREYA_BANK_TEAM_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
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
        self.lock = threading.Lock()

    def line(self, msg):
        s = "[%s +%5.0fs] %s" % (time.strftime("%H:%M:%S"), time.time() - self.t0, scrub(msg))
        with self.lock:
            self.log.write(s + "\n"); self.log.flush(); print(s, flush=True)

    def raw(self, obj):
        self.jsonl.write(scrub(json.dumps(obj, default=str)) + "\n"); self.jsonl.flush()

    def elapsed_min(self):
        return (time.time() - self.t0) / 60

    def close(self):
        self.log.close(); self.jsonl.close()


NO_CREDENTIAL = []   # steps that failed for lack of a Claude credential (fail fast, see run_step)


def run_step(trace, name, cmd, timeout):
    """Run a helper script, copy its 'model call' lines and summary into the trace, return (returncode, stdout)."""
    trace.line("step %s: %s" % (name, " ".join(cmd)))
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        partial = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        for l in partial.splitlines():
            if "model call" in l: trace.line(l.strip())
        trace.line("step %s: TIMEOUT after %d s" % (name, timeout)); return 1, ""
    for l in (p.stderr or "").splitlines():
        if "model call" in l: trace.line(l.strip())
    if "Not logged in" in (p.stderr or "") or "Invalid API key" in (p.stderr or ""):
        trace.line("FATAL step %s: no Claude credential. Set ANTHROPIC_API_KEY or run `claude login` on this machine, then rerun." % name)
        NO_CREDENTIAL.append(name)
    out = (p.stdout or "").strip()
    tail = out.splitlines()[-3:] if out else []
    trace.line("step %s: exit %d%s" % (name, p.returncode, (" | " + " | ".join(t.strip()[:160] for t in tail)) if tail else ""))
    if p.returncode != 0 and p.stderr:
        trace.line("step %s stderr: %s" % (name, " ".join(p.stderr.split())[-400:]))
    return p.returncode, out


def detect_cases(briefs):
    """Practice cases for the kit's and the synthetic briefs; none for a hidden brief."""
    last = pathlib.Path(briefs[-1])
    if last.resolve() == (ROOT / "briefs" / "brief-a.md").resolve(): return str(ROOT / "public-test-set.json"), "A"
    if last.resolve() == (ROOT / "briefs" / "brief-b.md").resolve(): return str(ROOT / "public-test-set.json"), "B"
    cand = last.with_name(last.stem + ".cases.json")
    if cand.exists(): return str(cand), None
    return None, None


async def run_claude(briefs, tool_api, slot, trace, cases, brief_filter, runner, minutes_left, generated=None):
    from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, ToolResultBlock,
                                  ToolUseBlock, UserMessage, query)
    model = os.environ.get("BUILDER_MODEL", DEFAULT_BUILDER_MODEL)
    options = ClaudeAgentOptions(
        cwd=str(ROOT), model=model, skills=[SKILL], setting_sources=["project"],
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"], permission_mode="dontAsk", max_turns=200,
        env={"BASH_DEFAULT_TIMEOUT_MS": "900000", "BASH_MAX_TIMEOUT_MS": "1200000", "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"},
    )
    gen_line = ""
    if generated and generated == cases:
        runner = "sim"   # generated cases reuse mock customers (mock_case) and other dates: only builder/sim.py runs them
        gen_line = (" These practice cases were GENERATED from the brief by an independent case writer (builder/cases.py), not by "
                    "the organisers: each carries expected_confidence and rule_ids. Run them once (skill step 9, repair round for "
                    "generated cases: --concurrency 2, fix only deterministic agent errors, never on a low/medium-confidence "
                    "expectation, at most 2 rounds). Do not read out/%s.cases.rationale.md." % slot)
    elif generated:
        gen_line = (" Extra generated rule-branch cases (independent case writer, sim.py only): %s; use them only if time is "
                    "left after the practice cases, under skill step 9's rules for generated cases." % generated)
    test_line = ("No practice cases exist for this brief: test with lint, dry run, the smoke scripts and the audit only."
                 if not cases else
                 "Practice cases: %s%s. Test runner: %s (%s)." % (cases, (" --brief " + brief_filter) if brief_filter else "", runner,
                 "python3 builder/sim.py <slot> --cases <file>%s --concurrency 3 (the chat route answers 504 above that)" % ((" --brief " + brief_filter) if brief_filter else "")
                 if runner == "sim" else "python3 tools/run_cases.py <agent_id> --cases <file>%s" % ((" --brief " + brief_filter) if brief_filter else "")))
    deadline = time.strftime("%H:%M:%S", time.localtime(time.time() + minutes_left * 60))
    prompt = ("Use the %s skill to build a phone agent. Brief file(s): %s. Tool API file: %s. Slot name: %s. "
              "The rule inventory is at out/%s.rules.json (and .md); resolve out/%s.rules.conflicts.md first; the structured values "
              "are in out/%s.spec.json. %s%s Time budget: %d minutes from now (stop by %s local "
              "time; check `date` before starting a test round) for everything, including your own tests; save a working "
              "agent early and improve it." % (SKILL, " ".join(briefs), tool_api, slot, slot, slot, slot, test_line, gen_line, int(minutes_left), deadline))
    trace.line("model call: %s | purpose: build, test and fix the phone agent from the brief | prompt: %s" % (model, prompt))
    async for message in query(prompt=prompt, options=options):
        trace.raw({"type": type(message).__name__, **dataclasses.asdict(message)})
        if isinstance(message, AssistantMessage):
            m = getattr(message, "model", None) or model
            for block in message.content:
                if isinstance(block, TextBlock):
                    text = block.text.strip(); first = text.splitlines()[0] if text else ""
                    if first: trace.line("model call: %s | says: %s" % (m, first[:220]))
                elif isinstance(block, ToolUseBlock):
                    arg = block.input.get("command") or block.input.get("file_path") or block.input.get("pattern") or ""
                    trace.line("model call: %s | tool %s | %s" % (m, block.name, " ".join(str(arg).split())[:220]))
        elif isinstance(message, UserMessage) and isinstance(message.content, list):
            for block in message.content:
                if isinstance(block, ToolResultBlock):
                    text = block.content if isinstance(block.content, str) else json.dumps(block.content, default=str)
                    hits = [l.strip() for l in text.splitlines() if re.match(r"\s*(PASS|FAIL|RESULT:|ERROR|WARN)\b", l) or " passed" in l or "workflow_id" in l or "implemented" in l]
                    if hits: trace.line("test/tool result: " + " | ".join(h[:160] for h in hits[:24]))
        elif isinstance(message, ResultMessage):
            trace.line("agent run done: %s turns, %.0f s, $%.2f" % (message.num_turns, message.duration_ms / 1000, message.total_cost_usd or 0))


def export(slot, trace):
    """Export the phone agent exactly as it is on Freya. This file is what gets scored."""
    import freya
    f = ROOT / ".freya-agents.json"
    state = json.loads(f.read_text()) if f.exists() else {}
    if slot not in state:
        trace.line("ERROR: no workflow saved for slot %r (not in .freya-agents.json). Nothing exported." % slot); return None
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
    opts = {"--cases": None, "--runner": "sim", "--minutes": "29"}; flags = set()
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in opts and i + 1 < len(argv): opts[a] = argv[i + 1]; i += 2; continue
        if a in ("--no-rules", "--no-audit", "--no-gen-cases", "--gen-cases"): flags.add(a); i += 1; continue
        args.append(a); i += 1
    briefs = [a for a in args if a.lower().endswith(".md")]
    apis = [a for a in args if a.lower().endswith(".json")]
    if len(apis) == 1: tool_api = apis[0]
    elif not apis and len(args) >= 2: briefs, tool_api = args[:-1], args[-1]
    else: sys.exit(__doc__)
    if not briefs: sys.exit(__doc__)
    for p in briefs + [tool_api]:
        if not pathlib.Path(p).exists(): sys.exit("not found: " + p)
    for k in ("FREYA_API_KEY", "FREYA_BANK_TEAM_KEY"):
        if not os.environ.get(k) or os.environ[k].endswith("your_key_here"): sys.exit(k + " is not set. source env.sh first.")
    budget = float(opts["--minutes"]); slot = pathlib.Path(briefs[-1]).stem
    cases, brief_filter = (opts["--cases"], None) if opts["--cases"] else detect_cases(briefs)
    trace = Trace(slot)
    trace.line("build start %s | briefs=%s tool_api=%s slot=%s | cases=%s runner=%s budget=%.0f min | builder model=%s | phone agent model=%s"
               % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), briefs, tool_api, slot, cases, opts["--runner"], budget, os.environ.get("BUILDER_MODEL", DEFAULT_BUILDER_MODEL), os.environ.get("FREYA_AGENT_MODEL", "experimental-5")))
    (ROOT / "out").mkdir(exist_ok=True)
    # rules and generated cases run at the same time (T31); the case writer reads the brief itself (independent reader)
    gen_cases = None
    want_cases = "--no-gen-cases" not in flags and (not cases or "--gen-cases" in flags)
    rules_out = "out/%s.rules.json" % slot
    cases_out = "out/%s.cases.json" % slot
    jobs = []
    if "--no-rules" not in flags:
        jobs.append(threading.Thread(target=run_step, args=(trace, "rules", [PY, "builder/rules.py", *briefs, "--api", tool_api, "--out", rules_out], 420)))
    if want_cases:
        (ROOT / cases_out).unlink(missing_ok=True)
        cmd = [PY, "builder/cases.py", "--brief", *briefs, "--api", tool_api, "--out", cases_out]
        if "--no-rules" in flags and (ROOT / rules_out).exists():
            cmd += ["--rules", rules_out]
        jobs.append(threading.Thread(target=run_step, args=(trace, "cases", cmd, 420)))
    for j in jobs: j.start()
    for j in jobs: j.join()
    if want_cases and (ROOT / cases_out).exists():
        if (ROOT / rules_out).exists():
            run_step(trace, "cases-map", [PY, "builder/cases.py", "--map-rules", cases_out, "--rules", rules_out], 60)
        rc, _ = run_step(trace, "cases-check", [PY, "builder/cases.py", "--check", cases_out, "--api", tool_api], 60)
        gen_cases = str(ROOT / cases_out)
        if not cases:
            cases, brief_filter = gen_cases, None
    elif want_cases:
        trace.line("cases: no generated cases file; the build runs without practice cases")
    if NO_CREDENTIAL:
        trace.line("build end %s | ABORTED: no Claude credential (steps %s)" % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), NO_CREDENTIAL))
        trace.close()
        return 2
    try:
        left = budget - trace.elapsed_min() - 3          # keep 3 minutes for verify + export
        await asyncio.wait_for(run_claude(briefs, tool_api, slot, trace, cases, brief_filter, opts["--runner"], left, generated=gen_cases), timeout=max(60, left * 60))
    except asyncio.TimeoutError:
        trace.line("STOPPED: the build budget was reached. Verifying and exporting whatever is saved on Freya.")
    except Exception as e:
        trace.line("ERROR in the agent run: %r" % (e,))
    wf_path = ROOT / "out" / ("%s.workflow.json" % slot)
    if wf_path.exists():
        rules_file = ROOT / "out" / ("%s.rules.json" % slot)
        lint_cmd = [PY, "builder/lint.py", str(wf_path), "--api", tool_api] + (["--rules", str(rules_file), "--budget"] if rules_file.exists() else [])
        try:   # the call variables every call carries: the practice cases name them (no test_variables are shipped)
            cs = json.load(open(cases)) if cases else []
            cs = cs.get("cases", cs) if isinstance(cs, dict) else cs
            names = sorted({"customer_id"} | set((cs[0].get("variables") or {}).keys())) if cs else []
            if names:
                lint_cmd += ["--call-vars", ",".join(names)]
        except Exception:
            pass
        run_step(trace, "lint", lint_cmd, timeout=max(30, min(120, int((budget - trace.elapsed_min() - 1) * 60))))
        # the audit only when it cannot push the trace's end past the budget (worst case was 34 min before this guard)
        left_min = budget - trace.elapsed_min()
        if "--no-audit" not in flags and rules_file.exists() and left_min > 7:
            gen = ROOT / "out" / ("gen_%s.py" % slot)
            run_step(trace, "audit", [PY, "builder/audit.py", "--rules", str(rules_file), "--workflow", str(wf_path),
                                      "--generator", str(gen) if gen.exists() else "", "--out", "out/%s.audit.json" % slot],
                     timeout=int(min(360, (left_min - 1.5) * 60)))
        elif "--no-audit" not in flags:
            trace.line("audit skipped: %.1f minutes left of the %d-minute budget" % (left_min, budget))
    try:
        export(slot, trace)
    except Exception as e:
        trace.line("ERROR exporting the workflow: %r" % (e,))
    trace.line("build end %s | total %.0f s" % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), time.time() - trace.t0))
    trace.close()
    # keep every run: traces/<slot>.log is the latest run (what the form points at); a timestamped copy keeps the earlier ones
    import shutil
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(trace.t0))
    for ext in ("log", "jsonl"):
        src = ROOT / "traces" / ("%s.%s" % (slot, ext))
        if src.exists(): shutil.copy(src, ROOT / "traces" / ("%s-%s.%s" % (slot, stamp, ext)))
    print("trace: traces/%s.log (copy traces/%s-%s.log)" % (slot, slot, stamp))


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])) or 0)
