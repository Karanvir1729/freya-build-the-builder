"""Guards that builder/build.py runs around the building agent. Standard library plus freya.py; no model calls.

1. Builder edits (snapshot_builder / builder_edits / agent_touched / restore_builder): the building agent may extend
   builder/policy.py or another library file while it builds. Every change to the builder's own files during the run
   goes to a patch in out/; the changes the agent made (paths in its Write/Edit calls or named in its shell commands)
   are put back as they were when the build started, so code written for one brief (a hidden brief after the freeze)
   never stays in builder/ by accident. Changes nobody can tie to the agent (another session, a person) are reported and
   left alone; nothing is restored when git HEAD moved or another build runs from the same checkout. The exported agent
   is unaffected: it was generated and saved before the restore.
2. Published check (ensure_published): after the agent run, the newest version of the slot's workflow must be the
   published one and must run on the event's agent model (freya.AGENT_LLM). Fixed with the kit's own calls if not.
3. Best tested version (choose_version / restore_version): builder/sim.py records, per case, the workflow version the
   call ran on (results/versions/<workflow_id>.jsonl). When the final version passed clearly fewer of the cases it shares
   with the version tested before it, and gained none, the earlier version's definition is saved again and shipped.

    python3 builder/tests/test_buildguard.py
"""
import difflib, json, os, pathlib, re, shutil, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent

# what the building agent can change that the builder itself runs. Not .claude/ as a whole: Claude Code keeps session
# worktrees (.claude/worktrees/) and local settings there.
WATCHED_DIRS = ("builder", ".claude/skills", "tools")
WATCHED_FILES = ("freya.py",)
SKIP_DIRS = ("__pycache__",)
SKIP_SUFFIXES = (".pyc",)


# ------------------------------------------------------------------------------------------- 1. builder edits
def _watched_files(root=ROOT):
    files = []
    for d in WATCHED_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # never descend into a cache or a nested checkout (a worktree or another repository has its own .git)
            dirnames[:] = sorted(x for x in dirnames if x not in SKIP_DIRS and not os.path.exists(os.path.join(dirpath, x, ".git")))
            files += [pathlib.Path(dirpath) / f for f in sorted(filenames) if not f.endswith(SKIP_SUFFIXES)]
    files += [root / f for f in WATCHED_FILES if (root / f).is_file()]
    return files


def snapshot_builder(root=ROOT):
    """{relative path: bytes} of every file the builder runs, taken before the building agent starts."""
    return {str(p.relative_to(root)): p.read_bytes() for p in _watched_files(root)}


def builder_edits(snapshot, root=ROOT):
    """(changed, added, deleted) relative paths since the snapshot."""
    now = {str(p.relative_to(root)): p for p in _watched_files(root)}
    changed = sorted(k for k, p in now.items() if k in snapshot and p.read_bytes() != snapshot[k])
    added = sorted(k for k in now if k not in snapshot)
    deleted = sorted(k for k in snapshot if k not in now)
    return changed, added, deleted


WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# a shell command writes a file it names when it redirects into it, edits it in place, copies or moves onto it, removes
# it, or is a script that names it and writes (python open(..., 'w') / write_text / .write). Naming a file is not
# writing it: 'python3 builder/tests/test_policy.py 2>&1 | tail' reads only.
def _py_writes(cmd, p):
    """A python snippet that writes this path: open('<path>', 'w'), Path('<path>').write_text(...), os.replace/shutil onto
    it, or a variable holding the path that is opened for writing (p = 'builder/policy.py'; open(p, 'w'))."""
    q = r"['\"]" + p + r"['\"]"
    mode = r"\s*,\s*['\"](?:w|a|r\+)b?['\"]"
    if re.search(r"open\(\s*" + q + mode, cmd) or re.search(r"Path\(\s*" + q + r"\s*\)\s*\.\s*write_(?:text|bytes)\(", cmd) or \
            re.search(r"(?:os\.replace|os\.rename|shutil\.(?:copy\w*|move))\([^)]*,\s*" + q, cmd):
        return True
    for m in re.finditer(r"\b(\w+)\s*=\s*(?:pathlib\.)?(?:Path\()?" + q, cmd):
        v = re.escape(m.group(1))
        if re.search(r"open\(\s*" + v + mode, cmd) or re.search(r"\b" + v + r"\s*\.\s*write_(?:text|bytes)\(", cmd) or \
                re.search(r"Path\(\s*" + v + r"\s*\)\s*\.\s*write_(?:text|bytes)\(", cmd):
            return True
    return False


