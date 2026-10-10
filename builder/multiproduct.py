"""multiproduct: brief-agnostic helpers for Freya phone agents whose customer can be late on one to three products.

It generalises the machinery the organisers' example builder added in out/gen_brief-b.py (3/3 on the Brief B
practice cases): per-product facts prepared in code, a per-product state machine kept in workflow variables by the
pre/post hooks of the promise tool and the note tool, and a finalize code node that picks the closing outcome.
builder/freyalib.py holds the platform shapes (tools, nodes, transitions, guarded code); this module only produces
Python source for hooks and code nodes, plus the finalize transitions. builder/MULTIPRODUCT.md describes the state
machine and how a generator wires it.

Nothing in this module names a bank value: bands, floors, product wording, the spoken statement, tool names and
note reasons are parameters the generator reads from the brief and the tool API file.

Standard library only. Python 3.10+.

Variables the hooks and code nodes use (all strings, see MULTIPRODUCT.md):
    pids_csv   every product id, in get_account order, comma separated   (prepare)
    dl_<pid>   that product's deadline, YYYY-MM-DD                        (prepare; promise_pre caps the date)
    pd_<pid>   that product's past-due amount, str(float)                 (prepare; promise_pre caps the amount)
    rec_pids   ids with a recorded promise                                 (promise_post)
    note_log   "<pid>:<reason>" per noted product, comma separated         (note_post)
    open_pids  ids with neither a promise nor a note                       (prepare, _status)
    all_done   "yes" once open_pids is empty, else "no"                    (prepare, _status) -> ALL_DONE transition
    pending_pid, pending_note   what the current tool call is about        (promise_pre, note_pre)
    fail_<pid> failed promise calls for that product                       (promise_post)
    final_route  the fin key the finalize node chose                       (finalize)
"""
from __future__ import annotations

import pathlib
import re
import sys

try:
    import freyalib as fl
except ImportError:  # imported from somewhere other than builder/
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import freyalib as fl  # noqa: E402

ROUTE_VAR = "final_route"
STATE_VARS = ("pids_csv", "rec_pids", "note_log", "open_pids", "all_done", "pending_pid", "pending_note")


def _ident(name, what="name"):
    """Tool names and reasons are spliced into string literals of the generated code: identifiers only."""
    if not isinstance(name, str) or not re.fullmatch(r"\w+", name):
        raise ValueError("%s must be an identifier (letters, digits, _), got %r" % (what, name))
    return name


def _no_braces(code, where):
    if "{{" in code or "}}" in code:
        raise ValueError("%s: generated code contains '{{' or '}}' (check the templates)" % where)
    return code


# ----------------------------------------------------------------------------------------------- shared state
_STATE_FN = r"""
def _getv():
    try:
        return vars
    except Exception:
        return None
def _status(V):
    pids = [x for x in str(V.get('pids_csv') or '').split(',') if x]
    rec = [x for x in str(V.get('rec_pids') or '').split(',') if x]
    notes = [x for x in str(V.get('note_log') or '').split(',') if x]
    noted = [x.split(':')[0] for x in notes]
    opn = [x for x in pids if x not in rec and x not in noted]
    V['open_pids'] = ','.join(opn)
    V['all_done'] = 'yes' if pids and not opn else 'no'
    s = 'Recorded promises: ' + (', '.join(rec) or 'none') + '. Notes: ' + (', '.join(notes) or 'none') + '. '
    if opn:
        s += 'Still open: ' + ', '.join(opn) + __OPEN_TEXT__
    return s
"""


def state_fn_code(promise_tool="create_promise", note_tool="add_note", still_open_text=None):
    """Source defining, for a hook: _getv() (the `vars` dict, or None when the hook has no vars) and _status(V),
    which recomputes open_pids / all_done from pids_csv, rec_pids and note_log and returns the status sentence for
    what_to_do_next. `still_open_text` is the tail appended after 'Still open: p1, p2'."""
    _ident(promise_tool, "promise_tool")
    _ident(note_tool, "note_tool")
    if still_open_text is None:
        still_open_text = (". For each open product: if the customer confirmed a promise for it, call %s for it now; "
                           "otherwise call %s for it with the right reason. One tool call per message." % (promise_tool, note_tool))
    return _STATE_FN.replace("__OPEN_TEXT__", repr(still_open_text))


