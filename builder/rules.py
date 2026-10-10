#!/usr/bin/env python3
"""Rule inventory: Claude reads the brief(s) and the tool API file and lists every rule as structured JSON.

    source env.sh   # not needed for this script, but harmless
    .venv/bin/python builder/rules.py briefs/brief-a.md --api tools/openapi.json --out out/brief-a.rules.json
    .venv/bin/python builder/rules.py briefs/brief-a.md briefs/brief-b.md --api tools/openapi.json --out out/brief-b.rules.json

As a function:

    from rules import extract_rules
    rules = extract_rules(["briefs/brief-a.md"], "tools/openapi.json", "out/brief-a.rules.json")

Output: <out> is a JSON list of rules
  {"id": "R01", "source": "brief-a.md rule 6", "category": "<see CATEGORIES>", "text": "...", "verbatim": [...],
   "values": {...}, "overrides": "" | "R07", "in_force": true | false, "superseded_by": "R52"}
and <out with .md> is a Markdown rendering of the same list.

A brief can be one Markdown file with several documents in it (a mail, a policy extract, a memo, a code list). When a later
document changes an earlier rule, the inventory has the new rule with "overrides": "<id of the old rule>", the old rule gets
"in_force": false and "superseded_by", and only rules in force are audited by builder/audit.py.

After extraction the script checks the inventory itself: every numbered rule of every brief must be cited by at least one
inventory rule, and every ISO date and every `backticked` token of the brief must appear somewhere in the inventory. Missing
numbered rules trigger one gap-fill call. Invalid JSON triggers one retry.

Needs a Claude login (or ANTHROPIC_API_KEY). RULES_MODEL overrides the model (default claude-opus-5-5).
Progress and every model call go to stderr ("model call: <model> | purpose: ..."); the one-line summary goes to stdout.
"""
import argparse, asyncio, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-opus-5-5"
MAX_BUDGET_USD_PER_CALL = 6.0

CATEGORIES = ["opening", "third_party", "identity", "disclosure", "dates", "amounts", "persuasion", "hardship",
              "confirmation", "recording", "special", "multi_product", "closing", "wording", "other"]

RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "R01, R02, ... in document order"},
                    "source": {"type": "string", "description": "e.g. 'brief-a.md rule 6', 'brief-a.md section 7 table row early', 'memo 2026-10-12', 'openapi.json /close_call'"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "text": {"type": "string", "description": "the rule in force, one or two sentences, numbers/dates/enum values quoted exactly"},
                    "verbatim": {"type": "array", "items": {"type": "string"}, "description": "sentences the agent must say word for word, if any"},
                    "values": {"type": "object", "description": "structured values when present (lists, bands, mappings, windows, limits)"},
                    "overrides": {"type": "string", "description": "id of the earlier rule this one replaces, else empty string"},
                },
                "required": ["id", "source", "category", "text", "verbatim", "values", "overrides"],
            },
        }
    },
    "required": ["rules"],
}

