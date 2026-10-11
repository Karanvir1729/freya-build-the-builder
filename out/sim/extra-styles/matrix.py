"""Builds the cases x styles matrix of out/extra-styles.REPORT.md from the sim JSON files (before and after the fixes).
python3 out/sim/extra-styles/matrix.py"""
import json, pathlib
D = pathlib.Path(__file__).parent
STY = ["terse", "rambling_corrects", "pieces_identity", "impatient", "previous_question", "volunteer", "silent_turn",
       "hangs_up_after_promise", "final_like"]
AB = {"terse": "terse", "rambling_corrects": "ramb", "pieces_identity": "pieces", "impatient": "impat",
      "previous_question": "prevq", "volunteer": "volun", "silent_turn": "silent", "hangs_up_after_promise": "hangup",
      "final_like": "final"}
# classification of every failure of the first round (read from the transcripts; see the report)
CLASS = {
    "PUB-05[terse]": "J", "PUB-05[impatient]": "J", "PUB-05[previous_question]": "J",
    "PUB-05[hangs_up_after_promise]": "J", "PUB-05[final_like]": "J",
    "PUB-05[pieces_identity]": "B",
    "PUB-07[previous_question]": "S", "PUB-09[pieces_identity]": "C", "PUB-09[impatient]": "C",
    "PUB-10[final_like]": "S",
    "PUB-12[rambling_corrects]": "S", "PUB-12[pieces_identity]": "B", "PUB-12[previous_question]": "J",
    "PUB-13[rambling_corrects]": "S",
}


def rows(files):
    out = {}
    for f in files:
        p = D / f
        if p.exists():
            for r in json.load(open(p))["rows"]:
                out[r["id"]] = r
    return out


def table(rows_, cases, after=None):
    hdr = "| case | " + " | ".join(AB[s] for s in STY) + " |\n|---|" + "---|" * len(STY) + "\n"
    body = ""
    for c in cases:
        cells = []
        for s in STY:
            k = "%s[%s]" % (c, s)
            r = rows_.get(k)
            if r is None:
                cells.append("–")
                continue
            if r["pass"]:
                cells.append("PASS")
            else:
                cell = "FAIL·" + CLASS.get(k, "?")
                if after and k in after:
                    cell += " → " + ("PASS" if after[k]["pass"] else "FAIL")
                cells.append(cell)
        body += "| %s | %s |\n" % (c, " | ".join(cells))
    return hdr + body


def totals(rows_, after=None):
    lines = []
    for s in STY:
        ks = [k for k in rows_ if k.endswith("[%s]" % s)]
        n = sum(rows_[k]["pass"] for k in ks)
        m = n + sum(1 for k in ks if not rows_[k]["pass"] and after and k in after and after[k]["pass"])
        lines.append("| %s | %d / %d | %d / %d |" % (s, n, len(ks), m, len(ks)))
    return "| style | before | after one rerun of the failures |\n|---|---|---|\n" + "\n".join(lines)


A = rows(["a-pub.part1.json", "a-pub.part2.json", "a-pub.part3.json"])
B = rows(["b-pub.json"])
after = rows(["rerun/" + f.name for f in sorted((D / "rerun").glob("*.json"))]) if (D / "rerun").exists() else {}
print("## Brief A (brief-a-v3-x, public cases PUB-01..10)\n")
print(table(A, ["PUB-%02d" % i for i in range(1, 11)], after))
print("\n" + totals(A, after))
print("\n## Brief B (brief-b-v3-x, public cases PUB-11..13)\n")
print(table(B, ["PUB-11", "PUB-12", "PUB-13"], after))
print("\n" + totals(B, after))
