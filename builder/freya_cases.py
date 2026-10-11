"""Run extended (rule-branch) cases on the organisers' simulator, scored like tools/run_cases.py.

    python3 builder/freya_cases.py <agent_id> --cases tests/cases/brief-a-extended.cases.json [--chunk 14] [--style corrects]
                                   [--only EXT-A-01,EXT-A-02] [--reps 1] [--out results/freya-ext-a.json]

The difference from tools/run_cases.py (a kit file, kept as shipped): an extended case reuses a mock customer
under its own id, so the practice session is opened for case["mock_case"] (fallback: the case id), and the
case's own call date replaces the session's variables["now"] (the mock enforces no date rule). Cases run
--chunk at a time, one simulation per chunk (the workspace runs one simulation at a time). Personas, the
ledger check and the judge are the kit's: persona_for, http, score_ledger. Costs Freya credits.
"""
import argparse, hashlib, json, pathlib, re, sys, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
import freya
from score import http, score_ledger
from run_cases import STYLES, persona_for


def personas(cases, style):
    """Persona ids for the cases, created when the text is new (same store and key scheme as run_cases.py)."""
    store = ROOT / ".personas.json"; ids = json.load(open(store)) if store.exists() else {}
    spec = {c["id"]: persona_for(c, {"identity": c["identity"]}, style) for c in cases}
    key = {i: i + ":" + hashlib.sha1(json.dumps(p, sort_keys=True).encode()).hexdigest()[:10] for i, p in spec.items()}
    new = [c for c in cases if key[c["id"]] not in ids]
    if new:
        made = freya.create_personas([spec[c["id"]] for c in new])["personas"]
        ids.update({key[c["id"]]: p["id"] for c, p in zip(new, made)}); json.dump(ids, open(store, "w"), indent=1)
    return {c["id"]: ids[key[c["id"]]] for c in cases}


def session(case):
    s = http("/v1/practice/sessions", {"case": case.get("mock_case") or case["id"]})
    v = dict((s or {}).get("variables") or {})
    if not v: raise RuntimeError(f"mock bank: no practice session for {case.get('mock_case') or case['id']}: {s}")
    if (case.get("variables") or {}).get("now"): v["now"] = case["variables"]["now"]
    return v


def slowest_turn(call):
    last_user, worst = None, 0.0
    for m in call.get("messages", []):
        t = m.get("secondsFromStart")
        if t is None: continue
        if m.get("role") == "user": last_user = t
        elif last_user is not None: worst = max(worst, t - last_user); last_user = None if m.get("role") == "assistant" else last_user
    return round(worst, 1)


def close_from_args(led):
    """--close-from-args: the organisers' mock checks close_call reasons against the KIT briefs' table, so a synthetic brief
    with its own codes gets ok:false and an empty ledger outcome. Score the outcome/reason the agent SENT in its last
    close_call instead (as builder/sim.py does). Only when the ledger outcome is empty."""
    if led.get("outcome"):
        return led, None
    closes = [c for c in led.get("calls") or [] if c.get("tool") == "close_call"]
    if not closes:
        return led, None
    args = closes[-1].get("args") or {}
    return dict(led, outcome=args.get("outcome"), reason=args.get("reason")), args


def _retry(fn, tries=12, wait=15):
    # a gateway error (502/503/504) from Freya while polling is transient: try again
    for i in range(tries):
        try:
            return fn()
        except RuntimeError as e:
            if not re.search(r"-> 5\d\d", str(e)) or i == tries - 1:
                raise
            print("Freya answered %s; retrying in %d s" % (str(e)[:80], wait), flush=True)
            time.sleep(wait)


def run_simulation(agent_id, name, variables):
    """freya.run_simulation, but a 502/503/504 while it polls no longer loses the run (two runs lost on 11 Oct): the
    simulation id comes from the error, and polling and the iteration lookup go on with retries."""
    for attempt in range(40):          # the start itself: a gateway error or an API outage ('API key validation is
        try:                           # temporarily unavailable', 503) is retried for up to 20 minutes
            return freya.run_simulation(agent_id, name, variables)
        except RuntimeError as e:
            m = re.search(r"/api/v2/simulations/([0-9a-f-]{36})(?:/iterations)? -> 5\d\d", str(e))
            if m:
                sim_id = m.group(1)
                print("Freya answered %s while polling simulation %s; polling again" % (str(e)[:60], sim_id), flush=True)
                break
            if not re.search(r"POST /api/v2/simulations -> 5\d\d", str(e)) or attempt == 39:
                raise
            print("Freya answered %s when starting; retrying in 30 s" % str(e)[:80], flush=True)
            time.sleep(30)
    while True:
        time.sleep(10)
        s = _retry(lambda: freya.api("GET", f"/api/v2/simulations/{sim_id}"))
        s = s.get("simulation") or s
        if s.get("status") in ("completed", "failed", "paused"):
            break
    its = _retry(lambda: freya.api("GET", f"/api/v2/simulations/{sim_id}/iterations"))
    its = its.get("iterations") or its.get("items") or its
    return sim_id, its[0]["id"], s.get("status")


