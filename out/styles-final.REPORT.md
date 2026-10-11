# Styles final: the frozen v3 agents under the five kit styles (organisers' simulator)

Measurement run on 10 Oct 2026, 22:53–23:37 UTC. The agents were not changed, regenerated or saved:
- brief-a-v3 = agent `7d100f1a-7799-42ef-9d12-ff74aa69ff13` (cert3 version 17);
- brief-b-v3 = agent `24083493-68b9-4c7d-86d1-914ffa24b18c` (cert3 version 15).

Each cell is one run of `tools/run_cases.py <agent> --brief A|B --style <style>` (1 rep). Raw results are in `out/freya/final-<a|b>-<style>.json`. I read every failing call with `freya.get_call(call_id)['messages']`. None returned 413 (no looping call). No call was slow: the slowest turn in any failing call was 8.0 s.

**Credits used: 10 simulator runs** (budget 12). Another session in the same workspace (a simulation named `cases 19:24:15` on the Brief B agent) ran at the same time. B talkative waited about 16 minutes for it, then completed normally, so no simulation was force-completed.

## Result: 59/65 (A 46/50, B 13/15)

### Brief A — agent 7d100f1a (slot brief-a-v3, frozen)

| case | pieces | corrects | talkative | asks_back | in_words |
|---|---|---|---|---|---|
| PUB-01 | PASS | PASS | PASS | PASS | PASS |
| PUB-02 | PASS | PASS | PASS | PASS | PASS |
| PUB-03 | PASS | PASS | PASS | PASS | PASS |
| PUB-04 | PASS | FAIL agent (cut-off amount) | PASS | PASS | PASS |
| PUB-05 | PASS | PASS | FAIL agent (once-only offer repeated) | PASS | PASS |
| PUB-06 | PASS | PASS | FAIL agent (once-only offer repeated) | PASS | PASS |
| PUB-07 | PASS | FAIL agent (cut-off day) | PASS | PASS | PASS |
| PUB-08 | PASS | PASS | PASS | PASS | PASS |
| PUB-09 | PASS | PASS | PASS | PASS | PASS |
| PUB-10 | PASS | PASS | PASS | PASS | PASS |
| **total** | **10/10** | **8/10** | **8/10** | **10/10** | **10/10** |

### Brief B — agent 24083493 (slot brief-b-v3, frozen)

| case | pieces | corrects | talkative | asks_back | in_words |
|---|---|---|---|---|---|
| PUB-11 | PASS | PASS | PASS | PASS | PASS |
| PUB-12 | PASS | PASS | PASS | FAIL judge | PASS |
| PUB-13 | FAIL agent (day in pieces) | PASS | PASS | PASS | PASS |
| **total** | **2/3** | **3/3** | **3/3** | **2/3** | **3/3** |

Classes:
- **agent**: an agent bug brought out by the style's persona (the rule and mechanism are below).
- **judge**: the verdict contradicts the transcript or the brief.

No failure was purely a persona-model artefact. Two agent bugs were triggered by persona cut-offs, and in A-corrects PUB-07 the persona also went off-script.

## Per-style totals

| style | Brief A | Brief B | both |
|---|---|---|---|
| pieces | 10/10 | 2/3 | 12/13 |
| corrects | 8/10 | 3/3 | 11/13 |
| talkative | 8/10 | 3/3 | 11/13 |
| asks_back | 10/10 | 2/3 | 12/13 |
| in_words | 10/10 | 3/3 | 13/13 |
| **all** | **46/50** | **13/15** | **59/65** |

## Mechanisms, ranked by frequency

### 1. A day cut off mid-word, or said across two turns (3 failures) — agent bug
Failures: A-corrects PUB-04, A-corrects PUB-07, B-pieces PUB-13.

- **B pieces PUB-13** (one date for both products):
  1. The customer said "I want to pay both on thirty…". `offer_when='thirty'` ends on a bare tens word, so `resolve_when` returned *vague* and the agent asked "Which exact day would that be?".
  2. On the next turn the customer said "October.". `offer_when='October'` resolved to nothing and `offer_kind` came out `vague`. Nothing joined it to the previous turn's "thirty".
  3. As a second vague answer it took the `vague_again` path, and the agent offered the card's deadline (Mon 2 Nov), which the customer accepted.

  The ledger has the card on 2026-11-02; the case expects 2026-10-30. The same happened on the loan, where its deadline (23 Oct) happens to be the right answer. The extractor's `offer_date=2026-10-30` was right but is deliberately ignored after a vague `offer_when`.
