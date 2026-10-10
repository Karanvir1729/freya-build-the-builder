# Organisers' simulator results (tools/run_cases.py, Freya credits)

Copies of the gitignored `results/freya-styles/*.json` and `results/freya-v3/*.json` so that cloud workers can read them.
`a-v2-<style>.json`: the v2 reference agent (slot brief-a-v2, agent 2f2a0c4e…) on the 10 Brief A public cases under one kit style.
`a-v3-x1.json` / `a-v3-x3.json`: the policy-as-code v3 agent (brief-a-v3, agent 7d100f1a…) once and with 3 reps; `b-v3-*`: brief-b-v3 on Brief B's cases; `a-v3-<style>.json`: v3 under each kit style.
Each row has `pass`, `failed` (the reasons), `call_id` (transcript via `freya.get_call`), `tools`, `slowest_turn_s`.

`a-v3-talkative-after.json`: brief-a-v3 (main at 20:24 UTC) under talkative, the paired baseline of persona-2. `a-v3p2-*.json` / `b-v3p2-*.json`: the persona-2 fixes on separate slots (brief-a-v3-p2 agent 458a5e90…, brief-b-v3-p2 agent 7148e3fe…); `-r2`/`-r3` are later versions; `a-v3p2-x1.json` unstyled. See out/persona-2.REPORT.md.
