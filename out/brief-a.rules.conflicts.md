# Rule inventory: conflicts and doubts (brief-a.md)

Resolve these FIRST, before writing the generator: re-read the quoted source sentence in the brief, decide, and use the value the brief sets (never a value from another brief). Anything not listed here was found by every extraction sample and, where it carries a value, verified against a quote of the brief.

## Rules found by only one extraction sample (confidence low)

- **R31** (_openapi.json /verify_identity_, samples C): `verify_identity` requires `customer_id`, `field` (`date_of_birth` or `phone_last4`) and `answer`; `phone_last4` answer is four digits; an unreadable value returns `ok=false` and is not counted as a wrong answer.
- **R32** (_openapi.json /schedule_callback_, samples C): `schedule_callback` requires `customer_id`, `date` (format date) and `time` as `HH:MM`.