- **A corrects PUB-07**: the customer said "The twenty-fifth, sorry, I mean Monday the twenty" (cut off before "-sixth"). The cut-off rule made it *vague*. That was the second vague answer (after "the week after next"), so the agent offered the deadline (Mon 2 Nov) instead of asking again. The persona accepted it, which is off-script: its script says "accepts the next business day", i.e. Tue 27 Oct. The ledger has 2026-11-02; the case expects 2026-10-27.
- **A corrects PUB-04**:
  1. The customer said "Am I talking to a robot? I accept the twenty" (cut off before "-third").
  2. Extraction gave `offer_amount=20.0` and `stance=offer`, with no date.
  3. The offer guard treated 20 as a below-floor amount and spent the once-only floor offer: "I cannot record 20. The lowest amount I can record is 400, your monthly instalment. Can you pay 400 on Friday 23 October?". The customer took it.

  The ledger has 400; the case expects 1250 on 23 Oct. The robot aside was answered correctly.
- **Patch** (`builder/policy.py`, commit "policy: cut-off days…", test `test_cutoff_day_and_amount`):
  - **Cut-off day asked again.** A day cut off mid-word (`cut_off()`: the words end on "twenty" or "thirty") gets a new neutral text, `cutoff_day`: "Sorry, I did not catch the day. Which day would that be?". It no longer counts as the vague question, so a second cut-off never jumps to the deadline.
  - **Pieces joined.** The unresolved day words of the last policy turn (`pending_when` → `when_prev`) are joined with this turn's words: "thirty" + "October" gives 30 Oct, and "Monday the twenty" + "sixth" gives the 26th. After a cut-off, the join is tried first.
  - **Cardinal days.** A cardinal day number next to a month name now resolves ("thirty October", "October twenty six"). A bare "twenty" is still never a day.
  - **Day-sized amount.** A whole number from 1 to 31, below the floor, said with no day, is asked again once (`cutoff_amount` + the current offer) before the floor is spent. If the customer repeats it, it is treated as a real offer.
  - **Limits.** Each ask is capped at 2 per call. The new texts are generic defaults (no bank wording), overridable by a generator.
  - **Existing test.** `test_offer_when_resolved_in_code` is updated for the intended change of verdict (`vague` → `cutoff`).

### 2. A once-only offer repeated by the dialogue model on small-talk turns (2 failures) — agent bug
Failures: A-talkative PUB-05, A-talkative PUB-06.

- **PUB-05** (hardship, declines support):
  1. Code said the sympathy line and the support offer once.
  2. Five small-talk or cut-off turns followed, with `hs_answer='none'`, so no route fired and the dialogue model answered.
  3. The generator's hardship prompt said "answer in one short sentence, then ask whether they want to be connected", so the model re-asked the support offer twice.

  The judge saw three offers against the brief's "offer once". The ledger was correct (no_promise/hardship).
- **PUB-06** (too much, accepts the floor): `too_much` correctly offered 637.50 once. Then the customer asked "How much can you let me pay instead?" (`stance='other'`). The dialogue model followed the state line (`Current offer, ask exactly this: "Can you pay 637.50 today?"`) and said the floor again. The judge counted two floor offers. The ledger was correct. This is a borderline judge strictness case, but the agent did repeat the offer, so I count it as an agent bug.
- **Patch** (commit "policy: once-only offers…", test `test_once_only_offers_not_repeated`):
  - **State line, floor.** When the current offer is the floor and it has been offered, the state line says "Current offer, already said once: … Never repeat its amount or the question; … ask only whether they can do that".
  - **State line, hardship.** In hardship mode it says "The sympathy and the offer of help were already said once: never say them again".
  - **Node prompts.** `negotiate_node` and `hardship_node` append `ONCE_RULE`: reply in one short sentence (or "Please go on.") and wait.
  - **Reference generators.** `out/gen_brief-a_v3.py` and `out/gen_brief-b_v3.py` no longer tell the hardship node to re-ask the support offer.
  - **Skill.** The skill's counters bullet says never to write a prompt line that re-asks a once-only offer.

### 3. A question back followed by the question re-posed, counted as a re-ask (1 failure) — judge artefact
Failure: B-asks_back PUB-12.

- The ledger was exactly right:
  - one promise, on p1, for 15 Oct;
  - `refused` notes on p2 and p3;
  - two attempts on the loan and one on the car loan.
- The check "the phone question is asked again once, the date of birth is not" failed because the judge counted these as re-asks:
  - the DOB question re-posed after the persona's scripted "Why do you need that?";
  - the phone question re-posed after "Which account is this about?".
- The only re-ask after a wrong answer (4401 → 4410) was the single phone re-ask, which is what the case wants. The verdict contradicts the transcript.
- Mitigation, not patched: in the question-back path, end the answer with "go ahead when you are ready" instead of restating the question. The asks_back persona answers anyway. I did not apply it because a real customer may need the question restated, and this is the judge's reading, not a rule of the brief.

## Notes
- **Lint.** Both reference workflows regenerated with the patched builder have 0 lint errors. Their warning counts (45 and 46) equal the unpatched baseline.
- **Tests.** Policy 48/48 (2 new), normalisation 148/148, lint 29/29.
- **Nothing published.** The workflows were generated to the scratchpad only; nothing was saved or published. The frozen agents still hold the unpatched policy.
- **Not yet tested on Freya.** The patches need one simulator round on a non-frozen slot (corrects and talkative on A, pieces on B) before they go into a certified build.
