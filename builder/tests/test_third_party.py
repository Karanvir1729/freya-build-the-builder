"""Third-party helpers: the re-ask sentence in the node's prompt (Ashvale PUB-02: the extraction read 18:30 as inside a
window closing at 17:00 and the model's own re-ask left the hours out) and third_party_offer (Ashvale/Kestrel PUB-02:
an offer to pay made in the same message as 'who is this?' was never declined).

    python3 builder/tests/test_third_party.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import freyalib as fl  # noqa: E402

REASK = "Calls can be arranged between 08:30 and 17:00. Is there another time that would suit?"
ENTRY = "I'm calling about a private matter for {{title}} {{last_name}}. When can they be reached?"


def graph(offer=True):
    nodes = {}
    nodes["opening"] = fl.conv("opening", "Opening.", on_enter={"type": "tts", "text": "Hello."},
                               extraction=[fl.ext("who1", ["customer", "someone_else", "unclear"], "who")])
    nodes["opening_retry"] = fl.conv("opening_retry", "Ask again.", extraction=[fl.ext("who2", ["customer", "someone_else"], "who")],
                                     transitions=[fl.eq("who2", "customer", "ask", "customer"),
                                                  fl.eq("who2", "someone_else", "third_party", "someone else answered"),
                                                  fl.always("fin_cb")])
    nodes["ask"] = fl.conv("ask", "Ask.", transitions=[fl.always("fin_cb")])
    initial = fl.conversation_first("opening", "vars['x'] = 1\n", "who1",
                                    [("customer", "ask", "customer"), ("someone_else", "third_party", "someone else answered")],
                                    "opening_retry", nodes)
    fl.end_pair("cb", "not_reached", "CB", "Goodbye.", nodes)
    fl.end_pair("ncb", "not_reached", "NCB", "Goodbye.", nodes)
    fl.third_party_callback(nodes, "Book a callback.", [], [], [fl.always("fin_cb")], REASK, "fin_ncb",
                            on_enter={"type": "tts", "text": ENTRY})
    if offer:
        fl.third_party_offer(nodes, "Thank you, but no.")
    return initial, nodes


TESTS = []


def test(f):
    TESTS.append(f)
    return f


@test
def reask_sentence_in_the_prompt():
    _, nodes = graph(offer=False)
    for name in ("third_party", "third_party_reask"):
        assert REASK in nodes[name]["task_message"], nodes[name]["task_message"]


@test
def offer_node_and_routes():
    initial, nodes = graph()
    off = nodes["third_party_offer"]
    assert off["on_enter"] == {"type": "tts", "text": "Thank you, but no. " + ENTRY}, off["on_enter"]
    assert off["transitions"] == nodes["third_party"]["transitions"]
    for src, var in (("setup", "who1"), ("opening_retry", "who2")):
        targets = [t["target_node"] for t in nodes[src]["transitions"]]
        assert targets.index("third_party_offer") == targets.index("third_party") - 1, (src, targets)
        t = nodes[src]["transitions"][targets.index("third_party_offer")]
        leaf = t["condition"]["conditions"][0]
        assert leaf["logic"] == "and" and {c["variable"] for c in leaf["conditions"]} == {var, "tp_offered"}, leaf
    # the offer is extracted where the person speaks: the opening (it leads into setup) and opening_retry
    for name in ("opening", "opening_retry"):
        assert "tp_offered" in [e["name"] for e in nodes[name]["extraction_schema"]], name
    assert "tp_offered" not in [e["name"] for e in nodes["ask"].get("extraction_schema", [])]
    fl.assemble(initial, nodes, "System.", [])          # check() passes: every target exists, every path ends


@test
def needs_a_fixed_entry_line():
    nodes = {"third_party": fl.conv("third_party", "Task.", transitions=[fl.always("x")])}
    try:
        fl.third_party_offer(nodes, "Thank you, but no.")
    except ValueError:
        return
    raise AssertionError("an llm entry line must be refused")


def main():
    bad = 0
    for f in TESTS:
        try:
            f()
            print("ok   " + f.__name__)
        except Exception as e:
            bad += 1
            print("FAIL %s: %r" % (f.__name__, e))
    print("%d/%d third-party tests pass" % (len(TESTS) - bad, len(TESTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