SYSTEM_PROMPT = """You are a meticulous compliance analyst. You read a bank's specification for an automated outbound phone call
(a "brief": one or more Markdown documents) plus the bank's tool API (OpenAPI JSON) and you write the complete RULE INVENTORY:
every obligation, prohibition, value, threshold, mapping and mandatory sentence that a phone agent built from this brief must
follow. The inventory is later used to audit the agent, so completeness and exactness matter more than brevity.

OUTPUT: JSON {"rules": [...]} matching the schema you are given. Nothing else.

WHAT COUNTS AS A RULE (list ALL of them, in document order):
1. Every numbered rule of every document. One inventory rule per numbered rule by default. Split a numbered rule into two or
   more inventory rules ONLY when it contains clearly independent obligations (for example: a wording rule plus a closing
   outcome). Each part cites the same source number ("brief-a.md rule 3").
2. Every table: the table as a whole is a rule, and every row is in "values" (bands, outcome/reason mapping, call
   variables, code lists, holidays). Quote every cell value exactly.
3. Every unnumbered sentence that constrains behaviour: definitions (business days, holidays, windows), "never" / "always" /
   "only" statements, notes under tables ("If a transfer follows a recorded promise ..."), statements that a tool is not used,
   what is known at the start of the call, how to address the customer, the language to speak.
4. Every sentence the agent must say word for word goes into "verbatim" (exact text, including punctuation), and the rule
   text says when it is said.
5. Tool API constraints that the brief does not state itself and that change what the agent must do: required fields,
   enum values, formats, "one per product", "always the last call". Source: "openapi.json /<path>". Do not list API
   facts the brief already states; put them in the brief rule's "values" instead (e.g. the queue names, the enum values).
6. For a brief made of several documents (a covering mail, a policy extract, a memo, a code list, an older version and a
   newer one): list the rules of every document. When a later document changes, tightens, relaxes or withdraws an earlier
   rule, write the NEW rule in force with "overrides": "<id of the earlier rule>" and say in its text what changed and
   since when. The new rule's text and values must be SELF-CONTAINED: the complete rule now in force (what stays from the
   old rule plus what changed), because the old rule is no longer audited. A later rule that only ADDS to an earlier one
   without changing it is a new rule with "overrides": "" (the earlier rule stays in force). The earlier rule stays in
   the list with its original text. When documents conflict without saying which wins, the most recent dated document
   wins; say so in the text. Use "source" like "memo 2026-10-12" or "policy extract v3 rule 4" so a reader can find it.

FIELDS:
- "id": R01, R02, ... in order. Never reuse an id.
- "category": opening (first sentence, who is on the line, confirmation of identity of the person), third_party (someone
  else answers, callbacks), identity (security questions, wrong answers, declining), disclosure (what may or may not be said
  before/after verification, to whom), dates (business days, holidays, deadlines, how to read dates, weekday words),
  amounts (full amount, floor, accepted ranges), persuasion (attempts, what to propose, when to stop), hardship (illness,
  death, job loss, support transfer), confirmation (read-back, confirm question, changes at read-back), recording (tool
  call rules for recording a promise/note/callback, retries, "recorded" wording), special (already paid, dispute,
  restructuring, human, scam, robot, unanswerable questions, does not want to talk), multi_product (several products),
  closing (close_call outcomes/reasons, last tool call, thanks and goodbye), wording (how to address, language, forbidden
  words, mandatory sentences not tied to another category), other (call variables, API constraints, anything else).
- "text": the rule in force in one or two sentences. Quote numbers, dates, times, enum values and tool names exactly as in
  the document (keep `backticks` around identifiers). If the rule depends on another rule, name it ("see rule 30").
- "values": structured data when present, with descriptive keys, for example:
  {"holidays": ["2026-10-26", ...]}, {"business_days": "Mon-Fri except holidays"},
  {"bands": [{"name": "early", "min_days": 1, "max_days": 7, "deadline_rule": "12th business day after today", "attempts": 1}, ...]},
  {"floor": {"credit_card": "minimum_payment", "personal_loan": "instalment_amount"}},
  {"callback_window": {"days": "today or next business day", "from": "10:00", "to": "19:00", "later_than_now": true}},
  {"outcomes": [{"outcome": "not_reached", "reason": "callback", "when": "rule 6"}, ...]},
  {"identity_fields": ["date_of_birth", "phone_last4"], "max_wrong_answers": 3},
  {"confirmation_words": ["yes", "that's me", "speaking", "own name"], "not_confirmation": ["hello", "go ahead", "who is this"]},
  {"tool": "close_call", "queue": "support", "outcome": "transferred", "reason": "support"}.
  Use {} when there is nothing structured.
- "verbatim": [] when nothing must be said word for word.
- "overrides": "" unless this rule replaces an earlier listed rule.

Be exhaustive: a brief of 47 numbered rules with three tables and a few definitions yields 50 to 65 inventory rules.
Do not summarise several numbered rules into one. Do not skip a rule because it looks obvious or repeats another one.
Do not invent rules that are not in the documents."""


