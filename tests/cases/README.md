# Extended practice cases (Brief A, Brief B)

The 13 practice cases cover only a few rules. These files add 56 scored cases that cover every rule family of Brief A
and the multi-product rules of Brief B. The mock bank serves only the practice customers `PUB-01`..`PUB-13` (fixed
identity answers, products, `days_late`, faults), so each case reuses one of them through `mock_case` with its own
script, expected ledger and checks; some cases change `variables.now` (see `builder/SIM.md`, "Extended cases").

| File | What |
|---|---|
| `brief-a-extended.cases.json` | 42 cases `EXT-A-01`..`EXT-A-42` (6 of them on other call dates) |
| `brief-b-extended.cases.json` | 14 cases `EXT-B-01`..`EXT-B-14` (multi-product PUB-11..13, plus single-product customers under Brief B's note rules) |
| `brief-a-extended.rationale.md`, `brief-b-extended.rationale.md` | Derivation of every expected value, business-day ladders, what the fixed customers cannot test |
| `_gen_cases.py` | Writes both case files (mock data copied from `public-test-set.json`, expectations hand-written) |
| `verify_cases.py` | Independent re-derivation: own calendar code, recomputes every promise/callback, checks floors, deadlines, the outcome table, notes and the closing rule |

Run (local simulator only: `tools/run_cases.py` does not know `mock_case` or the `now` override):

```bash
source env.sh
python3 builder/sim.py <workflow> --cases tests/cases/brief-a-extended.cases.json --concurrency 2
python3 builder/sim.py <workflow> --cases tests/cases/brief-b-extended.cases.json --concurrency 2 --out results/sim-ext-b.json --transcripts results/ext-b/
python3 builder/sim.py <workflow> --cases tests/cases/brief-a-extended.cases.json --only EXT-A-09,EXT-A-41 --verbose
python3 tests/cases/verify_cases.py .          # after editing a case
```

Run Brief A cases against a Brief A agent and Brief B cases against a Brief B (or A+B) agent: the two rule sets differ
on notes. These files are test data for the developers; the builder never reads them.