# ----------------------------------------------------------------------------------------------- promise hooks
_PROMISE_PRE = r"""
try:
    V = _getv()
    b = config.get('body')
    if isinstance(b, dict):
        pid = str(b.get(__PID__) or '').strip()
__PREFIX_BLOCK__        b[__PID__] = pid
        if __AMOUNT__ in b:
            b[__AMOUNT__] = float(str(b[__AMOUNT__]).replace(',', '').strip())
        if __DATE__ in b:
            b[__DATE__] = str(b[__DATE__]).strip()[:10]
        if V is not None:
            V['pending_pid'] = pid
__CAP_DATE____CAP_AMOUNT__except Exception:
    pass
"""
_PREFIX_BLOCK = """        if pid.isdigit():
            pid = __PREFIX__ + pid
"""
_CAP_DATE = """            dl = str(V.get('dl_' + pid) or '')
            if dl and b.get(__DATE__) and str(b[__DATE__]) > dl:
                b[__DATE__] = dl
"""
_CAP_AMOUNT = """            pd = V.get('pd_' + pid)
            if pd and float(b.get(__AMOUNT__) or 0) > float(pd):
                b[__AMOUNT__] = float(pd)
"""


def promise_pre_code(cap_to_deadline=True, cap_to_amount=True, id_prefix="p", pid_field="product_id",
                     amount_field="amount", date_field="date", promise_tool="create_promise", note_tool="add_note"):
    """Pre hook of the promise tool. Normalises the product id (a bare number gets `id_prefix`, so '1' -> 'p1';
    None skips it), amount -> float (commas stripped), date -> YYYY-MM-DD, remembers vars['pending_pid'], and
    with cap_to_deadline / cap_to_amount clamps the date to vars['dl_<pid>'] and the amount to vars['pd_<pid>']
    (the per-product facts the prepare node wrote), so the model can never record past a product's deadline or
    above its past-due amount."""
    code = _PROMISE_PRE
    code = code.replace("__PREFIX_BLOCK__", _PREFIX_BLOCK.replace("__PREFIX__", repr(str(id_prefix))) if id_prefix else "")
    code = code.replace("__CAP_DATE__", _CAP_DATE if cap_to_deadline else "")
    code = code.replace("__CAP_AMOUNT__", _CAP_AMOUNT if cap_to_amount else "")
    code = code.replace("__PID__", repr(pid_field)).replace("__AMOUNT__", repr(amount_field)).replace("__DATE__", repr(date_field))
    return _no_braces(state_fn_code(promise_tool, note_tool) + code, "promise_pre_code")


_PROMISE_POST = r"""
try:
    V = _getv()
    if isinstance(result, dict):
        result.pop('header', None)
        d = result.get('data')
        ok = isinstance(d, dict) and (d.get(__OK__) is True or str(d.get(__OK__)).lower() == 'true')
        msg = ''
        if V is not None:
            pid = str(V.get('pending_pid') or '')
            if ok and pid:
                rec = [x for x in str(V.get('rec_pids') or '').split(',') if x]
                if pid not in rec:
                    rec.append(pid)
                V['rec_pids'] = ','.join(rec)
                msg = 'The promise for ' + pid + ' is recorded. '
            elif pid:
                n = int(float(V.get('fail_' + pid) or 0)) + 1
                V['fail_' + pid] = n
                if n >= __MAXF__:
                    msg = 'NOT recorded, failed __TIMES__. Tell the customer you could not record the promise for ' + pid + ', then call __NOTE__ for ' + pid + ' with reason __REASON__. '
                else:
                    msg = 'NOT recorded. Do not say it is recorded. Call __TOOL__ once more for ' + pid + ' with exactly the same values. '
            msg += _status(V)
        else:
            msg = 'The promise is recorded.' if ok else 'NOT recorded. Do not say it is recorded. Call __TOOL__ once more with exactly the same values.'
        if isinstance(d, dict):
            d['what_to_do_next'] = msg
        else:
            result['what_to_do_next'] = msg
except Exception:
    pass
"""


