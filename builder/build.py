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
even when a cases file exists (they are then an extra set; the given file stays the practice set), --keep-builder-edits
to leave the agent's edits to the builder's own files in place (development only), --allow-parallel to run beside another
build from the same checkout (each agent then sees the other's library edits; otherwise refused).

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

  6. guards:   (builder/buildguard.py) the newest version must be published on the event's agent model; when the final
               version, re-tested, clearly lost cases against the version tested before it and gained none, that
               earlier version is saved again and shipped; every change to builder/, .claude/skills/, tools/ or
               freya.py during the run goes to out/<slot>-<stamp>.builder-edits.patch, and the ones the building agent
               made are put back (not when --keep-builder-edits is given, git HEAD moved, or another build runs from
               the same checkout; changes nobody can tie to the agent are reported and left alone); TURN_TAKING=1 sets a longer
               turn-taking wait after the last save (off by default: slower turns cost more than the fewer cut-offs gained)

Needs FREYA_API_KEY and FREYA_BANK_TEAM_KEY (env.sh), a Claude login or ANTHROPIC_API_KEY; OPENAI_API_KEY for the
local simulator's customer/judge models (otherwise it falls back to the Claude CLI).
BUILDER_MODEL sets the builder's own model for every step (default claude-fable-5-1, Anthropic's most capable model;
claude-opus-5-5 takes over when it is overloaded); BUILDER_EFFORT sets the building agent's effort (default high).
The phone agent's model is fixed in freya.py.
"""
import asyncio, dataclasses, json, os, pathlib, re, subprocess, sys, threading, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builder"))
import buildguard  # noqa: E402

SKILL = "build-phone-agent"
DEFAULT_BUILDER_MODEL = "claude-fable-5-1"
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL") or "claude-opus-5-5"      # when the builder model is overloaded (the Claude CLI's --fallback-model)
# the building agent's effort; the Claude CLI's default for claude-fable-5-1 is high (claude-opus-5-5: medium)
BUILDER_EFFORT = os.environ.get("BUILDER_EFFORT") or "high"
# rules and cases run in parallel before the agent: measured on Fable (Brief F, a mailbox) 309 s and 365 s at the default
# effort, against 173 s and 124 s on claude-opus-5-5
STEP_TIMEOUT = 540
AGENT_TOOL_USES = []                    # (tool name, input) of every tool call of the building agent (builder-edit guard)
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


async def run_claude(briefs, tool_api, slot, trace, cases, brief_filter, runner, minutes_left, generated=None, no_rules=False):
    from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, ToolResultBlock,
                                  ToolUseBlock, UserMessage, query)
    model = os.environ.get("BUILDER_MODEL") or DEFAULT_BUILDER_MODEL
    options = ClaudeAgentOptions(
        cwd=str(ROOT), model=model, fallback_model=FALLBACK_MODEL if model != FALLBACK_MODEL else None,
        effort=BUILDER_EFFORT, skills=[SKILL], setting_sources=["project"],
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"], permission_mode="dontAsk", max_turns=200,
        env={"BUILD_MODEL_LOG": os.environ.get("BUILD_MODEL_LOG", ""), "BASH_DEFAULT_TIMEOUT_MS": "900000", "BASH_MAX_TIMEOUT_MS": "1200000", "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"},
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
    test_line = ("No practice cases exist for this brief: test with lint, dry run, the smoke runs of the skill's \"Self-tests "
                 "without practice cases\" section and the audit only."
                 if not cases else
                 "Practice cases: %s%s. Test runner: %s (%s)." % (cases, (" --brief " + brief_filter) if brief_filter else "", runner,
                 "python3 builder/sim.py <slot> --cases <file>%s --concurrency 3 (the chat route answers 504 above that)" % ((" --brief " + brief_filter) if brief_filter else "")
                 if runner == "sim" else "python3 tools/run_cases.py <agent_id> --cases <file>%s" % ((" --brief " + brief_filter) if brief_filter else "")))
    deadline = time.strftime("%H:%M:%S", time.localtime(time.time() + minutes_left * 60))
    inventory = ("The rule inventory is at out/%s.rules.json (and .md); resolve out/%s.rules.conflicts.md first; the structured values "
                 "are in out/%s.spec.json." % (slot, slot, slot) if not no_rules else
                 "The rules step did not finish: there is no out/%s.rules.json or .spec.json. Do NOT run builder/rules.py (it takes "
                 "5-9 minutes): read the brief(s) and the tool API in full, build from them, and run lint without --rules." % slot)
    prompt = ("Use the %s skill to build a phone agent. Brief file(s): %s. Tool API file: %s. Slot name: %s. "
              "%s %s%s Time budget: %d minutes from now (stop by %s local "
              "time; check `date` before starting a test round) for everything, including your own tests; save a working "
              "agent early and improve it. A step you decide on is something to run now, not to announce: do not end your "
              "turn before step 10's finish line or the deadline." % (SKILL, " ".join(briefs), tool_api, slot, inventory, test_line, gen_line, int(minutes_left), deadline))
    if os.environ.get("BUILD_CASE_NOTE"):
        prompt += " " + os.environ["BUILD_CASE_NOTE"]
    if os.environ.get("BUILD_RESUME_NOTE"):
        prompt += " " + os.environ["BUILD_RESUME_NOTE"]
    t_start = time.time()
    t_end = t_start + minutes_left * 60

    async def consume(p, opts, purpose):
        trace.line("model call: %s | purpose: %s | prompt: %s" % (model, purpose, p))
        last_text, result = "", None
        async for message in query(prompt=p, options=opts):
            trace.raw({"type": type(message).__name__, **dataclasses.asdict(message)})
            if isinstance(message, AssistantMessage):
                m = getattr(message, "model", None) or model
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text.strip(); first = text.splitlines()[0] if text else ""
                        if text: last_text = text
                        if first: trace.line("model call: %s | says: %s" % (m, first[:220]))
                    elif isinstance(block, ToolUseBlock):
                        AGENT_TOOL_USES.append((block.name, dict(block.input or {})))
                        arg = block.input.get("command") or block.input.get("file_path") or block.input.get("pattern") or ""
                        trace.line("model call: %s | tool %s | %s" % (m, block.name, " ".join(str(arg).split())[:220]))
            elif isinstance(message, UserMessage) and isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, ToolResultBlock):
                        text = block.content if isinstance(block.content, str) else json.dumps(block.content, default=str)
                        hits = [l.strip() for l in text.splitlines() if re.match(r"\s*(PASS|FAIL|RESULT:|ERROR|WARN)\b", l) or " passed" in l or "workflow_id" in l or "implemented" in l]
                        if hits: trace.line("test/tool result: " + " | ".join(h[:160] for h in hits[:24]))
            elif isinstance(message, ResultMessage):
                result = message
                served = ", ".join(sorted((message.model_usage or {}).keys())) or model
                trace.line("agent run done: %s turns, %.0f s, $%.2f, served by %s" % (message.num_turns, message.duration_ms / 1000, message.total_cost_usd or 0, served))
        return last_text, result

    last_text, result = await consume(prompt, options, "build, test and fix the phone agent from the brief")
    # a long autonomous run can end on a sentence that announces the next step instead of running it: one continuation
    # in the same session while 4 minutes or more are left and step 10's finish line (workflow_id ...) was not written
    done = any(k in last_text.lower() for k in ("workflow_id", "agent_id", "workflow id"))
    if result is not None and not result.is_error and not done and time.time() < t_end - 240:
        left = int((t_end - time.time()) / 60)
        last_text, r2 = await consume("Continue the build: run the step you announced and the rest of the procedure, then finish with step 10's "
                                      "line. %d minutes are left (stop by %s local time)." % (left, deadline),
                                      dataclasses.replace(options, resume=result.session_id), "continue the build after a turn that ended early")
        result = r2 or result
    # time left unused (the ttau-bench lesson): a run that ends with practice cases still failing on the newest tested
    # version and 8+ minutes left gets one more round in the same session (Brief E on Sonnet stopped at 12 of 29 minutes
    # with 2 of 5 cases failing)
    failing = latest_failures(slot, t_start)
    audit_gap = audit_todo(slot, t_start) if not no_rules else ""
    if result is not None and not result.is_error and (failing or audit_gap) and time.time() < t_end - 480:
        left = int((t_end - time.time()) / 60)
        todo = []
        if failing:
            todo.append("On the newest tested version these practice cases still fail: %s. Under the skill's rules for repair "
                        "rounds: read each failure and fix the deterministic agent errors (never weaken a check or follow a "
                        "low/medium-confidence expectation against the brief), then re-run only those cases." % ", ".join(failing[:12]))
        if audit_gap:
            todo.append(audit_gap)
        await consume("%d minutes are left (stop by %s local time). %s Save, then finish with step 10's line." % (left, deadline, " ".join(todo)),
                      dataclasses.replace(options, resume=result.session_id), "use the time left: repair what is still failing")


def audit_todo(slot, since):
    """The skill's step 8 still owed: '' when the agent ran the audit in this build and it lists nothing contradicted or
    missing; otherwise one instruction."""
    f = ROOT / "out" / ("%s.audit.json" % slot)
    try:
        if not f.exists() or f.stat().st_mtime < since:
            return ("You have not run step 8 (the audit) in this build: run it now and fix every contradicted and missing rule "
                    "and the top fixes.")
        a = json.loads(f.read_text())
        bad = [r.get("id", "?") for r in a.get("rules") or [] if r.get("status") in ("contradicted", "missing")]
        return ("Your last audit lists contradicted or missing rules: %s. Fix each one from the brief (a rule a later dated "
                "decision replaces is not contradicted), regenerate and save." % ", ".join(bad[:15])) if bad else ""
    except Exception:
        return ""


def latest_failures(slot, since):
    """Case ids whose last run failed on the newest version tested since `since` (the per-case version ledger)."""
    try:
        st = load_state().get(slot) or {}
        res = buildguard.results_by_version(ROOT / "results" / "versions" / ("%s.jsonl" % st.get("workflow_id")), since=since)
        if not res:
            return []
        v = max(res)
        return sorted(c for c, runs in res[v].items() if runs and not runs[-1])
    except Exception:
        return []


def load_state():
    f = ROOT / ".freya-agents.json"
    return json.loads(f.read_text()) if f.exists() else {}


def check_version(slot, trace, t0):
    """After the agent run: the newest version published on the event's model, then the best tested version shipped.
    Returns True when an earlier version was saved again (out/<slot>.workflow.json is then that definition)."""
    import freya
    state = load_state()
    if slot not in state:
        trace.line("published check: no workflow saved for slot %r" % slot); return False
    wid = state[slot]["workflow_id"]
    state_file = ROOT / ".freya-agents.json"
    try:
        version, note = buildguard.retry5xx(lambda: buildguard.ensure_published(freya, wid), log=trace.line)
        trace.line("published check: " + note)
        buildguard.write_state_version(state_file, slot, version)
    except Exception as e:
        trace.line("published check failed: %r" % (e,)); return False
    results = buildguard.results_by_version(ROOT / "results" / "versions" / ("%s.jsonl" % wid), since=t0)
    for v in sorted(results):
        n = sum(len(x) for x in results[v].values()); p = sum(sum(x) for x in results[v].values())
        trace.line("tested version %d: %d of %d case runs passed (%d cases)" % (v, p, n, len(results[v])))
    ship, why = buildguard.choose_version(results, version)
    trace.line("best tested version: ship version %d (%s)" % (ship, why))
    if ship == version:
        return False
    new_v, wf = buildguard.retry5xx(lambda: buildguard.restore_version(freya, slot, wid, ship), log=trace.line)
    wf_path = ROOT / "out" / ("%s.workflow.json" % slot)
    if wf_path.exists():
        wf_path.replace(wf_path.with_name("%s.workflow.agent-final.json" % slot))
    wf_path.write_text(json.dumps(wf, indent=1))
    buildguard.write_state_version(state_file, slot, new_v)
    trace.line("restored: version %d saved again as version %d and published; out/%s.workflow.json is now that "
               "definition (the agent's final one is out/%s.workflow.agent-final.json)" % (ship, new_v, slot, slot))
    return True


def tune_turn_taking(slot, briefs, trace):
    """Opt-in (TURN_TAKING=1), after the last save: longer wait, smart turn off, the brief's language; published
    (buildguard). Off by default: on Brief A talkative (11 Oct) it cut fewer customer messages off (74% -> 50%) but
    every turn took ~4 s longer, the median slowest turn went 4.2 -> 13 s, PUB-07 ran past the 420 s call limit
    (45 messages in 424 s against 74 in 280 s) and the score went 9/10 -> 8/10."""
    import freya
    if os.environ.get("TURN_TAKING", "0") != "1":
        trace.line("turn-taking: platform defaults (TURN_TAKING=1 sets a longer wait)"); return
    state = load_state()
    if slot not in state:
        return
    try:
        files = [f for b in map(pathlib.Path, briefs) for f in (sorted(b.rglob("*")) if b.is_dir() else [b]) if f.is_file()]
        lang = buildguard.brief_language("\n".join(f.read_text(errors="ignore") for f in files))
        version, note = buildguard.retry5xx(lambda: buildguard.tune_turn_taking(freya, state[slot]["workflow_id"], lang), log=trace.line)
        trace.line("turn-taking: " + note)
        if version:
            buildguard.write_state_version(ROOT / ".freya-agents.json", slot, version)
    except Exception as e:
        trace.line("turn-taking not set, the platform defaults stay: %r" % (e,))


def export(slot, trace):
    """Export the phone agent exactly as it is on Freya. This file is what gets scored."""
    import freya
    state = load_state()
    if slot not in state:
        trace.line("ERROR: no workflow saved for slot %r (not in .freya-agents.json). Nothing exported." % slot); return None
    wid, aid = state[slot]["workflow_id"], state[slot]["agent_id"]
    out = ROOT / "submission" / (slot + ".workflow.json"); out.parent.mkdir(exist_ok=True)
    buildguard.retry5xx(lambda: freya.export_workflow(wid, str(out)), log=trace.line)
    wf = json.loads(out.read_text())["workflow"]
    nodes = wf.get("nodes") or {}
    n_tools = sum(len(n.get("tools") or []) for n in nodes.values()) + len(wf.get("tools") or [])
    trace.line("created on Freya: workflow_id=%s agent_id=%s published_version=%s | %d steps (%s), %d global nodes, %d tools | exported to %s"
               % (wid, aid, state[slot].get("version", "?"), len(nodes), ", ".join(nodes), len(wf.get("global_nodes") or {}), n_tools, out.relative_to(ROOT)))
    return out


def guard_builder_edits(slot, trace, guard):
    """Changes to the builder's own files during this run: all in a patch in out/; the building agent's put back."""
    try:
        snapshot = guard["snapshot"]
        changed, added, deleted = buildguard.builder_edits(snapshot)
        if not (changed or added or deleted):
            trace.line("builder files: unchanged during this build"); return
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(trace.t0))
        patch = ROOT / "out" / ("%s-%s.builder-edits.patch" % (slot, stamp))
        patch.write_text(buildguard.edits_patch(snapshot, changed, added, deleted))
        mine = buildguard.agent_touched(AGENT_TOOL_USES, set(changed + added + deleted))
        theirs = sorted(set(changed + added + deleted) - mine)
        trace.line("builder files changed during this build: by the building agent %s; not tied to it %s | patch of all: %s"
                   % (sorted(mine) or "-", theirs or "-", patch.relative_to(ROOT)))
        if theirs:
            trace.line("WARNING: left as they are (another session or a person may have changed them): %s" % theirs)
        if not mine:
            return
        others = buildguard.other_builds(guard["lock_dir"], os.getpid())
        why = "--keep-builder-edits" if guard["keep"] else ("another build runs from this checkout: " + ", ".join(others)) if others else None
        if why:
            trace.line("WARNING: the building agent's edits stay in the working tree (%s). Never commit builder/ edits made "
                       "for a hidden brief." % why)
            return
        head = buildguard.git_head()
        if head != guard["head"]:            # a commit during the build: leave only the files it touched (it may hold them)
            committed = buildguard.git_changed_since(guard["head"], sorted(mine)) if guard["head"] and head else None
            held = set(mine) if committed is None else (set(mine) & committed)
            if held:
                trace.line("WARNING: git HEAD moved during the build (%s -> %s) and the commit touched %s: those stay as they are; "
                           "check that commit for builder/ edits made for a hidden brief" % (guard["head"], head, sorted(held)))
            mine = set(mine) - held
            if not mine:
                return
        keep_dir = ROOT / "out" / ("%s-%s.builder-edits" % (slot, stamp))
        left = buildguard.restore_builder(snapshot, [k for k in changed if k in mine], [k for k in added if k in mine],
                                          [k for k in deleted if k in mine], keep_dir, tool_uses=AGENT_TOOL_USES)
        trace.line("builder files the agent changed are back as they were at the start (its own edits reversed, other changes "
                   "kept; the exported agent is unchanged; files it added moved to %s; to keep a generic improvement: git apply %s)"
                   % (keep_dir.relative_to(ROOT), patch.relative_to(ROOT)))
        if left:
            trace.line("WARNING: %s changed again after the agent's edit, so its edit could not be reversed exactly: left as is" % left)
    except Exception as e:
        trace.line("builder edit check failed: %r" % (e,))


async def main(argv):
    opts = {"--cases": None, "--runner": "sim", "--minutes": "29", "--slot": None, "--resume": None}; flags = set()
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in opts and i + 1 < len(argv): opts[a] = argv[i + 1]; i += 2; continue
        if a in ("--no-rules", "--no-audit", "--no-gen-cases", "--gen-cases", "--keep-builder-edits", "--allow-parallel", "--fresh"): flags.add(a); i += 1; continue
        args.append(a); i += 1
    # a case folder and a mock URL (the final's run_command: build.py {case_folder} {mock_url}): the folder becomes one
    # combined brief (builder/casefolder.py), the tool API is the mock's own /openapi.json with the mock as the server
    folders = [a for a in args if pathlib.Path(a).is_dir()]
    urls = [a for a in args if re.match(r"https?://", a)]
    case_note = None
    if folders or urls:
        import casefolder
        if len(folders) != 1 or len(urls) > 1:
            sys.exit("give one case folder (and the mock URL, or a tool API .json): " + " ".join(args))
        slot0 = opts["--slot"] or casefolder.slot_name(folders[0])
        (ROOT / "out").mkdir(exist_ok=True)
        combined, n_files, missing = casefolder.combine(folders[0], ROOT / "out" / ("%s.case.md" % slot0))
        rest = [a for a in args if a not in folders and a not in urls]
        args = [combined] + [a for a in rest if a.lower().endswith(".md")]
        if urls:
            try:
                api_path = casefolder.fetch_openapi(urls[0], ROOT / "out" / ("%s.openapi.json" % slot0))
            except Exception as e:
                sys.exit("the mock's tool API %s/openapi.json could not be read: %r" % (urls[0].rstrip("/"), e))
            args.append(api_path)
            flags.add("--no-gen-cases")   # cases.py writes cases for the organisers' mock customers, not for an own mock
        else:
            args += [a for a in rest if a.lower().endswith(".json")]
        opts["--slot"] = slot0
        case_note = ("Case folder: %s (%d files; every original document is there, and the brief file is their combined "
                     "text%s). The tool API is the mock's /openapi.json; its server is %s." % (
                         pathlib.Path(folders[0]).resolve(), n_files,
                         "; NOT converted, read them yourself: " + ", ".join(r for r, _ in missing) if missing else "",
                         urls[0].rstrip("/") if urls else "the API file's"))
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
    if case_note:
        os.environ["BUILD_CASE_NOTE"] = case_note
    budget = float(opts["--minutes"]); slot = opts["--slot"] or pathlib.Path(briefs[-1]).stem
    cases, brief_filter = (opts["--cases"], None) if opts["--cases"] else detect_cases(briefs)
    # one build per checkout: two agents would load each other's library edits while they run (rehearsal, 10 Oct)
    others = buildguard.other_builds(ROOT / "results" / "builds", os.getpid())
    if others and "--allow-parallel" not in flags:
        sys.exit("another build is running from this checkout (%s): run the briefs one after another, or each from its own "
                 "worktree (git worktree add ../bb-%s HEAD; link env.sh and .venv there), or pass --allow-parallel" % (", ".join(others), slot))
    # an earlier run's trace of this slot is kept under its own time stamp (a rerun used to overwrite it)
    for ext in (".log", ".jsonl"):
        old = ROOT / "traces" / (slot + ext)
        if old.exists() and old.stat().st_size:
            old.rename(old.with_name("%s-run-%s%s" % (slot, time.strftime("%Y%m%d-%H%M%S", time.localtime(old.stat().st_mtime)), ext)))
    # resume: an earlier run of this slot left its generator; the agent improves it instead of starting over
    resume_note = None
    gen_prev = ROOT / "out" / ("gen_%s.py" % slot)
    if opts["--resume"]:   # start this slot from another run's generator (e.g. a parallel slot)
        src = pathlib.Path(opts["--resume"])
        if not src.exists():
            sys.exit("--resume: not found: %s" % src)
        if src.resolve() != gen_prev.resolve():
            gen_prev.write_bytes(src.read_bytes())
            os.utime(gen_prev, (src.stat().st_atime, src.stat().st_mtime))
    if gen_prev.exists() and "--fresh" not in flags:
        keep = gen_prev.with_name("gen_%s.prev.py" % slot)
        keep.write_bytes(gen_prev.read_bytes())
        newer = []
        if folders:
            base = pathlib.Path(folders[0]).resolve()
            newer = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.stat().st_mtime > gen_prev.stat().st_mtime)
        resume_note = ("An earlier run of this builder on this slot wrote out/gen_%s.py (%d bytes, %s; a copy is out/gen_%s.prev.py) "
                       "and saved its workflow. START FROM IT: read it and its DECISIONS block, check every decision against the "
                       "documents (newest first), keep what is right, fix what is wrong or missing, then regenerate, lint, save and "
                       "test as the skill says. %s" % (
                           slot, gen_prev.stat().st_size, time.strftime("%H:%M", time.localtime(gen_prev.stat().st_mtime)), slot,
                           ("Documents that arrived AFTER that generator was written (read them first, they may change decisions): "
                            + ", ".join(newer) + ".") if newer else "No document is newer than that generator."))
        os.environ["BUILD_RESUME_NOTE"] = resume_note
    trace = Trace(slot)
    if resume_note:
        trace.line("resume: " + resume_note)
    if case_note:
        trace.line("input: " + case_note + " Brief: %s; tool API: %s" % (" ".join(briefs), tool_api))
    guard = {"snapshot": buildguard.snapshot_builder(), "head": buildguard.git_head(),   # before any step can edit the builder
             "keep": "--keep-builder-edits" in flags, "lock_dir": ROOT / "results" / "builds"}
    guard["lock_dir"].mkdir(parents=True, exist_ok=True)
    lock = guard["lock_dir"] / ("%d.json" % os.getpid())
    lock.write_text(json.dumps({"pid": os.getpid(), "slot": slot, "start": time.time()}))
    rc = 0
    try:
        rc = await build(trace, briefs, tool_api, slot, cases, brief_filter, opts, flags, budget)
    except Exception as e:
        trace.line("ERROR in the build: %r" % (e,)); rc = 1
    finally:
        guard_builder_edits(slot, trace, guard)
        lock.unlink(missing_ok=True)
        trace.line("build end %s | total %.0f s%s" % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), time.time() - trace.t0,
                                                    " | ABORTED: no Claude credential (steps %s)" % NO_CREDENTIAL if NO_CREDENTIAL else ""))
        trace.close()
        # keep every run: traces/<slot>.log is the latest run (what the form points at); a timestamped copy keeps the earlier ones
        import shutil
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(trace.t0))
        for ext in ("log", "jsonl"):
            src = ROOT / "traces" / ("%s.%s" % (slot, ext))
            if src.exists(): shutil.copy(src, ROOT / "traces" / ("%s-%s.%s" % (slot, stamp, ext)))
        print("trace: traces/%s.log (copy traces/%s-%s.log)" % (slot, slot, stamp))
    return rc


async def build(trace, briefs, tool_api, slot, cases, brief_filter, opts, flags, budget):
    """Everything between the start and the end of the trace: rules + cases, the agent run, checks, lint, audit, export."""
    # the simulator's and smoke tests' customer/judge model calls run inside the agent's shell: each one is a line in
    # this file, merged into the trace after the agent run (the trace lists every model call)
    model_log = ROOT / "results" / ("%s.model-calls.log" % slot)
    model_log.parent.mkdir(exist_ok=True); model_log.write_text("")
    os.environ.pop("BUILD_MODEL_LOG", None)    # set for the agent run only: build.py's own steps are traced from their stderr
    builder_model = os.environ.get("BUILDER_MODEL") or DEFAULT_BUILDER_MODEL
    os.environ["BUILDER_MODEL"] = builder_model        # the same model for rules, cases and audit (their subprocesses read it)
    trace.line("build start %s | briefs=%s tool_api=%s slot=%s | cases=%s runner=%s budget=%.0f min | builder model=%s (effort %s, fallback %s) | phone agent model=%s"
               % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), briefs, tool_api, slot, cases, opts["--runner"], budget, builder_model,
                  BUILDER_EFFORT, FALLBACK_MODEL, os.environ.get("FREYA_AGENT_MODEL", "experimental-5")))
    dirty = buildguard.git_dirty()
    if dirty:
        trace.line("WARNING: the build starts with uncommitted changes to the builder's own files: %s" % "; ".join(dirty[:20]))
    others = buildguard.other_builds(ROOT / "results" / "builds", os.getpid())
    if others:
        trace.line("WARNING: another build runs from this checkout (%s): its library edits are not this build's" % ", ".join(others))
    (ROOT / "out").mkdir(exist_ok=True)
    # rules and generated cases run at the same time (T31); the case writer reads the brief itself (independent reader)
    gen_cases = None
    want_cases = "--no-gen-cases" not in flags and (not cases or "--gen-cases" in flags)
    rules_out = "out/%s.rules.json" % slot
    cases_out = "out/%s.cases.json" % slot
    jobs = []
    if "--no-rules" not in flags:
        jobs.append(threading.Thread(target=run_step, args=(trace, "rules", [PY, "builder/rules.py", *briefs, "--api", tool_api, "--out", rules_out], STEP_TIMEOUT)))
    if want_cases:
        (ROOT / cases_out).unlink(missing_ok=True)
        cmd = [PY, "builder/cases.py", "--brief", *briefs, "--api", tool_api, "--out", cases_out]
        if "--no-rules" in flags and (ROOT / rules_out).exists():
            cmd += ["--rules", rules_out]
        jobs.append(threading.Thread(target=run_step, args=(trace, "cases", cmd, STEP_TIMEOUT)))
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
        return 2
    no_rules = "--no-rules" not in flags and not (ROOT / rules_out).exists()
    if no_rules:
        trace.line("WARNING: the rules step left no inventory: the agent builds from the brief itself (no rules.py rerun)")
    os.environ["BUILD_MODEL_LOG"] = str(model_log)    # the simulator, smoke tests, rules/cases/audit runs the agent starts
    try:
        # keep 3 minutes for lint + export and 4 for the final audit (about 2 min: 8 batches, 3 in parallel); the
        # harrow rehearsal gave the agent all but 3 and the audit was skipped with 6 minutes left
        left = budget - trace.elapsed_min() - 3 - (0 if "--no-audit" in flags else 4)
        await asyncio.wait_for(run_claude(briefs, tool_api, slot, trace, cases, brief_filter, opts["--runner"], left, generated=gen_cases,
                                          no_rules=no_rules), timeout=max(60, left * 60))
    except asyncio.TimeoutError:
        trace.line("STOPPED: the build budget was reached. Verifying and exporting whatever is saved on Freya.")
    except Exception as e:
        trace.line("ERROR in the agent run: %r" % (e,))
    try:
        restored = check_version(slot, trace, trace.t0)
    except Exception as e:
        trace.line("version check failed, the final version stays: %r" % (e,)); restored = False
    tune_turn_taking(slot, briefs, trace)
    os.environ.pop("BUILD_MODEL_LOG", None)
    try:
        calls = [x for x in model_log.read_text().splitlines() if x.strip()]
        trace.line("simulator/smoke model calls during the agent run: %d (one line each below; time | provider model | purpose)" % len(calls))
        for x in calls:
            trace.line("model call (test): " + x)
    except Exception as e:
        trace.line("model-call log not read: %r" % (e,))
    wf_path = ROOT / "out" / ("%s.workflow.json" % slot)
    if wf_path.exists():
        rules_file = ROOT / "out" / ("%s.rules.json" % slot)
        lint_cmd = [PY, "builder/lint.py", str(wf_path), "--api", tool_api] + (["--rules", str(rules_file), "--budget"] if rules_file.exists() else [])
        try:   # the call variables every call carries: the practice cases name them (no test_variables are shipped)
            cs = json.load(open(cases)) if cases else []
            cs = cs.get("cases", cs) if isinstance(cs, dict) else cs
            names = sorted({"customer_id"} | set((cs[0].get("variables") or {}).keys())) if cs else []
            gen = ROOT / "out" / ("gen_%s.py" % slot)   # without cases: the generator's '# CALL VARIABLES:' header (skill section 0)
            if not names and gen.exists():
                m = re.search(r"^#\s*CALL VARIABLES:\s*(.+)$", gen.read_text(errors="ignore"), re.M)
                names = sorted({"customer_id"} | {n for n in re.split(r"[,\s]+", m.group(1)) if re.match(r"^[A-Za-z_]\w*$", n)}) if m else []
            if names:
                lint_cmd += ["--call-vars", ",".join(names)]
        except Exception:
            pass
        run_step(trace, "lint", lint_cmd, timeout=max(30, min(120, int((budget - trace.elapsed_min() - 1) * 60))))
        # the audit only when it cannot push the trace's end past the budget (worst case was 34 min before this guard)
        left_min = budget - trace.elapsed_min()
        if "--no-audit" not in flags and rules_file.exists() and left_min > 4.5:
            gen = ROOT / "out" / ("gen_%s.py" % slot)
            if restored:
                trace.line("audit: on the restored definition only (the generator belongs to the version that was replaced)")
            run_step(trace, "audit", [PY, "builder/audit.py", "--rules", str(rules_file), "--workflow", str(wf_path),
                                      "--generator", str(gen) if gen.exists() and not restored else "", "--out", "out/%s.audit.json" % slot],
                     timeout=int(min(360, (left_min - 1.5) * 60)))
        elif "--no-audit" not in flags:
            trace.line("audit skipped: %.1f minutes left of the %d-minute budget" % (left_min, budget))
    try:
        export(slot, trace)
    except Exception as e:
        trace.line("ERROR exporting the workflow: %r" % (e,))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])) or 0)
