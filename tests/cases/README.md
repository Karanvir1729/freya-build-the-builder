# Extended practice cases

More scored cases for the synthetic briefs, on top of the practice scripts in `tests/synthetic/`. Never read by the builder at run time.

The organisers' mock bank serves only the practice customers PUB-01..PUB-13 (fixed identity answers, products, `days_late`, and PUB-10's first `create_promise` failure). A case here reuses one of them through `mock_case` (e.g. `"PUB-03"`) with its own script, expected ledger and checks, so its `id` can be unique. Some cases also override `variables.now` (another call date; the mock enforces no date rule); every expected value of such a case is computed for that date.

| File | Brief | Cases | Rationale |
|---|---|---|---|
| `brief-c-extended.cases.json` | C (Nordvik, `tests/synthetic/brief-c.md`) | 30: `EXT-C-01`..`25` at 2026-10-14 11:00, `26`..`30` at other dates | `brief-c-extended.rationale.md` |
| `brief-d-extended.cases.json` | D (Kestrel, after the memo, `tests/synthetic/brief-d.md`) | 30: `EXT-D-01`..`25` at 2026-10-14 11:00, `26`..`30` at other dates | `brief-d-extended.rationale.md` |

Schema: as `tests/synthetic/brief-c.cases.json` (`id`, `brief`, `family`, `level`, `title`, `variables`, `identity`, `products`, `script`, `expected`, `checks`, `faults`) plus `mock_case`, and `third_party: true` on third-party cases. `identity`, `products` and `faults` are copied from the mock customer and are informative only: the mock decides them.

Run (local simulator over the chat route; needs `mock_case` support in `builder/sim.py`):

```bash
python3 builder/sim.py <workflow> --cases tests/cases/brief-c-extended.cases.json --concurrency 2
python3 builder/sim.py <workflow> --cases tests/cases/brief-d-extended.cases.json --concurrency 2 --only EXT-D-01,EXT-D-16
```

`tools/run_cases.py` opens practice sessions by case id, so it cannot run these files as shipped.