def promise_post_code(max_fails=2, fail_reason="service_error", promise_tool="create_promise", note_tool="add_note",
                      ok_field="ok"):
    """Post hook of the promise tool. On ok true adds pending_pid to rec_pids and says it is recorded; otherwise
    counts fail_<pid>: below `max_fails` it asks for one retry with the same values, at `max_fails` it tells the
    model to inform the customer and call the note tool with `fail_reason` (one of the API's note reasons). Every
    message ends with the _status sentence (recorded / noted / still open), which also refreshes open_pids and
    all_done so the ALL_DONE transition fires in the same turn."""
    _ident(promise_tool, "promise_tool")
    _ident(note_tool, "note_tool")
    _ident(fail_reason, "fail_reason")
    max_fails = int(max_fails)
    if max_fails < 1:
        raise ValueError("max_fails must be >= 1")
    times = {1: "once", 2: "twice"}.get(max_fails, "%d times" % max_fails)
    code = (_PROMISE_POST.replace("__MAXF__", str(max_fails)).replace("__TIMES__", times).replace("__NOTE__", note_tool)
            .replace("__REASON__", fail_reason).replace("__TOOL__", promise_tool).replace("__OK__", repr(ok_field)))
    return _no_braces(state_fn_code(promise_tool, note_tool) + code, "promise_post_code")


# ----------------------------------------------------------------------------------------------- note hooks
_NOTE_PRE = r"""
try:
    V = _getv()
    b = config.get('body')
    if isinstance(b, dict):
        pid = str(b.get(__PID__) or '').strip()
__PREFIX_BLOCK__        b[__PID__] = pid
        if V is not None:
            V['pending_note'] = pid + ':' + str(b.get(__REASON__) or '')
except Exception:
    pass
"""


def note_pre_code(id_prefix="p", pid_field="product_id", reason_field="reason", promise_tool="create_promise",
                  note_tool="add_note"):
    """Pre hook of the note tool: normalises the product id like promise_pre_code and remembers
    vars['pending_note'] = '<pid>:<reason>' for the post hook."""
    code = _NOTE_PRE.replace("__PREFIX_BLOCK__", _PREFIX_BLOCK.replace("__PREFIX__", repr(str(id_prefix))) if id_prefix else "")
    code = code.replace("__PID__", repr(pid_field)).replace("__REASON__", repr(reason_field))
    return _no_braces(state_fn_code(promise_tool, note_tool) + code, "note_pre_code")


_NOTE_POST = r"""
try:
    V = _getv()
    if isinstance(result, dict):
        result.pop('header', None)
        d = result.get('data')
        ok = isinstance(d, dict) and (d.get(__OK__) is True or str(d.get(__OK__)).lower() == 'true')
        msg = ''
        if V is not None:
            pn = str(V.get('pending_note') or '')
            if ok and pn:
                notes = [x for x in str(V.get('note_log') or '').split(',') if x]
                if pn.split(':')[0] not in [x.split(':')[0] for x in notes]:
                    notes.append(pn)
                V['note_log'] = ','.join(notes)
                msg = 'Note saved. '
            elif pn:
                msg = 'The note failed. Call __NOTE__ once more with the same values. '
            msg += _status(V)
        else:
            msg = 'Note saved.' if ok else 'The note failed. Call __NOTE__ once more.'
        if isinstance(d, dict):
            d['what_to_do_next'] = msg
        else:
            result['what_to_do_next'] = msg
except Exception:
    pass
"""


def note_post_code(promise_tool="create_promise", note_tool="add_note", ok_field="ok"):
    """Post hook of the note tool: on ok true appends pending_note to note_log (one note per product), otherwise
    asks for one retry; then the _status sentence, which refreshes open_pids and all_done."""
    _ident(note_tool, "note_tool")
    code = _NOTE_POST.replace("__NOTE__", note_tool).replace("__OK__", repr(ok_field))
    return _no_braces(state_fn_code(promise_tool, note_tool) + code, "note_post_code")


# ----------------------------------------------------------------------------------------------- transitions
def all_done_tr(target="finalize", desc="every product has a recorded promise or a note"):
    """The deterministic ALL_DONE transition: vars['all_done'] == 'yes' (written by the hooks) -> `target`."""
    return fl.eq("all_done", "yes", target, desc)


