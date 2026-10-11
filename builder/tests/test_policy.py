"""Tests of builder/policy.py (T1 offer guard, T2 counters in code, T3 state_line, T22 code-built read-back).

Every test execs the generated code-node source exactly as the platform runs a code node: one namespace holding
`vars`, the snippet mutates vars. A call is simulated as a sequence of events (the node the routing would enter),
with the extraction variables set the way the extractor would set them before each event. Dates are around
weekends, a bank holiday and both deadlines; amounts around the floor and the full amount. Example values are the
kit's practice calendar (now = Wednesday 14 October 2026); the module itself holds none of them.

    python3 builder/tests/test_policy.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import freyalib as fl  # noqa: E402
import policy as pol  # noqa: E402

HOL = ["2026-10-26", "2026-11-11"]
TODAY = "2026-10-14"

TEXTS = {
    "_allow_defaults": True,
    # the former library defaults (Brief A wording) that the older tests assert on; a real generator passes the brief's own
    "too_much_floor": "I understand. The lowest amount I can accept is [floor], the [floor_name]. The rest stays overdue.",
    "paid": "Thank you for letting me know. Payments can take one business day to appear, so I will not take a promise for your [words].",
    "hardship": "I am sorry to hear that. Would you like me to connect you with our customer support team?",
    "notalk_first": "I understand. This will only take a moment.",
    "wrap_change": "A recorded promise cannot be changed on this call, but you can change it in the mobile app.",
    "human_first": "Before I transfer you, is there anything I can help you with myself?","after_recorded": "You will receive a text message confirming this promise.",
         "wrap_change": "You can change it in the mobile app."}

BODY = r'''
today = datetime.date.fromisoformat(str(vars.get('today_iso')))
monday = today - datetime.timedelta(days=today.weekday())
a1 = lastbd_of_week(monday)
if a1 is None or a1 <= today:
    a1 = lastbd_of_week(monday + datetime.timedelta(days=7))
spec = json.loads(str(vars.get('test_products')))
for i, p in enumerate(spec):
    late = int(p['days_late']) > 7
    dl = addbd(today, 7 if late else 12)
    rungs = [('full_or_floor', a1)] + ([('floor', dl)] if late else [])
    register_product(vars, 'p' + str(i + 1), p['words'], p['full'], p['floor'], 'minimum payment', dl, rungs)
statement = 'STATEMENT'
'''


def mk(multi=False, notes=False, **kw):
    return pol.Policy(HOL, texts=TEXTS, multi=multi, notes=notes,
                      note_reasons={"refused": "refused", "hardship": "hardship", "dispute": "dispute",
                                    "paid": "paid", "service_error": "service_error"} if notes else None, **kw)


def run(src, V):
    exec(src, {"vars": V})
    return V


def start(products, multi=False, notes=False):
    import json
    P = mk(multi, notes)
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps(products)}
    run(P.prepare_code(BODY, "statement"), V)
    assert V.get("prepare_state") == "ok", V.get("prepare_state")
    return P, V


def ev(P, V, event, **ext):
    for k, v in ext.items():
        V[k] = v
    run(P.event_code(event), V)
    assert V.get("policy_state") == "ok", (event, V.get("policy_state"))
    for k, neutral in pol.CLEAR_ENUMS.items():
        assert V[k] == neutral, (k, V[k])
    return V


CARD = {"words": "credit card ending 4821", "full": 420, "floor": 126, "days_late": 6}      # early: 1 attempt
LOAN = {"words": "personal loan", "full": 2100, "floor": 700, "days_late": 28}               # late: 2 attempts
CAR = {"words": "car loan", "full": 75, "floor": 25, "days_late": 3}

TESTS = []


def test(f):
    TESTS.append(f)
    return f


@test
def prepare_and_statement():
    P, V = start([CARD])
    assert V["say_next"] == "STATEMENT" and V["route"] == "negotiate"
    assert V["deadline_p1"] == "2026-11-02", V["deadline_p1"]           # 12 business days, 26 Oct holiday skipped
    assert V["offer_question"] == "Can you pay 420 today?", V["offer_question"]
    assert V["state_line"].startswith("Product: credit card ending 4821"), V["state_line"]


@test
def early_refusals_exhaust():
    P, V = start([CARD])
    ev(P, V, "refuse")
    assert V["say_next"] == "Can you pay 420 on Friday 16 October?", V["say_next"]
    assert V["attempts_used_p1"] == "1"
    assert "420 on today" not in V["state_line"] and "420 on 2026-10-14" in V["state_line"], V["state_line"]
    ev(P, V, "refuse")
    assert V["route"] == "fin" and V["final_route"] == "refused", (V["route"], V.get("final_route"))


@test
def too_much_then_ladder_switches_to_floor():          # EXT-A-18
    P, V = start([LOAN])
    ev(P, V, "too_much")
    assert "700" in V["say_next"] and "rest stays overdue" in V["say_next"], V["say_next"]
    assert V["prop_amount"] == "700.0" and V["prop_date"] == TODAY and V["offered_floor_p1"] == "yes"
    ev(P, V, "refuse")
    assert V["say_next"] == "Can you pay 700 on Friday 16 October?", V["say_next"]        # attempt 1 = floor
    ev(P, V, "refuse")
    assert V["say_next"] == "Can you pay 700 on Friday 23 October?", V["say_next"]        # attempt 2 = floor, deadline
    ev(P, V, "accept", stance="accept")
    assert V["route"] == "confirm" and V["ok_amount"] == "700.0" and V["ok_date"] == "2026-10-23"
    assert V["readback_line"] == "To confirm: personal loan, 700, on Friday 23 October. Do you confirm?", V["readback_line"]


@test
def floor_offered_once_only():
    P, V = start([LOAN])
    ev(P, V, "too_much")
    ev(P, V, "too_much")                                   # too much again: a flat refusal, no second floor offer
    assert V["attempts_used_p1"] == "1" and V["say_next"] == "Can you pay 700 on Friday 16 October?", V["say_next"]
    assert "do not offer it again" in V["state_line"]


@test
def weekend_offer():
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-17", offer_amount="")
    assert V["offer_verdict"] == "weekend_or_holiday", V["offer_verdict"]
    assert V["say_next"] == ("Saturday 17 October is not a business day. The next business day is Monday 19 October. "
                             "Can you pay 420 on Monday 19 October?"), V["say_next"]
    ev(P, V, "accept", stance="accept")
    assert V["route"] == "confirm" and V["ok_date"] == "2026-10-19"


@test
def holiday_offer():                                       # PUB-07
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-26")
    assert V["offer_verdict"] == "weekend_or_holiday" and V["prop_date"] == "2026-10-27", V["prop_date"]


@test
def after_deadline_offer():                                # PUB-04
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-11-06")
    assert V["offer_verdict"] == "after_deadline" and V["prop_date"] == "2026-10-23"
    assert V["say_next"].startswith("The latest date I can record is Friday 23 October."), V["say_next"]
    ev(P, V, "refuse")                                     # refusing the deadline is a flat refusal
    assert V["attempts_used_p1"] == "1" and V["prop_date"] == "2026-10-16"


@test
def before_today_offer():
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-12", offer_when="12 October", offer_amount="420")
    assert V["offer_verdict"] == "before_today" and V["prop_date"] == TODAY


@test
def floor_boundaries():
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="700", offer_date="2026-10-22")       # = floor: ok
    assert V["offer_verdict"] == "ok" and V["route"] == "confirm" and V["ok_amount"] == "700.0"
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="699.99", offer_date="2026-10-22")
    assert V["offer_verdict"] == "below_floor" and V["prop_amount"] == "700.0" and V["prop_date"] == "2026-10-22"
    assert V["say_next"].startswith("I cannot record 699.99."), V["say_next"]
    ev(P, V, "offer", offer_kind="exact", offer_amount="500")                               # below again: refusal
    assert V["offer_verdict"] == "below_floor" and V["attempts_used_p1"] == "1", V["attempts_used_p1"]
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="2100", offer_date="2026-10-16")       # = full: ok
    assert V["offer_verdict"] == "ok"
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="2500")
    assert V["offer_verdict"] == "above_full" and V["prop_amount"] == "2100.0"


@test
def date_and_amount_problems_together():
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="100", offer_date="2026-10-18")
    assert V["offer_verdict"] == "weekend_or_holiday" and V["prop_amount"] == "700.0" and V["prop_date"] == "2026-10-19"
    assert "Sunday 18 October" in V["say_next"] and "I cannot record 100" in V["say_next"], V["say_next"]


@test
def amount_only_keeps_date_on_the_table():
    P, V = start([LOAN])
    ev(P, V, "refuse")                                      # attempt 1: 2100 on Fri 16
    ev(P, V, "offer", offer_kind="exact", offer_amount="1000", offer_date="")
    assert V["route"] == "confirm" and V["ok_date"] == "2026-10-16" and V["ok_amount"] == "1000.0"


@test
def vague_then_deadline():
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="vague", offer_date="2026-10-19")
    assert V["say_next"] == "Which exact day would that be?" and V["route"] == "negotiate"
    ev(P, V, "offer", offer_kind="vague")
    assert V["prop_date"] == "2026-11-02" and V["say_next"].startswith("The latest date I can record is Monday 2 November."), V["say_next"]


@test
def hardship_with_named_offer():                            # EXT-A-28
    P, V = start([LOAN])
    ev(P, V, "hardship", offer_kind="exact", offer_amount="700", offer_date="2026-10-22")
    assert V["route"] == "hardship" and V["hs_offer"] == "yes" and V["say_next"].startswith("I am sorry")
    assert V["offer_date"] == pol.CLEAR_VALUES["offer_date"] and V["offer_kind"] == "none"   # schema-valid clear
    ev(P, V, "hs_decline", hs_answer="support_no")
    assert V["route"] == "confirm" and V["ok_amount"] == "700.0" and V["ok_date"] == "2026-10-22", (V["route"], V.get("ok_date"))


@test
def hardship_without_offer():                               # PUB-05
    P, V = start([LOAN])
    ev(P, V, "hardship")
    ev(P, V, "hs_decline")
    assert V["route"] == "fin" and V["final_route"] == "hardship"


@test
def hardship_refusal_is_no_persuasion():
    P, V = start([LOAN])
    ev(P, V, "hardship")
    ev(P, V, "too_much")
    assert V["route"] == "fin" and V["final_route"] == "hardship" and V["attempts_used_p1"] == "0"


@test
def confirm_change_reads_back_again():                     # EXT-A-34
    P, V = start([CARD])
    ev(P, V, "refuse")
    ev(P, V, "accept", stance="accept")
    assert V["readback_line"] == "To confirm: credit card ending 4821, 420, on Friday 16 October. Do you confirm?"
    ev(P, V, "change", confirm="change", offer_amount="250")
    assert V["route"] == "confirm" and V["readback_line"] == "To confirm: credit card ending 4821, 250, on Friday 16 October. Do you confirm?", V["readback_line"]
    ev(P, V, "change", confirm="change", offer_date="2026-10-24")      # a Saturday at the read-back
    assert V["route"] == "negotiate" and V["prop_date"] == "2026-10-27", V["prop_date"]   # Mon 26 is a holiday


@test
def confirm_no_is_a_refusal():
    P, V = start([LOAN])
    ev(P, V, "accept", stance="accept")                    # 2100 today
    ev(P, V, "confirm_no", confirm="no")
    assert V["route"] == "negotiate" and V["say_next"] == "Can you pay 2100 on Friday 16 October?", V["say_next"]


@test
def record_retry_then_ok():                                # PUB-10
    P, V = start([CARD])
    ev(P, V, "accept", stance="accept")
    ev(P, V, "confirm_yes", confirm="yes")
    assert V["route"] == "record" and V["rec_pid"] == "p1" and V["rec_amount"] == "420.0" and V["rec_date"] == TODAY
    V["rec_ok"] = "False"
    ev(P, V, "rec_after")
    assert V["route"] == "record"
    V["rec_ok"] = "True"
    ev(P, V, "rec_after")
    assert V["route"] == "wrapup" and V["outcome"] == "promise" and V["reason"] == ""
    assert V["wrap_line"] == ("Your promise is recorded. You will receive a text message confirming this promise. "
                              "Is there anything else I can help you with?"), V["wrap_line"]


@test
def record_fails_twice():
    P, V = start([CARD])
    ev(P, V, "accept", stance="accept")
    ev(P, V, "confirm_yes")
    for _ in range(2):
        V["rec_ok"] = "pending"                            # HTTP 500: nothing mapped
        ev(P, V, "rec_after")
    assert V["route"] == "fin" and V["final_route"] == "service_error", (V["route"], V.get("final_route"))


@test
def wrapup_events():                                       # EXT-A-31, EXT-A-35
    P, V = start([CARD])
    ev(P, V, "accept", stance="accept")
    ev(P, V, "confirm_yes")
    V["rec_ok"] = "true"
    ev(P, V, "rec_after")
    ev(P, V, "wrap_change", wrap="change")
    assert V["route"] == "wrapup" and V["wrap_line"].startswith("You can change it in the mobile app."), V["wrap_line"]
    ev(P, V, "wrap_human", wrap="human")
    assert V["route"] == "wrapup" and V["wrap_line"].startswith("Before I transfer you")
    ev(P, V, "wrap_human", wrap="human")
    assert V["route"] == "xfer_general"
    ev(P, V, "finalize")
    assert V["final_route"] == "promise"


@test
def human_and_notalk_counters():
    P, V = start([CARD])
    ev(P, V, "human", topic="human")
    assert V["route"] == "negotiate" and V["say_next"].startswith("Before I transfer you")
    ev(P, V, "human", topic="human")
    assert V["route"] == "xfer_general"
    P, V = start([CARD])
    ev(P, V, "notalk", topic="no_talk")
    assert V["route"] == "negotiate" and V["say_next"].endswith("Can you pay 420 today?"), V["say_next"]
    ev(P, V, "notalk", topic="no_talk")
    assert V["route"] == "fin" and V["final_route"] == "refused"


@test
def paid_and_dispute_single():
    P, V = start([CARD])
    ev(P, V, "paid", topic="already_paid")
    assert V["route"] == "fin" and V["final_route"] == "paid"
    P, V = start([CARD])
    ev(P, V, "dispute", topic="dispute")
    assert V["final_route"] == "dispute"


@test
def multi_accept_all_today():
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    assert V["stage"] == "all" and V["offer_question"] == "Can you pay all of them today?"
    ev(P, V, "accept", stance="accept")
    assert V["route"] == "confirm" and V["readback_line"].count("today") == 3, V["readback_line"]


@test
def multi_one_date_after_a_deadline():                     # PUB-13
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-30", offer_for="all")
    assert V["route"] == "confirm"
    assert V["agreed_p1"].startswith("420.0|2026-10-30") and V["agreed_p2"].startswith("2100.0|2026-10-23|dl"), (V["agreed_p1"], V["agreed_p2"])
    assert "latest date I can record for it" in V["readback_line"], V["readback_line"]


@test
def multi_one_by_one_with_notes():                         # PUB-12
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-15", offer_for="first")
    assert V["state_p1"] == "agreed" and V["cur_pid"] == "p2" and V["attempts_used_p2"] == "1", V["say_next"]
    assert V["say_next"].endswith("For your personal loan, can you pay 2100 on Friday 16 October?"), V["say_next"]
    ev(P, V, "refuse")
    assert V["say_next"] == "For your personal loan, can you pay 700 on Friday 23 October?", V["say_next"]
    ev(P, V, "refuse")
    assert V["state_p2"] == "refused" and V["cur_pid"] == "p3" and V["say_next"].startswith("I understand."), V["say_next"]
    ev(P, V, "refuse")
    assert V["state_p3"] == "refused" and V["route"] == "confirm", V["route"]
    assert V["readback_line"].endswith("To confirm: credit card ending 4821, 420, on Thursday 15 October. Do you confirm?"), V["readback_line"]
    ev(P, V, "confirm_yes", confirm="yes")
    V["rec_ok"] = "true"
    ev(P, V, "rec_after")
    assert V["route"] == "note" and V["note_pid"] == "p2" and V["note_reason"] == "refused"
    V["note_ok"] = "true"
    ev(P, V, "note_after")
    assert V["route"] == "note" and V["note_pid"] == "p3"
    V["note_ok"] = "true"
    ev(P, V, "note_after")
    assert V["route"] == "wrapup" and V["outcome"] == "promise"


@test
def multi_refuse_all_today_goes_one_by_one():
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "refuse")
    assert V["stage"] == "one" and V["cur_pid"] == "p1"
    assert V["say_next"].startswith("Let us go through them one by one.") and V["say_next"].endswith("can you pay 420 on Friday 16 October?"), V["say_next"]


@test
def multi_one_date_for_all_after_one_by_one_started():     # PUB-11
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    ev(P, V, "refuse")
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-16", offer_for="all")
    assert V["route"] == "confirm" and all(V["agreed_" + p].startswith(x) for p, x in
                                           (("p1", "420.0|2026-10-16"), ("p2", "2100.0|2026-10-16"), ("p3", "75.0|2026-10-16"))), V["readback_line"]


@test
def multi_no_promise_closing_order():
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "paid", topic="already_paid", offer_for="first")
    assert V["state_p1"] == "paid" and V["cur_pid"] == "p2"
    ev(P, V, "dispute", topic="dispute")
    assert V["route"] == "note"
    for _ in range(2):
        V["note_ok"] = "true"
        ev(P, V, "note_after")
    assert V["route"] == "fin" and V["final_route"] == "dispute", V.get("final_route")


@test
def note_text_carries_the_customers_reason():               # Brief F PUB-05: the note must name the job loss
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "hardship", topic="hardship", customer_said="I lost my job last month")
    V["customer_said"] = "have no money right now"          # a later turn gives another reason: both are kept
    ev(P, V, "hs_decline", hs_answer="support_no")
    assert V["route"] == "note" and "lost my job last month; have no money right now" in V["note_text"], V.get("note_text")
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "hardship", topic="hardship", customer_said="I lost my job last month")
    V["customer_said"] = ""                                 # a later turn extracts nothing: the reason stays
    ev(P, V, "hs_decline", hs_answer="support_no")
    assert V["route"] == "note" and "lost my job last month" in V["note_text"], V.get("note_text")
    P, V = start([CARD], notes=True)
    ev(P, V, "dispute", topic="dispute", customer_said="the card was stolen in August")
    assert V["route"] == "note" and "the card was stolen in August" in V["note_text"], V.get("note_text")
    P, V = start([CARD], notes=True)                        # no reason given: the note still says what happened
    ev(P, V, "dispute", topic="dispute")
    assert V["route"] == "note" and "disputes" in V["note_text"], V.get("note_text")
    # multi-product: one product's reason never reaches another product's note (stale words are cleared each turn)
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "paid", topic="already_paid", offer_for="first", customer_said="paid the card last Friday by bank transfer")
    ev(P, V, "refuse")
    ev(P, V, "refuse")
    notes = {}
    while V.get("route") == "note":
        notes[V["note_pid"]] = V["note_text"]
        V["note_ok"] = "true"; ev(P, V, "note_after")
    assert "bank transfer" in notes.get("p1", "") and "bank transfer" not in notes.get("p2", "x"), notes
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "dispute", topic="dispute", offer_for="first", customer_said="I never opened that card")
    ev(P, V, "hardship", topic="hardship")
    ev(P, V, "hs_decline", hs_answer="support_no")
    notes = [V["note_text"]]
    while V.get("route") == "note":
        V["note_ok"] = "true"; ev(P, V, "note_after")
        if V.get("route") == "note":
            notes.append(V["note_text"])
    assert any("I never opened that card" in n and "disputes" in n for n in notes), notes
    assert not any("I never opened that card" in n and "hardship" in n for n in notes), notes
    # the extraction exists only when the brief keeps notes
    names = lambda pol_: [e["name"] for e in pol_.negotiate_node("t", [], [])["extraction_schema"]]
    assert "customer_said" in names(mk(True, True)) and "customer_said" not in names(mk(False, False))


@test
def one_day_for_all_moves_a_closed_day_by_the_brief():     # Kestrel PUB-13: closed_day_move='before' for several products
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-26", offer_for="all")   # a holiday (Monday)
    assert V["agreed_p1"].startswith("420.0|2026-10-27"), V["agreed_p1"]               # default: the next business day
    P2 = mk(True, True, closed_day_move="before")
    import json
    V2 = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD, LOAN])}
    run(P2.prepare_code(BODY, "statement"), V2)
    ev(P2, V2, "offer", offer_kind="exact", offer_date="2026-10-26", offer_for="all")
    assert V2["agreed_p1"].startswith("420.0|2026-10-23"), V2["agreed_p1"]             # 'before': Friday 23 October


@test
def every_event_survives_empty_vars():
    P = mk(True, True)
    for name, e in pol.EVENT_NODES.items():
        V = {}
        exec(P.event_code(e), {"vars": V})
        assert "route" in V and "state_line" in V, (name, V)


@test
def node_sources_are_platform_safe():
    P = mk(True, True)
    nodes = {}
    P.add_event_nodes(nodes)
    for n in nodes.values():
        src = n["pre_actions"][0]["function"]["parameters"]["properties"]["code"]["default"]
        assert "{{" not in src and "}}" not in src
        compile(src, n["name"], "exec")
        assert n["transitions"][-1]["condition"]["operator"] == "always"


def main():
    fails = 0
    for t in TESTS:
        try:
            t()
            print("ok   " + t.__name__)
        except Exception as e:
            fails += 1
            print("FAIL %s: %r" % (t.__name__, e))
    print("%d/%d policy tests pass" % (len(TESTS) - fails, len(TESTS)))
    return 1 if fails else 0


@test
def test_aside_prefix():
    """A side question in a turn that goes through code is answered first, in the line the route speaks."""
    import json
    P = pol.Policy(HOL, texts=TEXTS, asides={"robot": {"when": "asks whether they talk to a robot", "say": "I am the bank's digital assistant."}})
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    assert V.get("prepare_state") == "ok", V.get("prepare_state")
    V["stance"] = "accept"; V["aside"] = "robot"
    run(P.event_code("accept"), V)
    assert V.get("policy_state") == "ok", V.get("policy_state")
    key = {"confirm": "readback_line", "wrapup": "wrap_line"}.get(V.get("route"), "say_next")
    assert V[key].startswith("I am the bank's digital assistant."), (V.get("route"), V[key])
    assert V.get("aside") == "none"
    V["stance"] = "refuse"; V["aside"] = "none"
    run(P.event_code("refuse"), V)
    assert not V["say_next"].startswith("I am the bank"), V["say_next"]
    n = P.confirm_node("t", "c", "d", "a")
    assert any(e["name"] == "aside" for e in n["extraction_schema"]), n["extraction_schema"]


@test
def test_offer_when_resolved_in_code():
    """'tomorrow' and friends resolve against the CALL's today, not the real clock; a past extracted date is vague."""
    import json, datetime
    P, V = start([CARD])
    src = P.core()
    G = {"vars": V}
    exec(src + "\nout = {}\nfor w in ['tomorrow', 'next friday', 'this saturday', 'friday', 'the 23rd', 'the sixth of november', 'end of the month', 'day after tomorrow', 'in two weeks', 'November 6th', 'Monday the 26th', 'monday the twenty-sixth', 'next friday the 23rd', 'on friday 30', 'the twenty', 'on the thirty', 'the twenty third', '', 'monday the 26th', 'friday the 16th']:\n    d, k = resolve_when(vars, w)\n    out[w] = (d.isoformat() if d else None, k)\n", G)
    out = G["out"]
    assert out["tomorrow"] == ("2026-10-15", "exact"), out
    assert out["day after tomorrow"] == ("2026-10-16", "exact"), out
    assert out["next friday"] == ("2026-10-23", "exact"), out        # Wed 14 Oct: the Friday of the following week
    assert out["this saturday"] == ("2026-10-17", "exact"), out
    assert out["friday"] == ("2026-10-16", "exact"), out
    assert out["the 23rd"] == ("2026-10-23", "exact"), out
    assert out["the sixth of november"] == ("2026-11-06", "exact"), out
    assert out["November 6th"] == ("2026-11-06", "exact"), out
    assert out["in two weeks"] == ("2026-10-28", "exact"), out
    # a day of the month said with a weekday is that day, never the weekday's next occurrence (Freya PUB-07 talkative:
    # 'Monday the twenty-sixth' was read back as Monday 19 October)
    assert out["Monday the 26th"] == ("2026-10-26", "exact"), out
    assert out["monday the twenty-sixth"] == ("2026-10-26", "exact"), out
    assert out["next friday the 23rd"] == ("2026-10-23", "exact"), out
    assert out["on friday 30"] == ("2026-10-30", "exact"), out
    # a day cut off after its tens word is not a day (Freya talkative PUB-04: 'on the twenty' recorded as the 20th)
    assert out["the twenty"] == (None, "vague"), out
    assert out["on the thirty"] == (None, "vague"), out
    assert out["the twenty third"] == ("2026-10-23", "exact"), out
    P2, V2 = start([CARD])
    ev(P2, V2, "offer", offer_kind="exact", offer_date="2026-10-20", offer_when="the twenty", offer_amount="")
    # a cut-off day is asked again (not the vague question, which a second time offers the deadline: corrects PUB-07)
    assert V2.get("offer_verdict") == "cutoff", (V2.get("offer_verdict"), V2.get("say_next"))
    G2 = {"vars": V}
    exec(src + "\nr = resolve_when(vars, 'monday the 26th')\nr2 = resolve_when(vars, 'on monday the twenty sixth')\n", G2)
    assert G2["r"][0].isoformat() == "2026-10-26" and G2["r2"][0].isoformat() == "2026-10-26", (G2["r"], G2["r2"])   # EXT-B-14

    assert out["end of the month"] == (None, "vague"), out
    G2 = {"vars": V}
    exec(src + "\nout = {}\nfor w in ['Monday the 26th', 'Sunday the 25th', 'this Saturday, the 17th', 'on Friday the 23rd']:\n    d, k = resolve_when(vars, w)\n    out[w] = (d.isoformat() if d else None, k)\n", G2)
    o2 = G2["out"]
    P3 = pol.Policy(HOL, texts=TEXTS, weekday_rule="first_after")
    G3 = {"vars": {"today_iso": "2026-10-16"}}   # a Friday
    exec(P3.core() + "\nout = [resolve_when(vars, w)[0].isoformat() for w in ('this friday', 'next friday', 'friday', 'this saturday')]\n", G3)
    assert G3["out"] == ["2026-10-23", "2026-10-23", "2026-10-16", "2026-10-17"], G3["out"]
    n = P3.hardship_node("t", "a", "k", "d", "m", human=True)
    assert n["transitions"][0]["target_node"] == "pol_human" and "human" in n["extraction_schema"][0]["enum_values"], n["transitions"][0]
    assert o2 == {'Monday the 26th': ('2026-10-26', 'exact'), 'Sunday the 25th': ('2026-10-25', 'exact'),
                  'this Saturday, the 17th': ('2026-10-17', 'exact'), 'on Friday the 23rd': ('2026-10-23', 'exact')}, o2
    assert out[""] == (None, "none"), out
    assert out["monday the 26th"] == ("2026-10-26", "exact"), out      # the number wins over the weekday (PUB-07)
    assert out["monday the twenty-sixth"] == ("2026-10-26", "exact"), out
    assert out["friday the 16th"] == ("2026-10-16", "exact"), out
    # the offer event: the extraction said 2026-10-11 (real clock) but the words say tomorrow -> 15 Oct is checked
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-11", offer_when="tomorrow", offer_amount="420")
    assert V.get("offer_verdict") == "ok", (V.get("offer_verdict"), V.get("say_next"))
    assert "15 October" in (V.get("readback_line") or V.get("say_next") or ""), (V.get("route"), V.get("readback_line"), V.get("say_next"))
    # a past date with no words is treated as vague (ask once for the exact day), never 'has already passed'
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-11", offer_when="", offer_amount="420")
    assert V.get("offer_verdict") == "vague", (V.get("offer_verdict"), V.get("say_next"))


