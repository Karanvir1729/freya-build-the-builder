# Synthetic transfer briefs

Test fixtures written by cloud workers to check that the builder reads a brief it has never seen, instead of memorising the kit's Brief A/B. They are NEVER read by the builder at run time; they are inputs for test runs and coverage audits only.

| Brief | Form | Scorable on the organisers' mock? | Files |
|---|---|---|---|
| C — Nordvik Savings Bank | clean spec, one product; phone-first identity, two wrong answers, Mon–Sat calendar, different holidays/bands/floors/reason names | yes: `brief-c.cases.json` reuses PUB-01..10 with recomputed expectations (verified by an independent reviewer) | `brief-c.md`, `brief-c.cases.json`, `brief-c.rationale.md` |
| D — Kestrel Bank | raw material: email + policy extract + memo overriding it + code list; up to three products; reason codes | yes: `brief-d.cases.json` reuses PUB-01..13 with recomputed expectations (verified by an independent reviewer) | `brief-d.md`, `brief-d.cases.json`, `brief-d.rationale.md` |
| E — Northgate Business Bank | clean spec with a DIFFERENT tool API: company_number/founded_year identity, new enums, extra required `channel` field, new outcomes | no (different identity fields/enums): use for generation, lint, dry-run, coverage audit and stubbed chat scenarios | `brief-e.md`, `brief-e.openapi.json`, `brief-e.scenarios.md` |
| F — Ashvale Bank | raw mailbox export: 5 threads with dated decisions that silently change earlier ones (late-band latest date, callback window, card floor, wrong-answer limit, hardship handling/code, create_promise retry), a partly stale desk card, a current code list, an HR holiday mail and a distractor migration thread; up to three products; purpose: implicit supersession | yes: `brief-f.cases.json` reuses PUB-01..13 with recomputed expectations under the rules in force (verified by an independent reviewer); 5 cases fail if the desk card is trusted | `brief-f.md`, `brief-f.cases.json`, `brief-f.rationale.md` |

Run a scorable one with the kit's scorer: `python3 tools/run_cases.py <agent_id> --cases tests/synthetic/brief-c.cases.json` (the `--brief` filter is not needed).

## Brief G — Corran Bay Bank (raw material, implicit changes, own codes)

| Brief | Form | Scorable on the organisers' mock? | Files |
|---|---|---|---|
| G — Corran Bay Bank | raw material: operations mail + Arrears Handling Standard extract + review minutes dated after it that change three rules with no "supersedes" wording (card floor, Middle-band last date, a moved closure day) + a dialler code card with its own reason codes and one closing sentence per code; up to three products handled most-days-late first and recorded one by one; per-question wrong-answer limit; part payments with a shorter last date; split payments; a once-per-call "second-look" callback for turned-down products | ledger yes, outcome/reason only with `sim.py --close-from-args` (the kit's mock validates the kit's reason table): `brief-g.cases.json` has 16 cases `G-01`..`G-16` on PUB-01..13 via `mock_case`, three on other call dates | `brief-g.md`, `brief-g.openapi.json` (close_call reason enum = the card's codes, `reason` required), `brief-g.cases.json`, `brief-g.rationale.md`; new persona styles in `tests/cases/brief-g.styles.json` |

Build: `python3 builder/build.py tests/synthetic/brief-g.md tests/synthetic/brief-g.openapi.json`. Run: `python3 builder/sim.py <workflow> --cases tests/synthetic/brief-g.cases.json --close-from-args`. The case file and the rationale are never given to the builder.