def _writes(cmd, path):
    p = re.escape(path)
    end = r"(?=$|[\s;|&)'\"])"
    pats = [r">>?\s*['\"]?" + p + end,                                  # cat > path, echo x >> path
            r"\btee\s+(?:-a\s+)?['\"]?" + p + end,
            r"\b(?:sed|perl)\s+(?:-\w+\s+)*-i\b[^;&|\n]*" + p + end,  # sed -i ... path (same simple command)
            r"\b(?:cp|mv|install)\s+(?:-\w+\s+)*\S+\s+['\"]?" + p + end,  # cp src path (path is the target)
            r"\b(?:rm|unlink|truncate)\s+(?:-\w+\s+)*['\"]?" + p + end,
            r"\bgit\s+(?:checkout|restore)\b[^;&|\n]*" + p + end]
    if any(re.search(x, cmd) for x in pats):
        return True
    return _py_writes(cmd, p)


def agent_touched(tool_uses, paths, root=ROOT):
    """The paths (relative) among `paths` that the building agent wrote or named: a Write/Edit/NotebookEdit file_path,
    or a shell command that names the path (relative or absolute, or its file name next to its folder's name)."""
    root_s = str(pathlib.Path(root).resolve())
    hit = set()
    for name, inp in tool_uses:
        inp = inp or {}
        fp = (inp.get("file_path") or inp.get("notebook_path")) if name in WRITE_TOOLS else None
        if fp:
            p = pathlib.Path(fp)
            p = p if p.is_absolute() else pathlib.Path(root) / p
            try:
                rel = str(p.resolve().relative_to(root_s))
            except ValueError:
                rel = None
            if rel in paths:
                hit.add(rel)
        cmd = inp.get("command")
        if isinstance(cmd, str):
            for rel in paths:
                folder, base = os.path.split(rel)
                # the path as written in the command: relative, absolute, or the file name after a cd into its folder
                cd_in = folder and re.search(r"\bcd\s+['\"]?(?:\S*/)?" + re.escape(folder) + r"/?['\"]?(?=$|[\s;&|)])", cmd)
                forms = [rel, os.path.join(root_s, rel)] + ([base] if cd_in else [])
                if any(_writes(cmd, f) for f in forms):
                    hit.add(rel)
    return hit


def agent_edit_hunks(tool_uses, rel, root=ROOT):
    """(hunks, other) for one file: the (old_string, new_string) pairs of the agent's Edit/MultiEdit calls on it, in
    order, and whether it also wrote the file another way (Write, a shell command), which leaves no hunks to undo."""
    root_s = str(pathlib.Path(root).resolve())
    hunks, other = [], False
    for name, inp in tool_uses:
        inp = inp or {}
        fp = inp.get("file_path") or inp.get("notebook_path")
        if fp and name in WRITE_TOOLS:
            p = pathlib.Path(fp)
            p = p if p.is_absolute() else pathlib.Path(root) / p
            try:
                if str(p.resolve().relative_to(root_s)) != rel:
                    continue
            except ValueError:
                continue
            if name == "Edit" and isinstance(inp.get("old_string"), str) and isinstance(inp.get("new_string"), str) and not inp.get("replace_all"):
                hunks.append((inp["old_string"], inp["new_string"]))
            elif name == "MultiEdit" and isinstance(inp.get("edits"), list) and all(isinstance(e, dict) and not e.get("replace_all") for e in inp["edits"]):
                hunks += [(e.get("old_string", ""), e.get("new_string", "")) for e in inp["edits"]]
            else:
                other = True
        elif name not in WRITE_TOOLS and agent_touched([(name, inp)], {rel}, root):
            other = True
    return hunks, other


def undo_hunks(text, hunks):
    """The text with the hunks reversed, newest first (new_string -> old_string, each only where it occurs exactly
    once), or None when one of them cannot be found exactly once (someone changed that part since)."""
    for old, new in reversed(hunks):
        if not new or text.count(new) != 1:
            return None
        text = text.replace(new, old, 1)
    return text


