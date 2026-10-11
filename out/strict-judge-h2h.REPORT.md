# Head-to-head and strict-judge fixes (11 Oct 2026, ~05:10-07:30 UTC)

Branch `fixes/strict-judge` (worktree `/Users/karanvirkhanna/freya-bb-strict`), commit `8b92b75` on top of main `0ec3765`.
Not merged into main. It does not touch `state_line`, `negotiate_node`, `ONCE_RULE` or `CUTOFF_CLAUSE`.

## 1. Head-to-head against github.com/emrebarkind/freyahackathon

Both builders built synthetic Briefs D and F from scratch (hidden-brief conditions: briefs copied as `h2h-d.md` /
`h2h-f.md` so `build.py` did not auto-load the scoring cases). Scored with `builder/sim.py` on
`tests/synthetic/brief-{d,f}.cases.json`, 13 cases x 3 runs, `--close-from-args`, gpt-5-mini customer, gpt-5 judge.

| | D | F | total | runs passed | build time |
|---|---|---|---|---|---|
| ours (`0ec3765`) | 10/13 | 9/13 | 19/26 | 67/78 | 21.8 / 22.0 min |
| theirs | 6/13 | 8/13 | 14/26 | 48/78 | 3.9 / 3.1 min |

Theirs: Claude extracts one typed JSON spec, a fixed 2,200-line Python engine runs in one code node every turn, the model
never calls a tool. Its losses were things the spec cannot express: floors as formulas (2x minimum; max(50%, minimum)),
note `text` never sent, an always-on write retry (F allows one try), multi-product closure-day moves and calls left
without `close_call`, a 13x read-back loop. Bias: our library had already been fixed against D/F cases; theirs never saw
them. Their F PUB-01 opening is an `on_enter` tts on the first node, which the chat route skips.

## 2. What the fixes are (all brief-agnostic)

- `policy.py`: per-product last offer (`last_amount_<pid>`, `last_date_<pid>`, set in `set_prop`, read by
  `last_offer_of`). The refusal note read the call-wide `prop_*`, so in a multi-product call the loan's note named the
  full amount today (D PUB-12, 0/3 before).
- `policy.py`: every note text ends with `Call date: today, <weekday day month year>.` (D PUB-08: the brief asks for
  "the channel and the day they say they paid"; "this morning" named no day).
- `policy.py`: `vague_again='week_end'`, the extension the D build wrote and build.py reverted (its generator could not
  be regenerated without it).
- `freyalib.third_party_callback`: `reask_text` is appended to the node's prompt; `CB_OFFER_DESC` converts the time to
  24-hour first. The extraction read 18:30 as inside a window closing at 17:00, no route fired, and the model's own
  re-ask left the hours out (F PUB-02).
- `freyalib.third_party_offer(nodes, offer_line)`: `<name>_offer` = the third-party node entered with the brief's
  thanks-and-no before its fixed entry line; `tp_offered` extracted on the conversation nodes leading there; every route
  to `third_party` copied with `AND tp_offered == 'yes'`. The offer comes in the same message as "who is this?", which
  a fixed tts entry line cannot react to (D/F PUB-02). SKILL.md and FREYALIB.md say when to use it.
- `sim.py --strict-judge` (criteria read literally) and `sim.py <x> --rejudge DIR --cases f` (judge saved transcripts
  again, no calls: 39 gpt-5 calls per agent).
- Tests: `builder/tests/test_policy.py` 59/59 (two new), `builder/tests/test_third_party.py` 3/3 (new); lint 31/31,
  normalise 148/148, buildguard 15/15, gated identity 6/6; gen_brief-a_v3 / gen_brief-b_v3 regenerate, lint 0 errors.

## 3. Strict judge, before and after (same cases, 3 runs, a case counts with 3/3)

Before (re-judged transcripts of the build above): D 9/13, F 7/13.
After (agents regenerated from their own generators on the branch, F with one added `third_party_offer` call):
D runs 12/13 and 11/13, F runs 8/13 and 9/13 (run 3 still going when this was written). D/F PUB-02, D PUB-12 and the
D PUB-08 note pass in every finished run.

What still fails under the strict judge, and why it was left:
- "1275" vs "1275.00" (D PUB-06, F PUB-10, PUB-12): only our synthetic case writers write whole amounts with `.00`; the
  organisers' public checks never do. `fmt()` drops `.00`; not changed (spoken output, voice TTS).
- F PUB-05 / PUB-08: "Would you be able to pay the full overdue balance today?" counted as a proposal. The brief says
  "First ask, as written", before the customer mentions hardship or paying.
- F PUB-04: the case says both "no proposal is made" and "offers the latest date"; the agent offers the latest date.
- D PUB-08: "on our side" is in the brief's verbatim sentence; the case paraphrased it.

## 4. Open bug found, not fixed (negotiation path)

F PUB-06, 1 of 3 runs on the branch (passed 3/3 before, so likely variance, but a real gap): after the floor offer
("Would you be able to pay 1062.55 today, Wednesday 14 October?") the customer said "I accept 1062.55. I can't pay before
my salary; what's the latest day I can have to pay?". The agent read back 1062.55 today twice (the accept was taken,
the date refusal and the question ignored), then proposed Friday 16 October instead of the latest date, Thursday 22
October. Transcript: scratchpad `h2h/tx/strict2-ours-f/PUB-06-r1.txt` of session a0819b6b. The fix belongs where
accept + a date objection + "what's the latest day?" are classified (stance/offer extraction, `accept_offer`), i.e. the
code the other session is changing.

## 5. Things learned on the way

- The builder's Claude calls use the terminal `claude` login, not the desktop app's. It was a Console login ("API Usage
  Billing", apiKeySource `/login managed key`) and ran out of credit at 05:39 UTC ("Credit balance is too low" for every
  model). Re-logged in with the Max plan; test calls through the Agent SDK now report apiKeySource `none` and succeed.
- Freya workflows created by this work: `h2h-d` 1f0ac146 (v4), `h2h-f` 7195bdbc (v3), `theirs-h2h-d` eab0d215,
  `theirs-h2h-f` 88306a8d, plus `h2h-f2` from a fresh branch build that was stopped part way.
