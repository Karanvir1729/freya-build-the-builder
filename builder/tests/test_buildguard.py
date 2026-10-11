#!/usr/bin/env python3
"""Tests for builder/buildguard.py (no network: freya is a fake). Plain asserts: python3 builder/tests/test_buildguard.py"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "builder"))
import buildguard as bg  # noqa: E402


# ------------------------------------------------------------------------------------------- builder edits
def tree():
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "builder").mkdir(); (d / "builder" / "__pycache__").mkdir(); (d / ".claude" / "skills").mkdir(parents=True)
    (d / "tools").mkdir(); (d / "out").mkdir()
    (d / "builder" / "policy.py").write_text("def f():\n    return 1\n")
    (d / "builder" / "lint.py").write_text("X = 1\n")
    (d / "builder" / "__pycache__" / "policy.cpython-312.pyc").write_bytes(b"\x00\x01")
    (d / ".claude" / "skills" / "SKILL.md").write_text("# skill\n")
    (d / "tools" / "score.py").write_text("S = 2\n")
    (d / "freya.py").write_text("AGENT = 'x'\n")
    (d / "out" / "gen_x.py").write_text("generated\n")          # build output: not watched
    return d


def test_snapshot_ignores_caches_outputs_worktrees():
    d = tree()
    (d / ".claude" / "settings.local.json").write_text("{}")
    wt = d / ".claude" / "worktrees" / "other"; (wt / "builder").mkdir(parents=True)
    (wt / ".git").write_text("gitdir: elsewhere\n"); (wt / "builder" / "policy.py").write_text("theirs\n")
    nested = d / "builder" / "vendored"; nested.mkdir(); (nested / ".git").mkdir(); (nested / "x.py").write_text("x\n")
    snap = bg.snapshot_builder(d)
    assert set(snap) == {"builder/policy.py", "builder/lint.py", ".claude/skills/SKILL.md", "tools/score.py", "freya.py"}, sorted(snap)
    shutil.rmtree(d)


def test_edits_patch_restore_roundtrip():
    d = tree()
    snap = bg.snapshot_builder(d)
    assert bg.builder_edits(snap, d) == ([], [], [])
    (d / "builder" / "policy.py").write_text("def f():\n    return 2   # brief-specific\n")
    (d / "builder" / "newmod.py").write_text("NEW = True\n")
    (d / "tools" / "score.py").unlink()
    (d / "out" / "gen_x.py").write_text("regenerated\n")
    (d / "builder" / "__pycache__" / "x.pyc").write_bytes(b"\x02")
    changed, added, deleted = bg.builder_edits(snap, d)
    assert (changed, added, deleted) == (["builder/policy.py"], ["builder/newmod.py"], ["tools/score.py"]), (changed, added, deleted)
    patch = bg.edits_patch(snap, changed, added, deleted, d)
    assert "+    return 2   # brief-specific" in patch and "new file mode" in patch and "deleted file mode" in patch, patch
    edited = {k: (d / k).read_bytes() for k in changed + added}
    keep = d / "out" / "kept"
    bg.restore_builder(snap, changed, added, deleted, keep, d)
    assert bg.builder_edits(snap, d) == ([], [], []), bg.builder_edits(snap, d)
    assert (keep / "builder" / "newmod.py").read_text() == "NEW = True\n"   # an added file is moved, never deleted
    (keep / "builder" / "newmod.py").unlink()
    assert (d / "out" / "gen_x.py").read_text() == "regenerated\n"      # outputs are never touched
    # the patch re-applies the edits with git apply (what the trace tells a developer to run)
    if shutil.which("git"):
        (d / "edits.patch").write_text(patch)
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        r = subprocess.run(["git", "apply", "edits.patch"], cwd=d, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert {k: (d / k).read_bytes() for k in changed + added} == edited
        assert not (d / "tools" / "score.py").exists()
    shutil.rmtree(d)


def test_patch_without_trailing_newline():
    d = tree()
    snap = bg.snapshot_builder(d)
    (d / "builder" / "lint.py").write_text("X = 2")
    ch, ad, de = bg.builder_edits(snap, d)
    patch = bg.edits_patch(snap, ch, ad, de, d)
    if shutil.which("git"):
        bg.restore_builder(snap, ch, ad, de, d / "out" / "kept", d)
        (d / "e.patch").write_text(patch)
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        r = subprocess.run(["git", "apply", "e.patch"], cwd=d, capture_output=True, text=True)
        assert r.returncode == 0, (r.stderr, patch)
        assert (d / "builder" / "lint.py").read_text() == "X = 2"
    shutil.rmtree(d)


def test_agent_touched():
    d = tree()
    paths = {"builder/policy.py", "builder/lint.py", "tools/score.py", "builder/newmod.py"}
    uses = [("Edit", {"file_path": str(d / "builder" / "lint.py")}),
            ("Write", {"file_path": "builder/newmod.py"}),
            ("Write", {"file_path": str(d / "out" / "gen_x.py")}),
            ("Bash", {"command": "python3 - <<'EOF'\np='builder/policy.py'; s=open(p).read()\nopen(p,'w').write(s)\nEOF"}),
            ("Bash", {"command": "grep -n score tools/score.py"}),              # reads only: not an edit
            ("Read", {"file_path": str(d / "tools" / "score.py")})]
    assert bg.agent_touched(uses, paths, d) == {"builder/lint.py", "builder/newmod.py", "builder/policy.py"}, bg.agent_touched(uses, paths, d)
    assert bg.agent_touched([("Bash", {"command": "cd builder && sed -i 's/1/2/' policy.py"})], paths, d) == {"builder/policy.py"}
    assert bg.agent_touched([], paths, d) == set()
    reads = ["python3 builder/tests/test_policy.py 2>&1 | tail -3", "grep -n x builder/policy.py > /tmp/out.txt",
             "cp builder/policy.py /tmp/copy.py", "sed -n 1,40p builder/policy.py", "python3 -c \"import json; print(open('builder/lint.py').read()[:10])\""]
    reads.append("python3 - <<'EOF'\np='out/gen_x.py'; s=open(p).read()\nopen(p,'w').write(s)\nEOF\npython3 builder/lint.py out/x.json --api a")
    reads.append("sed -i '' 's/a/b/' out/gen_x.py && python3 out/gen_x.py && python3 builder/lint.py out/x.json")
    for c in reads:                                                     # naming a file is not writing it
        assert bg.agent_touched([("Bash", {"command": c})], paths, d) == set(), c
    writes = {"cat > builder/lint.py <<'EOF'\nX = 3\nEOF": "builder/lint.py", "echo y >> tools/score.py": "tools/score.py",
              "cp out/new.py builder/policy.py": "builder/policy.py", "rm -f builder/newmod.py": "builder/newmod.py",
              "printf 'x' | tee builder/lint.py": "builder/lint.py",
              "python3 - <<'EOF'\np='builder/policy.py'; s=open(p).read()\nopen(p,'w').write(s)\nEOF": "builder/policy.py",
              "python3 - <<'EOF'\nimport pathlib\npathlib.Path('builder/lint.py').write_text('x')\nEOF": "builder/lint.py",
              "python3 -c \"open('tools/score.py', 'a').write('#')\"": "tools/score.py",
              "python3 - <<'EOF'\nimport pathlib\nf = pathlib.Path('builder/policy.py')\nf.write_text(f.read_text())\nEOF": "builder/policy.py"}
    for c, want in writes.items():
        assert bg.agent_touched([("Bash", {"command": c})], paths, d) == {want}, (c, bg.agent_touched([("Bash", {"command": c})], paths, d))
    shutil.rmtree(d)


def test_hunk_undo_keeps_other_changes():
    d = tree()
    (d / "builder" / "policy.py").write_text("A = 1\nB = 2\nC = 3\n")
    snap = bg.snapshot_builder(d)
    # the agent edits one line, someone else adds a function to the same file meanwhile
    (d / "builder" / "policy.py").write_text("A = 1\nB = 20   # agent\nC = 3\ndef fix():\n    pass\n")
    uses = [("Edit", {"file_path": str(d / "builder" / "policy.py"), "old_string": "B = 2\n", "new_string": "B = 20   # agent\n"})]
    ch, ad, de = bg.builder_edits(snap, d)
    left = bg.restore_builder(snap, ch, ad, de, d / "out" / "kept", d, tool_uses=uses)
    assert left == [] and (d / "builder" / "policy.py").read_text() == "A = 1\nB = 2\nC = 3\ndef fix():\n    pass\n"
    # nothing else changed: back to the snapshot exactly
    (d / "builder" / "policy.py").write_text("A = 1\nB = 20   # agent\nC = 3\n")
    bg.restore_builder(snap, ["builder/policy.py"], [], [], d / "out" / "kept", d, tool_uses=uses)
    assert (d / "builder" / "policy.py").read_bytes() == snap["builder/policy.py"]
    # the agent's line was changed again by someone: left as is, reported
    (d / "builder" / "policy.py").write_text("A = 1\nB = 21   # someone\nC = 3\n")
    assert bg.restore_builder(snap, ["builder/policy.py"], [], [], d / "out" / "kept", d, tool_uses=uses) == ["builder/policy.py"]
    assert (d / "builder" / "policy.py").read_text() == "A = 1\nB = 21   # someone\nC = 3\n"
    # a file the agent rewrote with Write gets the snapshot
    (d / "builder" / "lint.py").write_text("rewritten\n")
    bg.restore_builder(snap, ["builder/lint.py"], [], [], d / "out" / "kept", d, tool_uses=[("Write", {"file_path": "builder/lint.py", "content": "rewritten\n"})])
    assert (d / "builder" / "lint.py").read_bytes() == snap["builder/lint.py"]
    assert bg.undo_hunks("x y x", [("a", "x")]) is None             # not exactly once: no guess
    shutil.rmtree(d)


def test_cd_into_the_repo_folder_is_not_a_cd_into_builder():
    d = tree()
    paths = {"builder/policy.py"}
    c = "cd /Users/me/freya-build-the-builder && python3 builder/tests/test_policy.py | tail -3; python3 - <<'EOF'\nopen('out/n.json','w').write('{}')\nEOF"
    assert bg.agent_touched([("Bash", {"command": c})], paths, d) == set()
    assert bg.agent_touched([("Bash", {"command": "cd builder && sed -i 's/1/2/' policy.py"})], paths, d) == {"builder/policy.py"}
    assert bg.agent_touched([("Bash", {"command": "cd /x/repo/builder && rm -f policy.py"})], paths, d) == {"builder/policy.py"}
    shutil.rmtree(d)


def test_git_helpers():
    if not shutil.which("git"):
        return
    d = tree()
    assert bg.git_head(d) is None or bg.git_head(d) == ""  # not a repository yet
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=d, check=True, env=env)
    assert len(bg.git_head(d) or "") == 40 and bg.git_dirty(d) == []
    (d / "builder" / "policy.py").write_text("changed\n"); (d / "out" / "gen_y.py").write_text("y\n")
    assert [l[-17:] for l in bg.git_dirty(d)] == ["builder/policy.py"], bg.git_dirty(d)
    start = bg.git_head(d)
    (d / "tools" / "score.py").write_text("S = 3\n")
    subprocess.run(["git", "add", "tools/score.py"], cwd=d, check=True)
    subprocess.run(["git", "commit", "-qm", "y"], cwd=d, check=True, env=env)
    assert bg.git_changed_since(start, ["builder/policy.py", "tools/score.py"], d) == {"tools/score.py"}
    assert bg.git_changed_since("nosuchref", ["tools/score.py"], d) is None
    shutil.rmtree(d)


def test_write_state_version():
    d = pathlib.Path(tempfile.mkdtemp()); f = d / ".freya-agents.json"
    f.write_text(json.dumps({"a": {"workflow_id": "w"}, "b": {"workflow_id": "x"}}))
    bg.write_state_version(f, "a", 7)
    assert json.loads(f.read_text()) == {"a": {"workflow_id": "w", "version": 7}, "b": {"workflow_id": "x"}}
    bg.write_state_version(f, "zz", 1)                                    # unknown slot: no change
    assert "zz" not in json.loads(f.read_text()) and not list(d.glob("*.tmp"))
    shutil.rmtree(d)


def test_other_builds():
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "me.json").write_text(json.dumps({"pid": os.getpid(), "slot": "mine"}))
    (d / "dead.json").write_text(json.dumps({"pid": 2 ** 22 + 12345, "slot": "gone"}))    # no such process
    (d / "junk.json").write_text("not json")
    assert bg.other_builds(d, os.getpid()) == []
    sleeper = subprocess.Popen(["sleep", "30"])                         # alive, but not a build: its lock is stale
    (d / "reused.json").write_text(json.dumps({"pid": sleeper.pid, "slot": "reused"}))
    assert bg.other_builds(d, os.getpid()) == [], bg.other_builds(d, os.getpid())
    sleeper.kill()
    fake = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", "builder/build.py"])   # 'build.py' in its command
    (d / "live.json").write_text(json.dumps({"pid": fake.pid, "slot": "other"}))
    assert bg.other_builds(d, os.getpid()) == ["other (pid %d)" % fake.pid], bg.other_builds(d, os.getpid())
    fake.kill()
    shutil.rmtree(d)


# ------------------------------------------------------------------------------------------- best tested version
def test_is_infra():
    f = lambda *x, **kw: dict(failed=list(x), **kw)
    assert bg.is_infra(f("harness: TimeoutError: x"))
    assert bg.is_infra(f("conversation: judge model failed: 500"))
    assert bg.is_infra(f("conversation: no verdict (the judge answered twice without pass/fail)"))
    assert bg.is_infra(f("mock bank: could not open a practice session for PUB-01"))
    assert bg.is_infra(f("outcome wrong", chat_branched=True))
    assert bg.is_infra(f("outcome wrong", stop="3 server errors without a reply (5xx or no answer)"))
    assert bg.is_infra(f("conversation: x", stop="customer model failed: 429"))
    assert not bg.is_infra(f("outcome ('no_promise', None) expected ('promise', None)"))
    assert not bg.is_infra(f("conversation: the agent offered the floor twice"))
    assert not bg.is_infra(f("conversation: silent", stop="two empty replies in a row"))   # the agent's own fault
    assert not bg.is_infra(f())


def test_record_and_read():
    d = pathlib.Path(tempfile.mkdtemp()); p = d / "w.jsonl"
    bg.record_result(p, {"pass": True, "version": 3, "version_id": "a", "failed": []}, "PUB-01", 1, "w", "cases.json")
    bg.record_result(p, {"pass": False, "version": 3, "failed": ["harness: boom"]}, "PUB-02", 1, "w", "cases.json")
    bg.record_result(p, {"pass": False, "version": None, "failed": ["x"]}, "PUB-03", 1, "w", "cases.json")
    bg.record_result(p, {"pass": False, "version": 4, "failed": ["outcome wrong"]}, "PUB-01", 1, "w", "cases.json")
    r = bg.results_by_version(p, since=0)
    assert r == {3: {"PUB-01": [True]}, 4: {"PUB-01": [False]}}, r          # infra and unknown-version rows dropped
    assert bg.results_by_version(p, since=10 ** 12) == {}                 # rows before the build started
    assert bg.results_by_version(d / "none.jsonl", since=0) == {}
    bg.record_result(d / "no" / "such" / "dir" / "x.jsonl", {"pass": True, "version": 1}, "A", 1, "w", None)   # never raises, makes dirs
    shutil.rmtree(d)


def R(**cases):
    return {k.replace("_", "-"): ([v] if isinstance(v, bool) else v) for k, v in cases.items()}


def test_choose_version():
    T, F = True, False
    full = dict(A=T, B=T, C=T, D=T, E=F, G=F)
    assert bg.choose_version({}, 5)[0] == 5
    assert bg.choose_version({1: R(**full)}, 1)[0] == 1
    # a repair round that re-ran only the failures: nothing lost, keep the final
    assert bg.choose_version({1: R(**full), 2: R(E=T, G=F)}, 2)[0] == 2
    # the final re-ran everything, lost 2 and gained none: ship the version before it
    ship, why = bg.choose_version({1: R(**full), 2: R(A=F, B=F, C=T, D=T, E=F, G=F)}, 2)
    assert ship == 1 and "A, B" in why, (ship, why)
    # lost 2 but gained 1 (the fix worked): keep the final
    assert bg.choose_version({1: R(**full), 2: R(A=F, B=F, C=T, D=T, E=T, G=F)}, 2)[0] == 2
    # one case lost is noise: keep
    assert bg.choose_version({1: R(**full), 2: R(A=F, B=T, C=T, D=T, E=F, G=F)}, 2)[0] == 2
    # fewer than 4 shared cases: keep, however bad
    assert bg.choose_version({1: R(A=T, B=T, C=T), 2: R(A=F, B=F, C=F)}, 2)[0] == 2
    # an untested final always stays (it holds fixes for what the last test found)
    assert bg.choose_version({1: R(**full), 2: R(A=F, B=F, C=F, D=F, E=F, G=F)}, 3)[0] == 3
    assert bg.choose_version({4: R(**full)}, 3)[0] == 3
    # only the immediately preceding tested version is compared, never the best of all older ones
    res = {1: R(A=T, B=T, C=T, D=T), 2: R(A=F, B=F, C=F, D=F), 3: R(A=F, B=F, C=F, D=T)}
    assert bg.choose_version(res, 3)[0] == 3
    # pass rates over reps: 3/3 against 1/3 on three cases is 2.0 lost
    assert bg.choose_version({1: R(A=[T, T, T], B=[T, T, T], C=[T, T, T], D=[T]), 2: R(A=[T, F, F], B=[F, T, F], C=[F, F, T], D=[T])}, 2)[0] == 1


def test_cases_date_in_text():
    import cases
    t = "On these days we are closed:\n- Monday 19 October 2026 - Charter Day\n- Thursday 12th November\n- 9/12/2026 staff day\nAlso 2026-12-25."
    assert all(cases.date_in_text(h, t) for h in ("2026-10-19", "2026-11-12", "2026-12-09", "2026-12-25"))
    assert not cases.date_in_text("2026-10-20", t) and not cases.date_in_text("2026-11-02", "112 November")
    assert cases.date_in_text("2026-10-19", "October 19th is a holiday") and cases.date_in_text("2026-10-19", "19 Oct.")


# ------------------------------------------------------------------------------------------- platform calls (fake)
class FakeFreya:
    AGENT_LLM = {"provider": "experimental-5", "model": "experimental-5"}

    def __init__(self, versions, workflow, snapshots=None):
        self.versions, self.workflow, self.snapshots = versions, workflow, snapshots or {}
        self.calls = []

    def workspace_id(self):
        return "ws"

    def api(self, method, path, body=None, **q):
        self.calls.append((method, path, body))
        if method == "GET" and path.startswith("/api/v2/versions/workflow/") and path.count("/") == 6:
            vid = path.rsplit("/", 1)[1]
            return {"version": {"configSnapshot": self.snapshots[vid]}}
        if method == "GET" and path.startswith("/api/v2/versions/workflow/"):
            return {"versions": self.versions}
        if method == "GET" and path.startswith("/api/v2/workflow/"):
            return {"workflow": {"workflow": self.workflow}}
        if method == "PUT" and path.startswith("/api/v2/workflow/"):
            self.workflow = body["workflow"]
            n = max(v["versionNumber"] for v in self.versions) + 1
            self.versions.append({"id": "v%d" % n, "versionNumber": n, "isPublished": False})
            return {}
        if method == "POST" and path.endswith("/publish"):
            for v in self.versions:
                v["isPublished"] = v["id"] == body["versionId"]
            return {}
        raise AssertionError((method, path))

    def update_workflow(self, wid, wf):
        self.calls.append(("update", wid, wf))
        n = max(v["versionNumber"] for v in self.versions) + 1
        self.versions.append({"id": "v%d" % n, "versionNumber": n, "isPublished": True})
        return n

    def validate_workflow(self, name, wf):
        self.calls.append(("validate", name, wf))
        assert "agent_config" not in json.dumps(wf) and "null" not in json.dumps(wf)
        return {}


def wf(model="experimental-5"):
    return {"initial_node": "a", "nodes": {"a": {"node_type": "conversation", "max_turn_transition": None}},
            "agent_config": {"llmConfig": {"provider": model, "model": model, "apiKey": None}}}


def test_ensure_published():
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": True}], wf())
    v, note = bg.ensure_published(f, "w")
    assert v == 1 and "is published" in note and not [c for c in f.calls if c[0] != "GET"], (note, f.calls)
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": True}, {"id": "v2", "versionNumber": 2, "isPublished": False}], wf())
    v, note = bg.ensure_published(f, "w")
    assert v == 2 and "published it" in note and f.versions[1]["isPublished"], (note, f.versions)
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": True}], wf("gpt-x"))
    v, note = bg.ensure_published(f, "w")
    upd = [c for c in f.calls if c[0] == "update"]
    assert v == 2 and "event's model" in note and upd and "agent_config" not in upd[0][2], (note, f.calls)
    assert "max_turn_transition" not in upd[0][2]["nodes"]["a"]


def test_restore_version():
    snaps = {"v1": wf()}
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": False}, {"id": "v2", "versionNumber": 2, "isPublished": True}], wf(), snaps)
    new_v, d = bg.restore_version(f, "slot", "w", 1)
    assert new_v == 3 and d == {"initial_node": "a", "nodes": {"a": {"node_type": "conversation"}}}, (new_v, d)
    kinds = [c[0] for c in f.calls]
    assert kinds.index("validate") < kinds.index("update"), kinds      # dry run before the save


def test_brief_language():
    assert bg.brief_language("Call the customer. Speak German at all times.") == "de"
    assert bg.brief_language("The language of the call is French.") == "fr"
    assert bg.brief_language("Collections brief. The customer may mention a holiday in Spain.") == "en"
    assert bg.brief_language("") == "en"


def test_tune_turn_taking():
    w = wf(); w["agent_config"].update({"ttsConfig": {"language": "tr", "startSpeakingPlan": {"waitSeconds": 0.5}},
                                        "sttConfig": {"language": "tr", "additionalSettings": {"smartTurnEnabled": True}}})
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": True}], w)
    v, note = bg.tune_turn_taking(f, "w", "en", wait=4.0)
    ac = f.workflow["agent_config"]
    assert v == 2 and f.versions[1]["isPublished"] and "read-back" not in note, (v, note, f.versions)
    assert ac["ttsConfig"]["startSpeakingPlan"]["waitSeconds"] == 4.0 and ac["sttConfig"]["additionalSettings"]["smartTurnEnabled"] is False
    assert ac["ttsConfig"]["language"] == ac["sttConfig"]["language"] == "en" and ac["llmConfig"]["model"] == "experimental-5"
    assert f.workflow["nodes"] == wf()["nodes"]                          # the definition itself is unchanged
    v, note = bg.tune_turn_taking(f, "w", "en", wait=4.0)                 # already set: no new version
    assert v is None and "already" in note and len(f.versions) == 2, (v, note)
    f = FakeFreya([{"id": "v1", "versionNumber": 1, "isPublished": True}], {"initial_node": "a", "nodes": {}})
    v, note = bg.tune_turn_taking(f, "w", "en", wait=4.0)                 # no agent_config: nothing sent
    assert v is None and not [c for c in f.calls if c[0] != "GET"], f.calls


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    bad = 0
    for t in tests:
        try:
            t(); print("ok  ", t.__name__)
        except Exception as e:
            bad += 1; print("FAIL", t.__name__, repr(e))
    print("%d/%d passed" % (len(tests) - bad, len(tests)))
    sys.exit(1 if bad else 0)