def _text(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return None


def edits_patch(snapshot, changed, added, deleted, root=ROOT):
    """A unified diff (git apply format) of the edits, from the snapshot to the files as they are now."""
    out = []
    for k in changed + added + deleted:
        old = _text(snapshot[k]) if k in snapshot else ""
        new = _text((root / k).read_bytes()) if (root / k).exists() else ""
        if old is None or new is None:
            out.append("Binary file %s changed (not in the patch)\n" % k)
            continue
        a = "/dev/null" if k in added else "a/" + k
        b = "/dev/null" if k in deleted else "b/" + k
        head = ["diff --git a/%s b/%s\n" % (k, k)]
        if k in added:
            head.append("new file mode 100644\n")
        elif k in deleted:
            head.append("deleted file mode 100644\n")
        body = list(difflib.unified_diff(old.splitlines(True), new.splitlines(True), a, b))
        if body:
            body = [l if l.endswith("\n") else l + "\n\\ No newline at end of file\n" for l in body]
            out += head + body
    return "".join(out)


def restore_builder(snapshot, changed, added, deleted, keep_dir, root=ROOT, tool_uses=None):
    """Put the agent's changes back: a file it changed only with Edit/MultiEdit gets those hunks reversed, so a change
    someone else made to the same file meanwhile stays (whole snapshot when nothing else changed); a file it rewrote
    (Write, a shell command) gets the snapshot; deleted files come back; added files move to keep_dir (never deleted).
    Returns the files it left as they are because a hunk could not be reversed exactly."""
    left = []
    for k in changed + deleted:
        p = root / k
        p.parent.mkdir(parents=True, exist_ok=True)
        if tool_uses is not None and k in changed:
            hunks, other = agent_edit_hunks(tool_uses, k, root)
            if hunks and not other:
                cur = _text(p.read_bytes())
                undone = undo_hunks(cur, hunks) if cur is not None else None
                if undone is None:
                    left.append(k)
                    continue
                if undone.encode("utf-8") != snapshot[k]:
                    p.write_text(undone)           # someone else's change in the same file stays
                    continue
        p.write_bytes(snapshot[k])
    for k in added:
        src = root / k
        if src.exists():
            dst = pathlib.Path(keep_dir) / k
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    return left


def git_head(root=ROOT):
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=20).stdout.strip() or None
    except Exception:
        return None