def done_intent_tr(target="finalize", desc="Every product now has a recorded promise or a note, and nothing is left to record.",
                   intent_desc="Every product has a recorded promise or a note"):
    """The tool-call fallback for the same event (the model calls transition_to_<target>)."""
    return fl.intent_tool(target, desc, intent_desc)


# ----------------------------------------------------------------------------------------------- finalize
_FINALIZE = r"""
try:
    rec = [x for x in str(vars.get('rec_pids') or '').split(',') if x]
    notes = [x for x in str(vars.get('note_log') or '').split(',') if x]
    pids = [x for x in str(vars.get('pids_csv') or '').split(',') if x]
    nd = dict()
    for x in notes:
        if ':' in x:
            nd[x.split(':')[0]] = x.split(':', 1)[1]
    keys = dict(__PAIRS__)
    if rec:
        r = __PROMISE__
    elif nd and all(nd.get(p) == __PAID_REASON__ for p in pids if p in nd) and len(nd) >= len(pids):
        r = __PAID__
    else:
        r = __DEFAULT__
__PICK__        if not rec and not nd:
            try:
                if int(float(vars.get(__SC__) or 0)) > 0 and str(vars.get(__OKVAR__)).lower() == 'true':
                    r = __PROMISE__
            except Exception:
                pass
    vars[__ROUTE__] = r
except Exception:
    vars[__ROUTE__] = __DEFAULT__
"""
_PICK_PRODUCT = """        for p in pids:
            if p in nd and nd[p] != __PAID_REASON__:
                r = keys.get(nd[p], __DEFAULT__)
                break
"""
_PICK_PRECEDENCE = """        for reason, key in __PAIRS__:
            if any(nd.get(p) == reason for p in pids):
                r = key
                break
"""


def _pairs(precedence):
    if isinstance(precedence, dict):
        pairs = list(precedence.items())
    else:
        pairs = [tuple(x) for x in precedence]
    for reason, key in pairs:
        _ident(reason, "note reason")
        _ident(key, "fin key")
    return pairs


def finalize_code(precedence, promise_key="promise", paid_key="paid", default_key="refused", paid_reason=None,
                  order="product", promise_tool="create_promise", route_var=ROUTE_VAR, ok_field="ok"):
    """Source of the finalize code node: writes vars[route_var] = the fin key of the closing outcome.
    `precedence` is the ordered list of (note_reason, fin_key) pairs (or an ordered dict) for the no-promise
    endings. Rules, in this order:
      1. at least one promise recorded (rec_pids)                      -> promise_key
      2. every product noted and every note is `paid_reason`           -> paid_key  (paid_reason defaults to paid_key)
      3. otherwise the fin key of a non-paid note:
           order="product":    the first product in get_account order whose note is not paid (Brief B's rule)
           order="precedence": the first pair of `precedence` that some product carries
         an unknown reason, or no note at all, gives default_key
      4. no hook state at all (hooks had no vars): <promise_tool>_success_count > 0 and ok true -> promise_key.
    Route the node with finalize_transitions(...) built from the same arguments."""
    pairs = _pairs(precedence)
    for k, what in ((promise_key, "promise_key"), (paid_key, "paid_key"), (default_key, "default_key")):
        _ident(k, what)
    _ident(promise_tool, "promise_tool")
    paid_reason = paid_key if paid_reason is None else _ident(paid_reason, "paid_reason")
    if order not in ("product", "precedence"):
        raise ValueError("order must be 'product' or 'precedence'")
    pick = _PICK_PRODUCT if order == "product" else _PICK_PRECEDENCE
    code = (_FINALIZE.replace("__PICK__", pick).replace("__PAIRS__", repr(pairs)).replace("__PROMISE__", repr(promise_key))
            .replace("__PAID_REASON__", repr(paid_reason)).replace("__PAID__", repr(paid_key)).replace("__DEFAULT__", repr(default_key))
            .replace("__SC__", repr("%s_success_count" % promise_tool)).replace("__OKVAR__", repr("%s_response.data.%s" % (promise_tool, ok_field)))
            .replace("__ROUTE__", repr(route_var)))
    return _no_braces(code, "finalize_code")