@test
def test_change_without_change_is_a_no():
    """PUB-12: an all-products read-back answered with 'change' that resolves to the same date for everyone must not loop."""
    P, V = start([CARD, LOAN], multi=True)
    ev(P, V, "offer", offer_kind="exact", offer_when="tomorrow", offer_date="2026-10-15")
    assert V["route"] == "confirm", (V["route"], V.get("say_next"))
    line1 = V["readback_line"]
    ev(P, V, "change", offer_kind="exact", offer_when="tomorrow", offer_date="2026-10-15")   # once more is allowed
    ev(P, V, "change", offer_kind="exact", offer_when="tomorrow", offer_date="2026-10-15")   # the second repeat is a no
    assert not (V["route"] == "confirm" and V["readback_line"] == line1), (V["route"], V["readback_line"])


@test
def test_too_much_with_a_date_offers_the_floor():
    """EXT-A-36: 'the full amount is too much, but I can pay the minimum today' arrives as an exact offer with no number
    (the extractor does not know the floor): the floor is offered once with the brief's too-much sentence, on the
    named day, never the full amount."""
    P, V = start([CARD])
    ev(P, V, "offer", stance="too_much", offer_kind="exact", offer_when="today", offer_amount="", offer_ref="none")
    assert V["route"] == "confirm" and V["ok_amount"] == "126.0" and V["ok_date"] == TODAY, (V["route"], V.get("ok_amount"), V.get("ok_date"))
    assert V["readback_line"].startswith("I understand. The lowest amount I can accept is 126") and "rest stays overdue" in V["readback_line"], V["readback_line"]
    assert V["readback_line"].endswith("credit card ending 4821, 126, today. Do you confirm?"), V["readback_line"]
    assert V["too_much_p1"] == "yes" and V["offered_floor_p1"] == "yes"
    # with a weekend day the guard still moves it, and the amount stays the floor
    P, V = start([CARD])
    ev(P, V, "offer", stance="too_much", offer_kind="exact", offer_when="saturday", offer_amount="", offer_ref="floor")
    assert V["offer_verdict"] == "weekend_or_holiday" and V["prop_amount"] == "126.0" and V["prop_date"] == "2026-10-19", (V["offer_verdict"], V["prop_amount"], V["prop_date"])
    assert V["say_next"].startswith("I understand. The lowest amount I can accept is 126"), V["say_next"]
    # as measured on Freya: stance 'offer' (not too_much), the floor by reference, today
    P, V = start([CARD])
    ev(P, V, "offer", stance="offer", offer_kind="exact", offer_when="today", offer_amount="", offer_ref="floor")
    assert V["route"] == "confirm" and V["ok_amount"] == "126.0" and "rest stays overdue" in V["readback_line"], (V["route"], V.get("ok_amount"), V["readback_line"])
    assert V["too_much_p1"] == "no"