def run_chunk(agent_id, cases, ids, from_args=False):
    sessions = {c["id"]: session(c) for c in cases}
    t0 = time.time()
    sim_id, it_id, status = run_simulation(agent_id, f"ext {time.strftime('%H:%M:%S')}", {ids[c["id"]]: sessions[c["id"]] for c in cases})
    took = time.time() - t0
    judge = {r["personaId"]: r for r in _retry(lambda: freya.get_iteration(sim_id, it_id))["runs"]}
    rows = []
    for c in cases:
        led = http("/v1/practice/ledger/" + sessions[c["id"]]["customer_id"])
        sent = None
        if from_args:
            led, sent = close_from_args(led)
        r = score_ledger(c, led)
        j = judge.get(ids[c["id"]], {})
        if j.get("outcome") != "pass": r["failed"].append("conversation: " + " ".join(str(j.get("reason") or "no verdict").split())[:400])
        row = {"id": c["id"], "mock_case": c.get("mock_case"), "level": c["level"], "family": c["family"], "pass": not r["failed"], "failed": r["failed"],
               "call_id": j.get("callId"), "tools": [x["tool"] for x in led["calls"]], "customer_id": sessions[c["id"]]["customer_id"],
               "now": sessions[c["id"]].get("now"), "simulation_id": sim_id, "close_from_args": sent}
        if row["call_id"]:
            try:
                call = freya.get_call(row["call_id"]); row["slowest_turn_s"] = slowest_turn(call); row["ended"] = call.get("endedReason")
            except Exception: pass
        rows.append(row)
        print(("PASS" if row["pass"] else "FAIL"), c["id"], f"{c['level']:<6}", f"{c['family']:<14}", "|",
              " > ".join(x["tool"].replace("verify_identity", "verify").replace("create_promise", "promise") for x in led["calls"]) or "(no tool calls)", flush=True)
        for f in row["failed"]: print("       -", f[:260])
    waits = sorted(r["slowest_turn_s"] for r in rows if "slowest_turn_s" in r)
    if waits: print(f"chunk: {sum(r['pass'] for r in rows)}/{len(rows)} passed, {took:.0f} s, slowest turn median {waits[len(waits) // 2]:.0f} s, worst {waits[-1]:.0f} s\n", flush=True)
    return rows, took


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent_id"); ap.add_argument("--cases", required=True); ap.add_argument("--chunk", type=int, default=14)
    ap.add_argument("--style", choices=sorted(STYLES)); ap.add_argument("--only"); ap.add_argument("--reps", type=int, default=1); ap.add_argument("--out")
    ap.add_argument("--close-from-args", action="store_true", help="score the outcome/reason sent in close_call when the mock rejected it (synthetic briefs with their own codes)")
    a = ap.parse_args()
    cases = [c for c in json.load(open(a.cases)) if not a.only or c["id"] in a.only.split(",")]
    if not cases: sys.exit("no cases")
    ids = personas(cases, a.style)
    reps, total = [], 0
    for rep in range(a.reps):
        rows = []
        for k in range(0, len(cases), a.chunk):
            r, took = run_chunk(a.agent_id, cases[k:k + a.chunk], ids, a.close_from_args); rows += r; total += took
        reps.append(rows)
        if a.reps > 1: print(f"-- run {rep + 1} of {a.reps}: {sum(r['pass'] for r in rows)} / {len(rows)} passed\n")
    final = [{"id": c["id"], "family": c["family"], "passes": sum(r[k]["pass"] for r in reps), "runs": a.reps, "pass": all(r[k]["pass"] for r in reps)} for k, c in enumerate(cases)]
    n = sum(f["pass"] for f in final)
    print(f"{n} / {len(final)} passed{'' if a.reps == 1 else f' (all {a.reps} runs)'}; failed: {','.join(f['id'] for f in final if not f['pass']) or '-'}; {total:.0f} s")
    (ROOT / "results").mkdir(exist_ok=True)
    with open(ROOT / "results" / "log.jsonl", "a") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%d %H:%M:%S"), "agent_id": a.agent_id, "cases": a.cases, "style": a.style, "runs": a.reps, "passed": n,
                            "total": len(final), "seconds": round(total), "failed": [f["id"] for f in final if not f["pass"]], "runner": "freya_cases"}) + "\n")
    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump({"agent_id": a.agent_id, "cases": a.cases, "style": a.style, "passed": n, "total": len(final), "runs": a.reps, "seconds": round(total),
                   "final": final, "rows": reps[-1], "all_rows": reps}, open(a.out, "w"), indent=1)


if __name__ == "__main__": main()