def finalize_transitions(precedence, promise_key="promise", paid_key="paid", default_key="refused", route_var=ROUTE_VAR,
                         fin_prefix="fin_"):
    """The finalize node's transitions: route_var == <key> -> fin_<key> for promise_key, paid_key and every fin key
    of `precedence` (in that order, once each), then always -> fin_<default_key>."""
    pairs = _pairs(precedence)
    out, seen = [], set()
    for key in [promise_key, paid_key] + [k for _, k in pairs]:
        if key in seen or key == default_key:
            continue
        seen.add(key)
        out.append(fl.eq(route_var, key, fin_prefix + key, key.replace("_", " ")))
    out.append(fl.always(fin_prefix + default_key))
    return out


# ----------------------------------------------------------------------------------------------- per-product facts
LINE_TEMPLATE = ("{pid} = {words}: full past-due amount {past_due}, {days_late} days late ({band} band). "
                 "Floor (lowest amount allowed) {floor} (the {floor_name}). "
                 "Deadline (latest date allowed) {deadline_text} ({deadline_iso}). "
                 "Attempt 1: propose {past_due} (or the floor {floor} if the customer already said the full amount is too much) on {a1_text} ({a1_iso}). ")
ATTEMPT2_TEMPLATE = "Attempt 2: propose the floor {floor} on the deadline {deadline_text}. Persuasion attempts allowed: {attempts}."
ONE_ATTEMPT_TEMPLATE = "NO attempt 2: persuasion attempts allowed: {attempts}."
PLACEHOLDERS = ("pid", "words", "past_due", "days_late", "band", "floor", "floor_name", "deadline_text", "deadline_iso",
                "a1_text", "a1_iso", "attempts", "title", "last_name", "first_name", "n")

_FACTS_BODY = r'''
prods = [p for p in prods if isinstance(p, dict)]
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
a1base = __A1BASE__
BANDS = __BANDS__
FLOORS = __FLOORS__
WORDS = __WORDS__
bdl = dict()
for _b in BANDS:
    if _b[3]:
        bdl[_b[0]] = datetime.date.fromisoformat(str(vars.get(_b[3])))
    else:
        bdl[_b[0]] = addbd(today, int(_b[4] or 0))
def _fill(t, d):
    return re.sub(r'\{(\w+)\}', lambda m: '' if d.get(m.group(1)) is None else str(d.get(m.group(1))), t)
infos = []
for i, p in enumerate(prods):
    ptype = str(p.get('type') or '')
    pid = str(p.get('product_id') or (__PREFIX__ + str(i + 1)))
    f = dict(p)
    f['type_words'] = ptype.replace('_', ' ') if ptype else __UNKNOWN__
    words = ''
    for _w in WORDS:
        if _w[0] is None or ptype in _w[0]:
            words = _fill(_w[1], f)
            break
    floor = None
    floor_name = ''
    for _r in FLOORS:
        if _r[0] is None or ptype in _r[0]:
            floor = p.get(_r[1])
            floor_name = _r[2]
            break
    past_due = float(p.get('past_due') or 0)
    try:
        floor = float(floor)
    except Exception:
        floor = past_due
    dl = int(float(p.get('days_late') or 0))
    band = BANDS[-1]
    for _b in BANDS:
        if _b[1] is None or dl <= int(_b[1]):
            band = _b
            break
    deadline = bdl[band[0]]
    att = int(band[2])
    a1 = a1base if a1base is not None and a1base <= deadline else deadline
    infos.append(dict(pid=pid, words=words, past_due=past_due, floor=floor, floor_name=floor_name, dl=dl, band=band[0], att=att, deadline=deadline, a1=a1))
    vars['dl_' + pid] = deadline.isoformat()
    vars['pd_' + pid] = str(past_due)
n = len(infos)
vars['n_products'] = str(n)
vars['pids_csv'] = ','.join(x['pid'] for x in infos)
vars['open_pids'] = vars['pids_csv']
vars['rec_pids'] = ''
vars['note_log'] = ''
vars['all_done'] = 'no'
base = dict(title=str(vars.get('title') or ''), last_name=str(vars.get('last_name') or ''), first_name=str(vars.get('first_name') or ''), n=str(n))
def _facts(x):
    f = dict(base)
    f.update(x)
    f['past_due'] = fmt(x['past_due'])
    f['floor'] = fmt(x['floor'])
    f['days_late'] = str(x['dl'])
    f['deadline_text'] = txt_short(x['deadline'])
    f['deadline_iso'] = x['deadline'].isoformat()
    f['a1_text'] = txt_short(x['a1'])
    f['a1_iso'] = x['a1'].isoformat()
    f['attempts'] = str(x['att'])
    return f
lines = []
for x in infos:
    f = _facts(x)
    lines.append('- ' + _fill(__LINE__, f) + _fill(__ATT2__ if x['att'] >= 2 else __ATT1__, f))
vars['products_text'] = '\n'.join(lines)
if n == 1:
    st = _fill(__ST_ONE__, _facts(infos[0]))
else:
    st = _fill(__ST_HEAD__, base)
    for x in infos:
        st += _fill(__ST_ITEM__, _facts(x))
    st += _fill(__ST_TAIL__, base)
vars['statement_text'] = st
maxdl = max([x['deadline'] for x in infos] or [today])
cal = []
d = today
while d <= maxdl + datetime.timedelta(days=__EXTRA__):
    nb = next_bd(d)
    if isbd(d):
        ok = [x['pid'] for x in infos if d <= x['deadline']]
        bad = [x['pid'] for x in infos if d > x['deadline']]
        tag = 'business day.'
        if ok:
            tag += ' Allowed for ' + ', '.join(ok) + '.'
        if bad:
            tag += ' AFTER THE DEADLINE of ' + ', '.join(bad) + ' (use that product\'s deadline instead).'
    else:
        tag = ('weekend' if d.weekday() not in BWD else 'bank holiday') + ', NOT allowed -> offer the next business day ' + txt_short(nb) + ' (' + nb.isoformat() + ') where it is not after the deadline.'
    cal.append(d.isoformat() + ' ' + txt_short(d) + ('  (today)' if d == today else '') + ': ' + tag)
    d = d + datetime.timedelta(days=1)
vars['calendar_text'] = '\n'.join(cal)
'''