@test
def test_amount_by_reference():
    """'I can pay the minimum' / 'all of it': the reference is resolved in code against the product (offer_ref)."""
    P, V = start([LOAN])
    ev(P, V, "offer", stance="offer", offer_kind="none", offer_when="", offer_amount="", offer_ref="floor")
    assert V["route"] == "confirm" and V["ok_amount"] == "700.0" and V["ok_date"] == TODAY, (V["route"], V.get("ok_amount"))
    # at the read-back: 'make it the minimum instead' is a change to the floor, read back again
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_when="friday", offer_amount="2100", offer_ref="none")
    assert V["route"] == "confirm" and V["ok_amount"] == "2100.0"
    ev(P, V, "change", confirm="change", offer_when="", offer_amount="", offer_ref="floor")
    assert V["route"] == "confirm" and V["ok_amount"] == "700.0" and V["ok_date"] == "2026-10-16", (V["route"], V.get("ok_amount"), V.get("ok_date"))
    n = P.confirm_node("t", "c", "d", "a")
    assert any(e["name"] == "offer_ref" for e in n["extraction_schema"])
    assert "offer_ref" in str(P.offer_guard_transitions()[0]), P.offer_guard_transitions()[0]


@test
def test_unchanged_change_is_not_a_loop():
    """EXT-A-36: a 'change' at the read-back that names nothing new re-read the same line 28 times. Once it is read
    back again; the second such answer in a row is a no to the read-back offer (the ladder's next rung)."""
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_when="today", offer_amount="", offer_ref="none")
    assert V["route"] == "confirm" and V["ok_amount"] == "420.0"
    first = V["readback_line"]
    ev(P, V, "change", confirm="change", offer_when="", offer_amount="", offer_ref="none")
    assert V["route"] == "confirm" and V["readback_line"] == first, (V["route"], V["readback_line"])
    ev(P, V, "change", confirm="change", offer_when="today", offer_amount="420", offer_ref="none")
    assert V["route"] == "negotiate" and V["say_next"] == "Can you pay 420 on Friday 16 October?", (V["route"], V["say_next"])
    assert V["same_change"] == "0"
    # a real change resets the count
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_when="today", offer_amount="", offer_ref="none")
    ev(P, V, "change", confirm="change", offer_when="", offer_amount="", offer_ref="none")
    ev(P, V, "change", confirm="change", offer_when="tomorrow", offer_amount="", offer_ref="none")
    assert V["route"] == "confirm" and V["ok_date"] == "2026-10-15" and V["same_change"] == "0", (V["route"], V.get("ok_date"))


