# Styles final: the frozen v3 agents under the five kit styles (organisers' simulator)

Measurement run on 10 Oct 2026, 22:53–23:37 UTC. The agents were not changed, regenerated or saved: brief-a-v3 = agent  (cert3 version 17) and brief-b-v3 = agent  (cert3 version 15).
Each cell is one run of  (1 rep). Raw results are in . I read every failing call with . None returned 413 (no looping call). No call was slow: the slowest turn in any failing call was 8.0 s.

**Credits used: 10 simulator runs** (budget 12). Another session in the same workspace (a simulation named  on the Brief B agent) ran at the same time. B talkative waited about 16 minutes for it, then completed normally, so no simulation was force-completed.

## Result: 59/65 (A 46/50, B 13/15)

{m}
Classes: **agent** = an agent bug brought out by the style's persona (the rule and mechanism are below). **judge** = the verdict contradicts the transcript or the brief. No failure was purely a persona-model artefact, but two agent bugs were triggered by persona cut-offs, and in A-corrects PUB-07 the persona also went off-script.

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

### 1. A day cut off mid-word, or said across two turns (3 failures: A-corrects PUB-04, A-corrects PUB-07, B-pieces PUB-13) — agent bug
- **B pieces PUB-13** (one date for both products): the customer said "I want to pay both on thirty…", then "October." on the next turn.  ends on a bare tens word, so  returned *vague* and the agent asked "Which exact day would that be?". The next turn's  resolved to nothing, , and nobody joined it to the previous turn's "thirty". The second vague answer took the  path and the agent offered the card's deadline (Mon 2 Nov), which the customer accepted. The ledger has the card on 2026-11-02; the case expects 2026-10-30. The same happened on the loan (deadline 23 Oct, which is correct there by luck). The extractor's  was right but is deliberately ignored after a vague .
- **A corrects PUB-07**: the customer said "The twenty-fifth, sorry, I mean Monday the twenty" (cut off before "-sixth"). The cut-off rule made it *vague*. That was the second vague answer (after "the week after next"), so the agent offered the deadline (Mon 2 Nov) instead of asking again. The persona accepted it (off-script: its script says "accepts the next business day", i.e. Tue 27 Oct). The ledger has 2026-11-02; the case expects 2026-10-27.
- **A corrects PUB-04**: "Am I talking to a robot? I accept the twenty" (cut off before "-third"). Extraction gave , , with no date. The offer guard treated it as a below-floor amount, spent the once-only floor offer ("I cannot record 20. The lowest amount I can record is 400, your monthly instalment. Can you pay 400 on Friday 23 October?"), and the customer took it. The ledger has 400; the case expects 1250 on 23 Oct. The robot aside was answered correctly.
- **Patch** (, commit "policy: cut-off days…", test ):
  - A cut-off day (: the words end on "twenty"/"thirty") is now asked again with a new neutral text  ("Sorry, I did not catch the day. Which day would that be?"). It no longer counts as the vague question, so a second cut-off never jumps to the deadline.
  - The unresolved day words of the last policy turn ( → ) are joined with this turn's words, so "thirty" + "October" gives 30 Oct and "Monday the twenty" + "sixth" gives the 26th. After a cut-off, the join is tried first.
  - Cardinal day numbers next to a month name resolve ("thirty October", "October twenty six"). A bare "twenty" is still never a day.
  - A day-sized amount (a whole number from 1 to 31, below the floor, said with no day) is asked again once, with  + the current offer, before the floor is spent. If the customer repeats it, it is treated as a real offer.
  - Each is capped at 2 asks per call. All new texts are generic defaults (no bank wording), overridable by a generator.
  - The intentional behaviour change in the existing test  (verdict  → ) is updated.

### 2. A once-only offer repeated by the dialogue model on small-talk turns (2 failures: A-talkative PUB-05, PUB-06) — agent bug
- **PUB-05** (hardship, declines support): code said the sympathy line and the support offer once. Then 5 small-talk or cut-off turns came in with , so no route fired and the dialogue model answered. Following the generator's hardship prompt ("answer in one short sentence, then ask whether they want to be connected"), it re-asked the support offer twice. The judge saw three offers against the brief's "offer once". The ledger was correct (no_promise/hardship).
- **PUB-06** (too much, accepts the floor):  correctly offered 637.50 once. On "How much can you let me pay instead?" (), the dialogue model followed the state line () and said the floor again. The judge counted two floor offers. The ledger was correct. This is a borderline judge strictness case, but the agent did repeat the offer, so I count it as an agent bug.
- **Patch** (commit "policy: once-only offers…", test ):
  - When the current offer is the floor and it has been offered, the state line now says "Current offer, already said once: … Never repeat its amount or the question; … ask only whether they can do that". In hardship mode it says "The sympathy and the offer of help were already said once: never say them again".
  -  and  append  (reply in one short sentence or "Please go on." and wait).
  - The reference generators  and  no longer tell the hardship node to re-ask the support offer.
  - The skill's counters bullet says never to write a prompt line that re-asks a once-only offer.

### 3. A question back followed by the question re-posed, counted as a re-ask (1 failure: B-asks_back PUB-12) — judge artefact
- The ledger was exactly right: one promise on p1 for 15 Oct,  notes on p2 and p3, two attempts on the loan and one on the car loan. The check "the phone question is asked again once, the date of birth is not" failed because the judge counted these as re-asks:
  - the DOB question re-posed after the persona's scripted "Why do you need that?";
  - the phone question re-posed after "Which account is this about?".

  The only re-ask after a wrong answer (4401 → 4410) was the single phone re-ask, as the case wants. The verdict contradicts the transcript.
- Mitigation, not patched: in the question-back path, end the answer with "go ahead when you are ready" instead of restating the question. The asks_back persona answers anyway. I did not apply it because a real customer may need the question restated, and this is the judge's reading, not a rule of the brief.

## Notes
- Patched builder state: lint gives 0 errors on both regenerated reference workflows, and the warning counts equal the unpatched baseline (45 / 46). Policy tests pass 48/48 (2 new), normalisation 148/148, lint tests 29/29. The workflows were generated to the scratchpad only; nothing was saved or published, and the frozen agents still hold the unpatched policy.
- The patches are untested on Freya. They need one simulator round (corrects + talkative on A, pieces on B) on a non-frozen slot before they go into a certified build.