def _types(rule, what):
    t = rule.get("types")
    if t is None:
        return None
    if isinstance(t, str):
        t = [t]
    return [str(x) for x in t]


def _check_template(tpl, what, allowed):
    if not isinstance(tpl, str):
        raise ValueError("%s must be a string template" % what)
    if "{{" in tpl or "}}" in tpl:
        raise ValueError("%s: a template may not contain '{{' or '}}'" % what)
    bad = [m for m in re.findall(r"\{(\w+)\}", tpl) if m not in allowed]
    if bad:
        raise ValueError("%s: unknown placeholders %s (allowed: %s)" % (what, bad, ", ".join(sorted(allowed))))
    return tpl


def products_facts_code(bands, floor_rules, wording, statement, attempt1_var="attempt1_date", id_prefix="p",
                        unknown_type_words="account", line_template=LINE_TEMPLATE, attempt2_template=ATTEMPT2_TEMPLATE,
                        one_attempt_template=ONE_ATTEMPT_TEMPLATE, calendar_extra_days=10):
    """The body of the prepare code node (put it after freyalib.products_from_vars() inside guarded(), with
    CAL_HELPERS on top; prepare_code() does that). From the product list `prods` it writes, per product,
    dl_<pid> and pd_<pid>, then n_products, pids_csv, open_pids (= pids_csv), rec_pids '', note_log '',
    all_done 'no', products_text (one '- ' line per product), statement_text (the opening statement) and
    calendar_text (one tagged line per day up to the latest deadline + calendar_extra_days, saying for which
    products a business day is allowed and which are past their deadline).

    bands: ordered list of {"name", "max_days_late" (None = catch-all, the last band), "attempts",
           "deadline_var" (an ISO date variable the setup node always sets) or "deadline_bdays" (business days
           from today)}; a product takes the first band with days_late <= max_days_late.
    floor_rules: ordered list of {"types": [product types] or None (any), "field": the product field holding the
           floor, "name": its words}; no usable floor -> the past-due amount is the floor.
    wording: ordered list of {"types": [...] or None, "template": "credit card ending {card_last4}"}; placeholders
           are the product's fields plus {type_words} (the type with '_' -> ' ', or `unknown_type_words`).
    statement: {"one": template for a single product, "many_head", "many_item" (per product), "many_tail"};
           placeholders: PLACEHOLDERS ({title}, {last_name}, {first_name}, {n} and the per-product facts).
    attempt1_var: the ISO variable with the attempt-1 date (capped at the product's deadline); None -> the deadline.
    line_template / attempt2_template / one_attempt_template: the products_text wording (per-product facts
           line, then the ladder sentence for 2+ attempts or for 1); the defaults are the organisers' wording of
           the Brief A/B ladder: override them when the brief's ladder differs.
    No bank value is baked in: everything above comes from the brief."""
    if not bands:
        raise ValueError("bands must list at least one band")
    band_rows = []
    for b in bands:
        name = str(b["name"])
        mx = b.get("max_days_late")
        mx = None if mx is None else int(mx)
        att = int(b.get("attempts", 1))
        dvar = b.get("deadline_var")
        dbd = b.get("deadline_bdays")
        if not dvar and dbd is None:
            raise ValueError("band %r needs deadline_var or deadline_bdays" % name)
        band_rows.append((name, mx, att, str(dvar) if dvar else "", None if dbd is None else int(dbd)))
    if band_rows[-1][1] is not None:
        raise ValueError("the last band must have max_days_late None (it catches every later product)")
    floor_rows = [(_types(r, "floor rule"), str(r["field"]), str(r["name"])) for r in floor_rules]
    if not floor_rows or floor_rows[-1][0] is not None:
        raise ValueError("floor_rules must end with a catch-all rule (types None)")
    word_rows = [(_types(r, "wording"), str(r["template"])) for r in wording]
    if not word_rows or word_rows[-1][0] is not None:
        raise ValueError("wording must end with a catch-all rule (types None)")
    for _, tpl in word_rows:
        if "{{" in tpl or "}}" in tpl:
            raise ValueError("wording template may not contain '{{' or '}}'")
    allowed = set(PLACEHOLDERS)
    st = {k: _check_template(statement[k], "statement[%r]" % k, allowed) for k in ("one", "many_head", "many_item", "many_tail")}
    line = _check_template(line_template, "line_template", allowed)
    att2 = _check_template(attempt2_template, "attempt2_template", allowed)
    att1 = _check_template(one_attempt_template, "one_attempt_template", allowed)
    a1 = "datetime.date.fromisoformat(str(vars.get(%r)))" % str(attempt1_var) if attempt1_var else "None"
    code = (_FACTS_BODY.replace("__A1BASE__", a1).replace("__BANDS__", repr(band_rows)).replace("__FLOORS__", repr(floor_rows))
            .replace("__WORDS__", repr(word_rows)).replace("__PREFIX__", repr(str(id_prefix or "")))
            .replace("__UNKNOWN__", repr(str(unknown_type_words))).replace("__LINE__", repr(line)).replace("__ATT2__", repr(att2))
            .replace("__ATT1__", repr(att1)).replace("__ST_ONE__", repr(st["one"])).replace("__ST_HEAD__", repr(st["many_head"]))
            .replace("__ST_ITEM__", repr(st["many_item"])).replace("__ST_TAIL__", repr(st["many_tail"]))
            .replace("__EXTRA__", str(int(calendar_extra_days))))
    return _no_braces(code, "products_facts_code")


def products_facts_fallbacks(statement_fallback, id_prefix="p", products_fallback="Product data could not be prepared."):
    """The guarded() fallbacks of the prepare node: what the prompts show when the product data could not be
    prepared (a single product named <id_prefix>1 stays open so the call still reaches finalize)."""
    pid = "%s1" % (id_prefix or "")
    return {"products_text": products_fallback, "statement_text": statement_fallback, "calendar_text": "",
            "pids_csv": pid, "open_pids": pid, "all_done": "no"}


def prepare_code(holidays, statement_fallback, business_weekdays=fl.BUSINESS_WEEKDAYS, state_var="prepare_state",
                 products_var="products", **facts):
    """The complete prepare code node source: CAL_HELPERS + guarded(products_from_vars() + products_facts_code(**facts)).
    `facts` are the products_facts_code keyword arguments (bands, floor_rules, wording, statement, ...)."""
    body = fl.products_from_vars(products_var) + products_facts_code(**facts)
    fb = products_facts_fallbacks(statement_fallback, facts.get("id_prefix", "p"))
    return fl.CAL_HELPERS(holidays, business_weekdays) + fl.guarded(body, state_var, fb)