@test
def test_per_product_claims_in_one_turn():
    """EXT-B-02: 'the card is not mine, I paid the loan yesterday, I will pay the car loan in full today' in answer to
    the all-products question. Only the card is a dispute and only the loan is paid; the car loan goes to the guard and
    the read-back. Before: topic=dispute settled every open product as dispute and the call ended."""
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    ev(P, V, "dispute", topic="dispute", per_product="first=dispute;second=paid;third=pay", offer_when="today", offer_amount="")
    assert (V["state_p1"], V["state_p2"], V["state_p3"]) == ("dispute", "paid", "agreed"), (V["state_p1"], V["state_p2"], V["state_p3"])
    assert V["route"] == "confirm" and V["ok_pid"] == "p3" and V["ok_amount"] == "75.0" and V["ok_date"] == TODAY, (V["route"], V.get("ok_pid"), V.get("ok_amount"))
    rb = V["readback_line"]
    assert "credit card ending 4821" in rb and "personal loan" in rb and rb.endswith("car loan, 75, today. Do you confirm?"), rb
    assert V["per_product"] == ""
    ev(P, V, "confirm_yes", confirm="yes")
    assert V["route"] == "record" and V["rec_pid"] == "p3"
    V["rec_ok"] = "true"; ev(P, V, "rec_after")
    notes = []
    while V["route"] == "note":
        notes.append((V["note_pid"], V["note_reason"])); V["note_ok"] = "true"; ev(P, V, "note_after")
    assert notes == [("p1", "dispute"), ("p2", "paid")], notes
    # claims with a refusal for the rest: the settled ones first, then one by one from the first OPEN product
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    ev(P, V, "refuse", stance="refuse", per_product="first=paid;second=refuse;third=refuse")
    assert V["state_p1"] == "paid" and V["cur_pid"] == "p2" and V["route"] == "negotiate", (V["state_p1"], V["cur_pid"])
    assert V["say_next"].startswith("Thank you for letting me know.") and "personal loan" in V["say_next"], V["say_next"]
    # no claims: the old behaviour (a dispute about everything)
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "dispute", topic="dispute", per_product="")
    assert V["state_p1"] == "dispute" and V["state_p2"] == "dispute"
    # single product: no per_product extraction at all
    assert not mk().claims_extraction() and mk(multi=True).claims_extraction()[0]["name"] == "per_product"