# ----------------------------------------------------------------------------------------------- Claude call
def _parse_json_text(text):
    """Find the first JSON object or list in a model answer (handles code fences and chatter)."""
    if text is None:
        raise ValueError("empty answer")
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    starts = [i for i in (s.find("{"), s.find("[")) if i >= 0]
    if not starts:
        raise ValueError("no JSON in answer")
    i = min(starts)
    dec = json.JSONDecoder()
    obj, _ = dec.raw_decode(s[i:])
    return obj


async def ask_json_async(prompt, system_prompt, schema, purpose, model=None, max_budget_usd=MAX_BUDGET_USD_PER_CALL,
                         log=None, effort=None):
    """One Claude call, no tools, structured JSON out. Returns (obj, info). Retries once on invalid JSON.

    info = {"model", "cost_usd", "seconds", "turns", "attempts", "usage"}
    """
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query
    model = model or os.environ.get("RULES_MODEL") or DEFAULT_MODEL
    log = log or (lambda s: print(s, file=sys.stderr, flush=True))
    info = {"model": model, "cost_usd": 0.0, "seconds": 0.0, "turns": 0, "attempts": 0, "usage": {}}
    last_err = None
    for attempt in range(2):
        info["attempts"] = attempt + 1
        t0 = time.time()
        log("model call: %s | purpose: %s%s" % (model, purpose, " (retry after invalid JSON)" if attempt else ""))
        options = ClaudeAgentOptions(
            cwd=str(ROOT), model=model, tools=[], allowed_tools=[], permission_mode="dontAsk", max_turns=4,
            setting_sources=[], system_prompt=system_prompt, max_budget_usd=max_budget_usd,
            output_format={"type": "json_schema", "schema": schema}, effort=effort)
        p = prompt if not attempt else (prompt + "\n\nYour previous answer was not valid JSON for the schema (%s). "
                                                 "Answer again with valid JSON only." % last_err)
        text, structured, result = "", None, None
        async for m in query(prompt=p, options=options):
            if isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, TextBlock):
                        text += b.text
            elif isinstance(m, ResultMessage):
                result = m
                structured = m.structured_output
                info["cost_usd"] += m.total_cost_usd or 0.0
                info["turns"] += m.num_turns or 0
                info["usage"] = m.usage or {}
        info["seconds"] += time.time() - t0
        if result is not None and result.is_error:
            last_err = "result error: %s %s" % (result.subtype, (result.errors or [result.result])[:1])
            log("model call failed: " + last_err)
            continue
        try:
            obj = structured if structured is not None else _parse_json_text(result.result if result and result.result else text)
            return obj, info
        except Exception as e:
            last_err = "%s: %s" % (type(e).__name__, e)
            log("invalid JSON: " + last_err)
    raise RuntimeError("Claude did not return valid JSON after 2 attempts: %s" % last_err)


def ask_json(*a, **kw):
    return asyncio.run(ask_json_async(*a, **kw))


# ----------------------------------------------------------------------------------------------- inputs
def api_digest(api_path):
    """A compact text of the tool API: path, summary, body fields with enums/formats/descriptions, required."""
    api = json.load(open(api_path))
    out = ["Tool API file: %s" % pathlib.Path(api_path).name]
    for p, v in (api.get("paths") or {}).items():
        op = v.get("post") or v.get("get") or next(iter(v.values()), {})
        out.append("- %s: %s" % (p, " ".join((op.get("summary") or op.get("description") or "").split())))
        body = ((op.get("requestBody") or {}).get("content") or {}).get("application/json", {}).get("schema", {})
        req = body.get("required") or []
        for f, fs in (body.get("properties") or {}).items():
            bits = [fs.get("type", "")]
            if fs.get("enum"):
                bits.append("enum " + json.dumps(fs["enum"]))
            if fs.get("format"):
                bits.append("format " + fs["format"])
            if fs.get("description"):
                bits.append(" ".join(fs["description"].split()))
            out.append("    %s%s: %s" % (f, "*" if f in req else "", "; ".join(b for b in bits if b)))
        resp = ((op.get("responses") or {}).get("200") or {}).get("content", {}).get("application/json", {}).get("schema", {})
        if resp:
            out.append("    response: " + json.dumps(resp)[:700])
    out.append("(* = required field)")
    return "\n".join(out)