def git_dirty(root=ROOT):
    """Uncommitted changes to the builder's own files (`git status --porcelain` lines), [] when clean or not a repo."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--", *WATCHED_DIRS, *WATCHED_FILES], cwd=root,
                             capture_output=True, text=True, timeout=20).stdout
        return [l for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def other_builds(lock_dir, me):
    """Slots of other builds running from the same checkout (their lock file names a live pid)."""
    found = []
    for f in sorted(pathlib.Path(lock_dir).glob("*.json")):
        try:
            d = json.loads(f.read_text())
            pid = int(d.get("pid"))
        except Exception:
            continue
        if pid == me:
            continue
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue                    # a stale lock of a build that died
        except PermissionError:
            pass                        # alive, another user's process
        try:                            # a killed build leaves its lock; its pid can be reused by anything else
            cmd = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=10).stdout
            if cmd.strip() and "build.py" not in cmd:
                continue
        except Exception:
            pass
        found.append("%s (pid %d)" % (d.get("slot"), pid))
    return found


def git_changed_since(start, paths, root=ROOT):
    """The paths a commit made after `start` touched (`git diff --name-only start..HEAD`), None when git cannot tell."""
    try:
        r = subprocess.run(["git", "diff", "--name-only", "%s..HEAD" % start, "--", *paths], cwd=root, capture_output=True, text=True, timeout=20)
        return set(l.strip() for l in r.stdout.splitlines() if l.strip()) if r.returncode == 0 else None
    except Exception:
        return None


# ------------------------------------------------------------------------------------------- 2. published check
def _versions(freya, wid):
    return freya.api("GET", "/api/v2/versions/workflow/%s" % wid, workspaceId=freya.workspace_id())["versions"]


def _strip(obj):
    """A platform workflow made fit to send again: no agent_config (the kit's update sets the model), no nulls."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if v is not None and k != "agent_config"}
    if isinstance(obj, list):
        return [_strip(v) for v in obj if v is not None]
    return obj


def retry5xx(fn, tries=10, wait=20, log=None):
    """fn() again after a 5xx from Freya (the platform answered 500/503/504 for an hour on 11 Oct: 'API key validation is
    temporarily unavailable', gateway time-outs). Any other error, or the last try, raises."""
    import re, time
    for i in range(tries):
        try:
            return fn()
        except RuntimeError as e:
            if not re.search(r"-> 5\d\d", str(e)) or i == tries - 1:
                raise
            if log:
                log("Freya answered %s; retrying in %d s" % (str(e)[:90], wait))
            time.sleep(wait)


def ensure_published(freya, wid):
    """Returns (published version number, note). The newest version must be published and the agent must run on
    freya.AGENT_LLM; otherwise the kit's calls fix it (update_workflow re-saves the same definition, sets the model
    and publishes; a model that is already right only needs the publish call)."""
    vs = _versions(freya, wid)
    newest = max(vs, key=lambda v: v["versionNumber"])
    w = freya.api("GET", "/api/v2/workflow/%s" % wid, workspaceId=freya.workspace_id())["workflow"]["workflow"]
    llm = (w.get("agent_config") or {}).get("llmConfig") or {}
    want = (freya.AGENT_LLM["provider"], freya.AGENT_LLM["model"])
    have = (llm.get("provider"), llm.get("model"))
    if have != want:
        v = freya.update_workflow(wid, _strip(w))
        return v, "agent model was %s/%s, not %s/%s: saved again with the event's model and published (version %d)" % (have + want + (v,))
    if not newest.get("isPublished"):
        freya.api("POST", "/api/v2/versions/workflow/%s/publish" % wid, {"versionId": newest["id"]})
        return newest["versionNumber"], "newest version %d was not published: published it" % newest["versionNumber"]
    return newest["versionNumber"], "newest version %d is published, agent model %s/%s" % ((newest["versionNumber"],) + want)


# ------------------------------------------------------------------------------------------- 3. best tested version
# failures builder/sim.py gives that are not the agent's: the harness, the mock bank, the judge, the chat route
INFRA_PREFIXES = ("harness", "mock bank: could not open", "mock bank: no ledger", "mock bank: the ledger could not be scored",
                  "conversation: no call was started", "conversation: no transcript to judge", "conversation: judge model failed",
                  "conversation: no verdict")
INFRA_STOPS = ("3 server errors", "customer model failed", "no call started", "no practice session", "harness error")


def is_infra(row):
    """A run that says nothing about the agent: a harness, mock bank, judge or customer-model failure, a call the chat
    route branched from an older message, or one cut short by server errors. 'Two empty replies' stays the agent's."""
    if row.get("chat_branched") or str(row.get("stop") or "").startswith(INFRA_STOPS):
        return True
    return any(str(f).startswith(INFRA_PREFIXES) for f in row.get("failed") or [])


def record_result(path, row, case_id, rep, workflow_id, cases_file):
    """One line per finished case (builder/sim.py calls this). Never raises."""
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {"t": time.time(), "at": time.strftime("%Y-%m-%d %H:%M:%S"), "workflow_id": workflow_id, "case": case_id,
               "rep": rep, "pass": bool(row.get("pass")), "version": row.get("version"), "version_id": row.get("version_id"),
               "infra": is_infra(row), "stop": row.get("stop"), "cases_file": cases_file}
        with open(p, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def results_by_version(path, since):
    """{version: {case: [pass, ...]}} from the ledger, rows written at or after `since` (epoch seconds), agent rows only."""
    out = {}
    p = pathlib.Path(path)
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("t", 0) < since or r.get("infra") or not r.get("version"):
            continue
        out.setdefault(int(r["version"]), {}).setdefault(r["case"], []).append(bool(r["pass"]))
    return out


def choose_version(results, final, min_common=4, margin=2.0):
    """(version to ship, reason). The final version stays unless it was tested and, on the cases it shares with the
    version tested just before it (at least `min_common`), passed at least `margin` fewer while passing none that the
    earlier one failed (pass rates when a case ran more than once). One run per case is noisy: anything less clear
    keeps the final version, and an untested final always stays (it holds fixes for what the last test found)."""
    if not results:
        return final, "no case results were recorded during this build"
    older = sorted(v for v in results if v < final)
    if final not in results:
        return final, "the final version %d was not tested after its last change%s; it stays" % (
            final, " (last tested: version %d)" % older[-1] if older else "")
    if not older:
        return final, "only the final version %d was tested" % final
    prev = older[-1]
    common = sorted(set(results[prev]) & set(results[final]))
    if len(common) < min_common:
        return final, "versions %d and %d share %d tested case(s), fewer than %d: the final version stays" % (prev, final, len(common), min_common)
    rate = lambda r, c: sum(r[c]) / len(r[c])
    worse = {c: rate(results[prev], c) - rate(results[final], c) for c in common}
    lost = sum(d for d in worse.values() if d > 0)
    gained = sum(-d for d in worse.values() if d < 0)
    if lost - gained >= margin and gained == 0:
        return prev, "the final version %d passed %.1f fewer of the %d cases it shares with version %d and none more (%s)" % (
            final, lost, len(common), prev, ", ".join(c for c, d in worse.items() if d > 0))
    return final, "the final version %d against version %d on %d shared cases: %.1f lost, %.1f gained; it stays" % (
        final, prev, len(common), lost, gained)


def restore_version(freya, slot, wid, version):
    """Save the definition of an earlier version again (dry run first) and publish it. Returns (new version, definition)."""
    vs = _versions(freya, wid)
    vid = next(v["id"] for v in vs if v["versionNumber"] == version)
    snap = freya.api("GET", "/api/v2/versions/workflow/%s/%s" % (wid, vid), workspaceId=freya.workspace_id())["version"]["configSnapshot"]
    wf = _strip(snap)
    freya.validate_workflow(slot, wf)
    return freya.update_workflow(wid, wf), wf


def write_state_version(state_file, slot, version):
    """Set .freya-agents.json[slot]['version'] from a fresh read, written atomically (other builds may save meanwhile)."""
    p = pathlib.Path(state_file)
    state = json.loads(p.read_text()) if p.exists() else {}
    if slot in state:
        state[slot]["version"] = version
        tmp = p.with_name(p.name + ".%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(state, indent=1))
        os.replace(tmp, p)