@test
def test_per_product_days_in_one_turn():
    """EXT-B-09: 'the card and the loan today, the car loan on Monday the 26th of October' (a holiday): the one
    extracted date was applied to every product, so the two 'today' products were capped at their deadline. Each
    product now gets its own day words; the holiday moves to the next business day and the read-back says so."""
    P, V = start([CARD, LOAN, CAR], multi=True, notes=True)
    ev(P, V, "offer", offer_kind="exact", offer_date="2026-10-26", offer_when="monday the twenty-sixth of october", offer_amount="",
       per_product="first=pay@today;second=pay@today;third=pay@monday the twenty-sixth of october")
    assert V["route"] == "confirm", (V["route"], V.get("say_next"))
    assert V["agreed_p1"].split("|")[:2] == ["420.0", TODAY] and V["agreed_p2"].split("|")[:2] == ["2100.0", TODAY], (V["agreed_p1"], V["agreed_p2"])
    assert V["agreed_p3"] == "75.0|2026-10-27|bd", V["agreed_p3"]
    assert "car loan, 75, on Tuesday 27 October" in V["readback_line"] and "today" in V["readback_line"], V["readback_line"]


@test
def test_no_notes_before_a_later_transfer():
    """EXT-B-06: card promised, loan refused, then a restructuring request in the wrap-up. With
    notes_on_transfer=False the loan's note waits for the wrap-up: the transfer adds none; 'nothing else' writes it."""
    import json
    def go():
        P = pol.Policy(HOL, texts=TEXTS, multi=True, notes=True, notes_on_transfer=False,
                       note_reasons={"refused": "refused", "hardship": "hardship", "dispute": "dispute", "paid": "paid", "service_error": "service_error"})
        V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD, LOAN])}
        run(P.prepare_code(BODY, "statement"), V)
        ev(P, V, "offer", offer_kind="exact", offer_when="today", offer_amount="", per_product="first=pay@today;second=refuse")
        assert V["state_p1"] == "agreed" and V["cur_pid"] == "p2", (V["state_p1"], V["cur_pid"], V.get("say_next"))
        ev(P, V, "refuse", stance="refuse"); ev(P, V, "refuse", stance="refuse")
        assert V["state_p2"] == "refused" and V["route"] == "confirm", (V["state_p2"], V["route"])
        ev(P, V, "confirm_yes", confirm="yes"); V["rec_ok"] = "true"; ev(P, V, "rec_after")
        return P, V
    P, V = go()
    assert V["route"] == "wrapup" and V["noted_p2"] == "no", (V["route"], V["noted_p2"])     # no note yet
    P, V = go()
    ev(P, V, "finalize", wrap="done")
    assert V["route"] == "note" and V["note_pid"] == "p2" and V["note_reason"] == "refused", (V["route"], V.get("note_pid"))
    V["note_ok"] = "true"; ev(P, V, "note_after")
    assert V["route"] == "fin" and V["final_route"] == "promise", (V["route"], V.get("final_route"))
    # default (notes_on_transfer=True): the note right after the promises, as before
    P, V = start([CARD, LOAN], multi=True, notes=True)
    ev(P, V, "accept", stance="accept")
    ev(P, V, "confirm_yes", confirm="yes"); V["rec_ok"] = "true"; ev(P, V, "rec_after")
    V["rec_ok"] = "true"; ev(P, V, "rec_after")
    assert V["route"] == "wrapup", V["route"]