def read_briefs(briefs):
    parts = []
    for b in briefs:
        p = pathlib.Path(b)
        parts.append("=" * 20 + " DOCUMENT FILE: %s " % p.name + "=" * 20 + "\n" + p.read_text())
    return "\n\n".join(parts)


# ----------------------------------------------------------------------------------------------- self-check
def numbered_rules(text):
    """Numbers of the numbered rules in a Markdown document (lines like '12. ...', not table rows)."""
    nums = []
    for line in text.splitlines():
        m = re.match(r"^\s{0,3}(\d{1,3})\.\s+\S", line)
        if m and not line.lstrip().startswith("|"):
            nums.append(int(m.group(1)))
    return nums


def _flatten_text(obj, acc=None):
    """All strings of a JSON object joined with newlines (no JSON escaping, so quoted tokens match)."""
    acc = [] if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.append(str(k)); _flatten_text(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _flatten_text(v, acc)
    else:
        acc.append(str(obj))
    return acc


def cited_numbers(rule, fname):
    """Rule numbers that a rule's source cites (e.g. 'rule 6', 'rules 30 and 41', 'rules 3-5')."""
    src = rule.get("source", "")
    nums = set()
    for m in re.finditer(r"(?:rules?|items?|points?|paragraphs?|clauses?|nos?\.|#)\s*([\d,\s\-–and&]+)", src, re.I):
        chunk = m.group(1)
        for a, b in re.findall(r"(\d+)\s*[-–]\s*(\d+)", chunk):
            nums.update(range(int(a), int(b) + 1))
        for n in re.findall(r"\d+", re.sub(r"(\d+)\s*[-–]\s*(\d+)", " ", chunk)):
            nums.add(int(n))
    return nums


def self_check(rules, briefs):
    """Deterministic completeness check. Returns {"missing_numbers": {file: [n,...]}, "missing_tokens": [...]}"""
    dump = "\n".join(_flatten_text(rules)).lower()
    missing_numbers, missing_tokens = {}, []
    for b in briefs:
        text = pathlib.Path(b).read_text()
        fname = pathlib.Path(b).name
        nums = numbered_rules(text)
        cited = set()
        for r in rules:
            src = r.get("source", "")
            # a source cites this file when it names it, or when there is only one brief
            if fname in src or pathlib.Path(b).stem in src or len(briefs) == 1:
                cited |= cited_numbers(r, fname)
        miss = sorted(n for n in nums if n not in cited)
        if miss:
            missing_numbers[fname] = miss
        for tok in sorted(set(re.findall(r"\d{4}-\d{2}-\d{2}", text))):
            if tok not in dump:
                missing_tokens.append(tok)
        for tok in sorted(set(re.findall(r"`([^`\n]{2,40})`", text))):
            t = tok.lower()
            if t not in dump and t.replace("`", "") not in dump:
                missing_tokens.append(tok)
    return {"missing_numbers": missing_numbers, "missing_tokens": sorted(set(missing_tokens))}


# ----------------------------------------------------------------------------------------------- normalise
def normalise(rules):
    """Validate shape, renumber ids in order, resolve overrides, mark in_force / superseded_by."""
    if isinstance(rules, dict):
        rules = rules.get("rules", [])
    if not isinstance(rules, list) or not rules:
        raise ValueError("inventory is not a non-empty list")
    clean, old_to_new = [], {}
    for i, r in enumerate(rules):
        if not isinstance(r, dict) or not r.get("text"):
            raise ValueError("rule %d has no text" % i)
        new_id = "R%02d" % (i + 1)
        old_to_new[str(r.get("id", new_id))] = new_id
        cat = r.get("category") if r.get("category") in CATEGORIES else "other"
        verb = r.get("verbatim") or []
        if isinstance(verb, str):
            verb = [verb]
        vals = r.get("values") if isinstance(r.get("values"), dict) else {}
        clean.append({"id": new_id, "source": str(r.get("source", "")), "category": cat, "text": str(r["text"]).strip(),
                      "verbatim": [str(v) for v in verb], "values": vals, "overrides": str(r.get("overrides") or ""),
                      "in_force": True, "superseded_by": ""})
    by_id = {r["id"]: r for r in clean}
    for r in clean:
        if r["overrides"]:
            tgt = old_to_new.get(r["overrides"], r["overrides"])
            if tgt in by_id and tgt != r["id"]:
                r["overrides"] = tgt
                by_id[tgt]["in_force"] = False
                by_id[tgt]["superseded_by"] = r["id"]
            else:
                r["overrides"] = ""
    return clean


# ----------------------------------------------------------------------------------------------- rendering
def render_md(rules, briefs, api_path, meta=None):
    L = ["# Rule inventory: %s" % ", ".join(pathlib.Path(b).name for b in briefs), ""]
    L.append("Tool API: `%s`. %d rules (%d in force, %d superseded)." % (
        pathlib.Path(api_path).name, len(rules), sum(r["in_force"] for r in rules), sum(not r["in_force"] for r in rules)))
    if meta:
        L.append("Model %s, %.0f s, $%.2f, %d call(s)." % (meta.get("model"), meta.get("seconds", 0), meta.get("cost_usd", 0), meta.get("calls", 0)))
        chk = meta.get("self_check") or {}
        if chk.get("missing_numbers") or chk.get("missing_tokens"):
            L.append("Self-check: missing numbered rules %s; missing tokens %s." % (chk.get("missing_numbers"), chk.get("missing_tokens")))
        else:
            L.append("Self-check: every numbered rule is cited; every date and backticked token of the brief appears in the inventory.")
    L.append("")
    for cat in CATEGORIES:
        rs = [r for r in rules if r["category"] == cat]
        if not rs:
            continue
        L.append("## %s (%d)" % (cat, len(rs)))
        L.append("")
        for r in rs:
            flag = "" if r["in_force"] else " **[superseded by %s]**" % r["superseded_by"]
            ov = " (overrides %s)" % r["overrides"] if r["overrides"] else ""
            L.append("- **%s**%s%s — _%s_: %s" % (r["id"], flag, ov, r["source"], r["text"]))
            for v in r["verbatim"]:
                L.append("  - verbatim: \"%s\"" % v)
            if r["values"]:
                L.append("  - values: `%s`" % json.dumps(r["values"], ensure_ascii=False))
        L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------------------------------- main
async def extract_rules_async(briefs, api_path, out_path, model=None, log=None):
    log = log or (lambda s: print(s, file=sys.stderr, flush=True))
    t0 = time.time()
    model = model or os.environ.get("RULES_MODEL") or DEFAULT_MODEL
    docs = read_briefs(briefs)
    api = api_digest(api_path)
    prompt = ("Write the complete rule inventory for the brief below.\n\n"
              "BRIEF DOCUMENT(S):\n\n%s\n\n%s\n\n"
              "Reminder: every numbered rule, every table row, every definition and every mandatory sentence. "
              "Use the file names above in \"source\" (e.g. \"%s rule 12\"). Answer with the JSON only."
              % (docs, api, pathlib.Path(briefs[-1]).name))
    obj, info = await ask_json_async(prompt, SYSTEM_PROMPT, RULE_SCHEMA, "extract the rule inventory from %s" % ", ".join(
        pathlib.Path(b).name for b in briefs), model=model, log=log)
    rules = normalise(obj)
    cost, calls = info["cost_usd"], info["attempts"]
    chk = self_check(rules, briefs)
    log("inventory: %d rules | self-check: missing numbered rules %s, missing tokens %s" % (
        len(rules), chk["missing_numbers"] or "none", chk["missing_tokens"] or "none"))
    if chk["missing_numbers"] or chk["missing_tokens"]:
        # one gap-fill pass: ask for the missing items only, then merge and renumber
        gaps = []
        for f, nums in chk["missing_numbers"].items():
            gaps.append("%s: numbered rules %s" % (f, ", ".join(map(str, nums))))
        if chk["missing_tokens"]:
            gaps.append("these values/tokens from the brief appear nowhere in the inventory: %s" % ", ".join(chk["missing_tokens"]))
        existing = "\n".join("%s | %s | %s" % (r["id"], r["source"], r["text"]) for r in rules)
        gp = ("The inventory below was extracted from the brief but is incomplete.\n\nMISSING:\n- %s\n\n"
              "EXISTING INVENTORY (id | source | text):\n%s\n\nBRIEF DOCUMENT(S):\n\n%s\n\n%s\n\n"
              "Return ONLY the rules that must be ADDED to cover the missing items (same schema, ids starting at R%02d). "
              "If a missing token belongs in an existing rule's values, return that rule again with the same id and the completed values; "
              "it will replace the existing one. Do not return rules that are already complete."
              % ("\n- ".join(gaps), existing, docs, api, len(rules) + 1))
        obj2, info2 = await ask_json_async(gp, SYSTEM_PROMPT, RULE_SCHEMA, "gap-fill the rule inventory (%s)" % "; ".join(gaps)[:160],
                                           model=model, log=log)
        cost += info2["cost_usd"]; calls += info2["attempts"]
        added = obj2.get("rules", []) if isinstance(obj2, dict) else obj2
        by_id = {r["id"]: r for r in rules}
        n_rep = n_add = 0
        for r in added or []:
            if not isinstance(r, dict) or not r.get("text"):
                continue
            rid = str(r.get("id", ""))
            if rid in by_id:
                by_id[rid].update({k: r[k] for k in ("source", "category", "text", "verbatim", "values", "overrides") if k in r})
                n_rep += 1
            else:
                rules.append(r); n_add += 1
        rules = normalise(rules)
        chk = self_check(rules, briefs)
        log("gap-fill: %d added, %d replaced -> %d rules | self-check: missing numbered rules %s, missing tokens %s" % (
            n_add, n_rep, len(rules), chk["missing_numbers"] or "none", chk["missing_tokens"] or "none"))
    meta = {"model": model, "seconds": time.time() - t0, "cost_usd": cost, "calls": calls, "self_check": chk,
            "briefs": [str(b) for b in briefs], "api": str(api_path)}
    out = pathlib.Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rules, indent=1, ensure_ascii=False) + "\n")
    md = out.with_suffix(".md") if out.suffix == ".json" else pathlib.Path(str(out) + ".md")
    md.write_text(render_md(rules, briefs, api_path, meta))
    cats = {}
    for r in rules:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print("rules: %d (%d in force) -> %s + %s | %d model call(s), %.0f s, $%.2f | by category: %s | self-check: %s" % (
        len(rules), sum(r["in_force"] for r in rules), out, md.name, calls, meta["seconds"], cost,
        ", ".join("%s %d" % kv for kv in sorted(cats.items())),
        "ok" if not (chk["missing_numbers"] or chk["missing_tokens"]) else "gaps %s %s" % (chk["missing_numbers"], chk["missing_tokens"])),
        flush=True)
    return rules


def extract_rules(briefs, api_path, out_path, model=None, log=None):
    return asyncio.run(extract_rules_async(briefs, api_path, out_path, model=model, log=log))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract the rule inventory of a brief with Claude.")
    ap.add_argument("briefs", nargs="+", help="brief Markdown file(s), earlier briefs first")
    ap.add_argument("--api", required=True, help="tool API file (OpenAPI JSON)")
    ap.add_argument("--out", required=True, help="output JSON path, e.g. out/<slot>.rules.json")
    ap.add_argument("--model", default=None, help="builder model (default $RULES_MODEL or %s)" % DEFAULT_MODEL)
    a = ap.parse_args(argv)
    for p in a.briefs + [a.api]:
        if not pathlib.Path(p).exists():
            sys.exit("not found: " + p)
    extract_rules(a.briefs, a.api, a.out, model=a.model)


if __name__ == "__main__":
    main()
