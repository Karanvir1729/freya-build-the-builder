# Rule inventory: conflicts and doubts (brief-a.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Rules found by only one extraction sample (confidence low)

- **R01** (_brief-a.md intro_, samples B): Freya Bank is fictional; every customer, debt and payment is synthetic.
- **R23** (_openapi.json /verify_identity_, samples C): An unreadable DOB is rejected with ok=false and does not count as a wrong answer; phone_last4 must be four digits.

## Values that differ between the extraction samples

- **R18** (_brief-a.md rule 11_): A16 and C17 include hint_values ["day_month_swapped"] on date_of_birth; B18 omits hint_values
  - chosen: `{"identity": [{"order": 1, "field": "date_of_birth", "hint_values": ["day_month_swapped"]}, {"order": 2, "field": "phone_last4"}]}`
  - B18: `{"identity": [{"order": 1, "field": "date_of_birth"}, {"order": 2, "field": "phone_last4"}]}`