@test
def test_change_per_product_and_recorded_guard():
    """EXT-B-14: (1) a holiday moved for one product is explained, not only tagged ', the next business day';
    (2) a change at the read-back naming each product's day is applied per product (it had put the loan's amount on
    the card: 'that is the most I can record', in a loop); (3) a recorded product is never reopened or recorded again."""
    P, V = start([CARD, CAR], multi=True, notes=True)
    ev(P, V, "offer", offer_kind="exact", offer_when="", offer_amount="", per_product="first=pay@today;second=pay@monday the 26th of october")
    assert V["route"] == "confirm" and V["agreed_p2"] == "75.0|2026-10-27|bd", (V["route"], V.get("agreed_p2"))
    assert V["readback_line"].startswith("Monday 26 October is not a business day. The next business day is Tuesday 27 October."), V["readback_line"]
    ev(P, V, "change", confirm="change", offer_amount="75", offer_when="monday the 26th", per_product="first=pay@today;second=pay@monday the 26th")
    assert V["route"] == "confirm" and V["agreed_p1"].startswith("420.0|" + TODAY) and V["agreed_p2"] == "75.0|2026-10-27|bd", (V["route"], V["agreed_p1"], V["agreed_p2"])
    assert "Monday 26 October is not a business day" in V["readback_line"], V["readback_line"]
    ev(P, V, "confirm_yes", confirm="yes"); V["rec_ok"] = "true"; ev(P, V, "rec_after"); V["rec_ok"] = "true"; ev(P, V, "rec_after")
    assert V["state_p1"] == "recorded" and V["state_p2"] == "recorded"
    for e, kw in (("change", dict(confirm="change", offer_when="friday", offer_amount="")), ("confirm_no", dict(confirm="no")),
                  ("accept", dict(stance="accept")), ("offer", dict(offer_kind="exact", offer_when="friday"))):
        ev(P, V, e, **kw)
        assert V["state_p1"] == "recorded" and V["state_p2"] == "recorded", (e, V["state_p1"], V["state_p2"])
        assert V["route"] in ("wrapup", "fin", "note"), (e, V["route"])


@test
def test_tomorrow_when_text():
    """Optional 'tomorrow_when' text: the read-back for tomorrow names the relative day too; '' (default) keeps the date."""
    import json
    P = pol.Policy(HOL, texts=dict(TEXTS, tomorrow_when="tomorrow, [date]"))
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="exact", offer_when="tomorrow", offer_amount="")
    assert V["readback_line"] == "To confirm: credit card ending 4821, 420, tomorrow, Thursday 15 October. Do you confirm?", V["readback_line"]
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_when="tomorrow", offer_amount="")
    assert V["readback_line"].endswith("420, on Thursday 15 October. Do you confirm?"), V["readback_line"]


@test
def test_vague_again_refuse():
    """vague_again='refuse': no exact day after the one ask is a non-answer (one persuasion attempt), not the deadline."""
    import json
    P = pol.Policy(HOL, texts=TEXTS, vague_again="refuse")
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([LOAN])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="vague", offer_when="next week")
    assert V["say_next"] == "Which exact day would that be?", V["say_next"]
    ev(P, V, "offer", offer_kind="vague", offer_when="I can't say")
    assert V["attempts_used_p1"] == "1" and V["prop_date"] == "2026-10-16", (V["attempts_used_p1"], V["prop_date"])
    assert V["say_next"] == "Can you pay 2,100 on Friday 16 October?" or "16 October" in V["say_next"], V["say_next"]


@test
def test_above_full_agree():
    """above_full='agree': an amount above the full amount goes straight to the read-back of the full amount."""
    import json
    P = pol.Policy(HOL, texts=TEXTS, above_full="agree", promise_reasons={"full": "full", "partial": "partial"})
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="exact", offer_when="this friday", offer_amount="500")
    assert V["route"] == "confirm" and V["agreed_p1"].startswith("420.0|2026-10-16"), (V["route"], V.get("agreed_p1"))
    assert V["readback_line"].startswith("The past-due amount is 420"), V["readback_line"]
    # a date problem as well: ask again (the corrected offer), never agree silently
    P2 = pol.Policy(HOL, texts=TEXTS, above_full="agree")
    V2 = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P2.prepare_code(BODY, "statement"), V2)
    ev(P2, V2, "offer", offer_kind="exact", offer_when="sunday", offer_amount="500")
    assert V2["route"] == "negotiate" and V2["offer_verdict"] == "weekend_or_holiday", (V2["route"], V2["offer_verdict"])


@test
def test_promise_reasons_and_ending_code():
    """promise_reasons: reason full/partial written when the promise is recorded; ending_code lets it decide a later transfer."""
    import json
    for amount, want in (("420", "full"), ("200", "partial")):
        P = pol.Policy(HOL, texts=TEXTS, promise_reasons={"full": "full", "partial": "partial"})
        V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
        run(P.prepare_code(BODY, "statement"), V)
        ev(P, V, "offer", offer_kind="exact", offer_when="tomorrow", offer_amount=amount)
        assert V["route"] == "confirm", V["route"]
        ev(P, V, "confirm_yes", confirm="yes")
        V["rec_ok"] = "True"
        ev(P, V, "rec_after")
        assert V["route"] == "wrapup" and V["outcome"] == "promise" and V["reason"] == want, (V["route"], V["outcome"], V["reason"])
        run(P.ending_code("transferred", "agent_request"), V)
        assert (V["outcome"], V["reason"]) == ("promise", want), (V["outcome"], V["reason"])
    V = {}
    run(P.ending_code("transferred", "agent_request"), V)
    assert (V["outcome"], V["reason"]) == ("transferred", "agent_request"), V
    V = {"recorded_pids": "p1"}
    run(P.ending_code("transferred", "agent_request", promise_decides=False), V)
    assert V["outcome"] == "transferred", V


@test
def test_repeated_change_is_bounded():
    """The same above-full correction repeated at the read-back ends after max_checks, never loops forever."""
    import json
    P = pol.Policy(HOL, texts=TEXTS, above_full="agree", max_checks=4)
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="exact", offer_when="this friday", offer_amount="500")
    routes = []
    for _ in range(6):
        if V["route"] != "confirm":
            break
        ev(P, V, "change", confirm="change", offer_when="friday", offer_amount="500")
        routes.append(V["route"])
    assert routes[-1] == "fin" and V["final_route"] == "refused" and len(routes) <= 4, routes


@test
def test_above_full_again():
    """A repeated above-full correction at the read-back gets the optional above_full_again sentence."""
    import json
    tx = dict(TEXTS, above_full_again="AGAIN [named] [full].")
    P = pol.Policy(HOL, texts=tx, above_full="agree")
    V = {"today_iso": TODAY, "now": TODAY + "T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="exact", offer_when="this friday", offer_amount="500")
    assert V["readback_line"].startswith("The past-due amount is 420"), V["readback_line"]
    ev(P, V, "change", confirm="change", offer_when="friday", offer_amount="500")
    assert V["route"] == "confirm" and V["readback_line"].startswith("AGAIN 500 420."), V["readback_line"]



@test
def test_cutoff_day_and_amount():
    """Days cut off mid-word or said in pieces (Freya styles-final: pieces PUB-13, corrects PUB-07 and PUB-04)."""
    # pieces PUB-13: 'thirty...' then 'October.' is 30 October, never the deadline after a second 'vague'
    P, V = start([CARD, LOAN], multi=True)
    ev(P, V, "offer", offer_kind="exact", offer_for="all", offer_when="thirty", offer_date="2026-10-30")
    assert V["offer_verdict"] == "cutoff", (V["offer_verdict"], V["say_next"])
    ev(P, V, "offer", offer_kind="vague", offer_for="all", offer_when="October", offer_date="2026-10-30")
    assert V["route"] == "confirm" and "Friday 30 October" in V["readback_line"], V.get("readback_line")
    # corrects PUB-07: 'Monday the twenty' (cut off) is asked again; the next piece 'sixth' completes it
    P, V = start([CARD])
    ev(P, V, "offer", offer_kind="exact", offer_when="Monday the twenty", offer_date="2026-10-19")
    assert V["offer_verdict"] == "cutoff" and V["say_next"].startswith("Sorry"), V["say_next"]
    ev(P, V, "offer", offer_kind="exact", offer_when="sixth", offer_date="2026-10-06")
    assert "26 October" in V["say_next"] and "Tuesday 27 October" in V["say_next"], V["say_next"]
    # corrects PUB-04: 'I accept the twenty' extracted as amount 20 (below the floor) is asked again once, the floor
    # is not spent; a second 20 is a real offer
    P, V = start([LOAN])
    q = V["offer_question"]
    ev(P, V, "offer", offer_kind="exact", offer_amount="20")
    assert V["offer_verdict"] == "cutoff_amount" and V["say_next"].endswith(q) and V["offered_floor_p1"] == "no", V["say_next"]
    ev(P, V, "offer", offer_kind="exact", offer_amount="20")
    assert V["offer_verdict"] == "below_floor" and V["offered_floor_p1"] == "yes", V["offer_verdict"]
    # an amount that is not day-sized, or one with a day, goes straight through the guard
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="20", offer_when="friday")
    assert V["offer_verdict"] == "below_floor", V["offer_verdict"]
    # 'thirty October' / 'October twenty six' as cardinals beside a month
    G = {"vars": V}
    exec(P.core() + "\nr = [resolve_when(vars, w) for w in ['thirty October', 'october twenty six', 'the twenty']]\n", G)
    assert [(d.isoformat() if d else None, k) for d, k in G["r"]] == [("2026-10-30", "exact"), ("2026-10-26", "exact"), (None, "vague")], G["r"]



@test
def test_pieces_day_units_and_cents():
    """A day or an amount said in two turns (Freya pieces, cert5: PUB-04 'Friday twenty' / 'Three' became Friday 16
    and an amount of 3; PUB-06 'six hundred and thirty-seven' / 'and fifty cents this Friday' ended as refused)."""
    G = {"vars": {"today_iso": TODAY, "now": TODAY + "T11:00"}}
    P, V = start([LOAN])
    exec(P.core() + "\nr = [resolve_when(vars, w) for w in ['Friday twenty three', 'the thirty one', 'friday twenty']]\n", G)
    got = [(d.isoformat() if d else None, k) for d, k in G["r"]]
    assert got[0][0] and got[0][0].endswith("-23") and got[1][0] and got[1][0].endswith("-31") and got[2] == (None, "vague"), got
    # 'Friday twenty' with the tens word taken as amount 20: a cut-off DAY; 'Three' completes it, not an amount
    P, V = start([LOAN])
    ev(P, V, "offer", offer_kind="exact", offer_amount="20", offer_when="Friday twenty")
    assert V["offer_verdict"] == "cutoff", (V["offer_verdict"], V["say_next"])
    ev(P, V, "offer", offer_kind="exact", offer_amount="3", offer_when="Three")
    txt = V.get("readback_line", "") + " " + V.get("say_next", "")
    assert "cannot record 3" not in txt and " 23 " in txt and "2100" in txt.replace(",", ""), txt
    # cents in the next turn: 637 is asked again (not below the floor), then 'and fifty cents' makes 637.50
    CENTS = {"words": "credit card ending 1903", "full": 2125.10, "floor": 637.50, "days_late": 12}
    for piece in ("0.5", "50"):
        P, V = start([CENTS])
        ev(P, V, "too_much", stance="too_much")
        ev(P, V, "offer", offer_kind="exact", offer_amount="637")
        assert V["offer_verdict"] == "cutoff_amount" and V["pending_amount"] == "637", (V["offer_verdict"], V["say_next"])
        ev(P, V, "offer", offer_kind="exact", offer_amount=piece, offer_when="this Friday")
        assert V["route"] == "confirm" and "637.50" in V["readback_line"], (piece, V["offer_verdict"], V.get("readback_line"), V["say_next"])
    # a whole amount that is no target's cut-off goes through the guard as before
    P, V = start([CENTS])
    ev(P, V, "offer", offer_kind="exact", offer_amount="500")
    assert V["offer_verdict"] == "below_floor" and not V.get("pending_amount"), V["offer_verdict"]


@test
def test_today_named_in_readback():
    """'this Friday' said on a Friday is today; with today_when the read-back names the day (EXT-A-38: a bare 'today'
    was refused by a customer who did not know the date, and the promise moved to the next Friday)."""
    import json
    P = pol.Policy(HOL, texts={**TEXTS, "today_when": "today, [date]"})
    V = {"today_iso": "2026-10-16", "now": "2026-10-16T11:00", "test_products": json.dumps([CARD])}
    run(P.prepare_code(BODY, "statement"), V)
    ev(P, V, "offer", offer_kind="exact", offer_when="this Friday")
    assert V["route"] == "confirm" and "today, Friday 16 October" in V["readback_line"], V.get("readback_line")


@test
def test_claims_need_a_named_product():
    """EXT-B-12: 'I paid the credit card yesterday and I never had a' (cut off) was settled as a dispute of the
    personal loan; the extraction only pairs a claim with a product the message names."""
    d = mk(True).claims_extraction()[0]["description"]
    assert "NAMES" in d and "never guess" in d, d


@test
def test_once_only_offers_not_repeated():
    """The floor and the hardship offer are said once by code; the state line and the node prompts forbid the
    dialogue model to repeat them on small talk (Freya talkative PUB-05: support offered 3 times; PUB-06: the
    minimum offered twice)."""
    P, V = start([LOAN])
    ev(P, V, "too_much", stance="too_much")
    assert "already said once" in V["state_line"] and "ask exactly this" not in V["state_line"], V["state_line"]
    P, V = start([LOAN])
    assert "ask exactly this" in V["state_line"], V["state_line"]
    ev(P, V, "hardship", topic="hardship")
    assert "never say them again" in V["state_line"], V["state_line"]
    n = P.negotiate_node("TASK", [], [fl.always("negotiate")])
    h = P.hardship_node("TASK", "a", "k", "d", "m")
    for node in (n, h):
        assert pol.ONCE_RULE.strip() in str(node), node.get("name")



if __name__ == "__main__":
    sys.exit(main())
