# Extra simulator styles on the v3 agents (public cases), 10–11 Oct 2026

Branch `cloud/extra-styles`. Local simulator `builder/sim.py` (chat route, gpt-5-mini customer, gpt-5 judge), `--styles extra`
(9 styles from `EXTRA_STYLES`), concurrency 2, one rep. Agents: the committed `out/gen_brief-a_v3.py` / `out/gen_brief-b_v3.py`
saved to the NEW slots `brief-a-v3-x` (workflow b3eaff30-…) and `brief-b-v3-x` (6e8d8427-…), version 1 = exactly the
committed files (the regenerated JSON was byte-identical to the commit). The frozen slots `brief-a-v3` / `brief-b-v3` were not touched.
`tools/run_cases.py` was not run.

Files: `out/sim/extra-styles/a-pub.part{1,2,3}.{json,log}`, `b-pub.{json,log}`, transcripts in `a-pub/` and `b-pub/`; the rerun
round in `rerun/` (+ `rerun2/`, one case); the matrix below is printed by `python3 out/sim/extra-styles/matrix.py`.

**Platform note.** At about 23:13–23:18 UTC the chat route answered HTTP 503 on every first turn (7 Brief A cases: PUB-03 x6 styles
and PUB-02[silent_turn], "no call was started" / two empty replies). The run was stopped and resumed after recovery (part 2 = PUB-02 x3
styles, part 3 = PUB-03..10 x9 styles); the matrix uses each case's run after recovery. A second episode at about 01:45–01:55 UTC
(503s, empty replies, a call resumed from an older message) spoiled two reruns; both are marked below.

Classes: **B** persona-induced agent bug (fixed, generic) · **J** judge artefact · **S** simulator artefact (the customer left its
script) · **C** chat-route artefact (`conversation_resumed isBranch=true`: the engine resumed the call from an older message; simulations
do not do this). "→" is the one rerun of the failures on the fixed agents (version 2, for PUB-12[previous_question] version 3).
No failure was "expected by the brief" (no style produced a legitimate hang-up without a promise).

## Brief A (brief-a-v3-x, public cases PUB-01..10)

| case | terse | ramb | pieces | impat | prevq | volun | silent | hangup | final |
|---|---|---|---|---|---|---|---|---|---|
| PUB-01 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-02 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-03 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-04 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-05 | FAIL·J → FAIL | PASS | FAIL·B → FAIL | FAIL·J → FAIL | FAIL·J → PASS | PASS | PASS | FAIL·J → FAIL | FAIL·J → FAIL |
| PUB-06 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-07 | PASS | PASS | PASS | PASS | FAIL·S → PASS | PASS | PASS | PASS | PASS |
| PUB-08 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-09 | PASS | PASS | FAIL·C → PASS | FAIL·C → PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-10 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL·S → PASS |


| style | before | after one rerun of the failures |
|---|---|---|
| terse | 9 / 10 | 9 / 10 |
| rambling_corrects | 10 / 10 | 10 / 10 |
| pieces_identity | 8 / 10 | 9 / 10 |
| impatient | 8 / 10 | 9 / 10 |
| previous_question | 8 / 10 | 10 / 10 |
| volunteer | 10 / 10 | 10 / 10 |
| silent_turn | 10 / 10 | 10 / 10 |
| hangs_up_after_promise | 9 / 10 | 9 / 10 |
| final_like | 8 / 10 | 9 / 10 |

## Brief B (brief-b-v3-x, public cases PUB-11..13)

| case | terse | ramb | pieces | impat | prevq | volun | silent | hangup | final |
|---|---|---|---|---|---|---|---|---|---|
| PUB-11 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PUB-12 | PASS | FAIL·S → FAIL | FAIL·B → PASS | PASS | FAIL·J → FAIL | PASS | PASS | PASS | PASS |
| PUB-13 | PASS | FAIL·S → FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS |


| style | before | after one rerun of the failures |
|---|---|---|
| terse | 3 / 3 | 3 / 3 |
| rambling_corrects | 1 / 3 | 1 / 3 |
| pieces_identity | 2 / 3 | 3 / 3 |
| impatient | 3 / 3 | 3 / 3 |
| previous_question | 2 / 3 | 2 / 3 |
| volunteer | 3 / 3 | 3 / 3 |
| silent_turn | 3 / 3 | 3 / 3 |
| hangs_up_after_promise | 3 / 3 | 3 / 3 |
| final_like | 3 / 3 | 3 / 3 |

Totals: Brief A **80/90 → 85/90**, Brief B **23/27 → 24/27** (one rerun of the failures). Every failure that remains is J or S
(or a platform-spoiled rerun); no ledger failure caused by the agent remains in the rerun round.

## Every failure, read from the transcript

| case | class | what happened |
|---|---|---|
| PUB-05 [terse, impatient, previous_question, hangs_up, final_like] | J | Same agent lines in all of them, including the PASSING styles (rambling_corrects, volunteer, silent_turn): statement + "Can you make this payment today?" (the brief's first ask, made BEFORE the hardship disclosure), sympathy once, support offered once, no plan. The gpt-5 judge reads the first ask as a "persuasion attempt although the band is late"; it flips run to run (prevq passed on the rerun). Ledger correct in all. The organisers' judge passed PUB-05 3/3 on this agent (cert run). Nothing to fix in the agent; the brief requires the ask. |
| PUB-05 [pieces_identity] | **B** | "eighty-eight" … "forty-six": the agent never joined the parts and asked for "the full four digits" ~30 times, the call ended not_verified/failed. Rerun on the fix: "And the rest, Mr Novak?" → verify 8846 → correct ledger; only the J verdict above remains. |
| PUB-07 [previous_question] | S | The customer flatly refused twice and never said "the week after next"/"Monday the 26th"; the agent made its two attempts and closed refused, as the brief says. Rerun: PASS. |
| PUB-09 [pieces_identity] | C | Correct restructuring transfer and end_call, then the engine resumed the call from an older message and the call continued to a refused close. Rerun: PASS. |
| PUB-09 [impatient] | C | After the statement the engine resumed the call in the identity node (`ask_phone`), the restructuring request was handled there and became a human transfer. Rerun: PASS. |
| PUB-10 [final_like] | S | "I will pay three hundred and sixty" (the style's split number, the second half never came); the read-back said 360, the customer confirmed 360 twice. Rerun: PASS. Side note (not fixed): the amount with no day was read back as "today" in the same line as "I can't pay today" (`stance` came out `offer`); the read-back caught it. |
| PUB-12 [rambling_corrects] | S | The style's wrong first day ("today") was never corrected at the read-back ("No, sorry, I meant 510 today, yes, I confirm"); recorded as confirmed. Same in the rerun. |
| PUB-12 [pieces_identity] | **B** (phrasing) | After a partial answer the agent repeated the whole phone question; the judge counted it as "asked again" (check: "the phone question is asked again once"). Fixed by "ask only for the rest". Rerun: PASS. |
| PUB-12 [previous_question] | J (style vs check) | The customer answered the previous question (DOB) at the phone question, so the phone question HAD to be asked again before the wrong 4401; the judge counts two re-asks. Ledger correct both times. The rerun exposed a real bug (next row). |
| PUB-12 [previous_question] rerun | **B** (fixed, ledger was saved by the read-back) | Repeating "I'll pay the credit card tomorrow and I will not pay the personal loan" while the loan was being asked (`offer_for=first`, `stance=refuse`) agreed the CARD's day for the LOAN: the read-back offered "your personal loan, 1320, tomorrow". The customer's "change" brought it back. Fixed in `policy.py` (`other_settled`); one run on version 3: correct ledger, clean read-back ("your credit card ending 9015, 510, tomorrow"), judge J as above. The transcript does not show whether the guard fired in that run. |
| PUB-13 [rambling_corrects] | S | "No, sorry, I meant 30 October, and yes, I confirm … the credit card on 2 November" in one line, then "Yes, I confirm" to the 2 November read-back; the agent took the last value, as it should. The rerun hit the 01:45 platform episode (empty replies, call resumed from an older message, not_verified): no information. |

## Generic fixes (commits 27bbbb7, 0a16fe3, c92871a)

1. **Identity answers in parts are joined across turns** (`builder/freyalib.py`): `latest_value_note(N)` / `latest_value_note(what=...)` now
   says to join the part from the previous message with the latest one (with a worked example for 4 digits), to call the tool once
   the parts are complete, never to ask again for a value the parts already give, and while a part is missing to ask **only for the rest**
   ("And the rest?") instead of repeating the question. `PERSONA_CONDUCT` (system prompt, `conduct=True`) says the same. The A/B v3
   generators now put the note on both identity nodes (the skill already required it; the A/B references had skipped it, Brief C v3 had
   it). `builder/lint.py` WARNs on any conversation node holding `verify_identity` whose prompt lacks a parts rule, so the builder
   (which fixes lint warnings) cannot ship an identity node without it. The skill and FREYALIB.md say so.
   *Why it transfers:* every brief has security questions with digits or dates; the sentence names no field, no value and no count beyond
   the N the generator reads from the brief/API.
2. **An offer for another, settled product is never applied to the product under discussion** (`builder/policy.py` `other_settled`):
   in a multi-product call at stage "one product at a time", when `offer_for` names a different product whose state is no longer
   open, the turn's refusal/"too much" counts for the CURRENT product and anything else gets the current question again.
   *Why it transfers:* it is a property of the per-product state machine (1–3 products, any ordinals, any ladder); no product, amount
   or date is named.

Tests: `builder/tests/test_policy.py` `test_identity_parts_across_turns` (note wording, conduct line, lint warning on/off) and
`test_offer_for_settled_other_product` (the PUB-12 sequence: card agreed, loan asked, card repeated with a refusal → loan rung 2, card
unchanged; a repeat without refusal → same question; an offer for the loan itself still agrees it). All suites pass:
test_policy 48/48, test_lint 29/29 (two fixtures updated for the new warning: the v1 reference `out/brief-a.workflow.json` predates it
and is filtered in `test_reference_workflows`; the rules fixture's identity prompt now carries a parts sentence), test_normalise 148/148,
test_gated_identity 6/6; `out/compare_*.py` summaries unchanged from main (brief-b_lib's 7 uncovered paths were there before). Lint of
both v3 workflows: 0 errors.

## Not done / open

- `out/brief-a_v3.workflow.json` and `out/brief-b_v3.workflow.json` were regenerated with the fixes (the committed files now differ from
  the FROZEN slots' published versions). The fixes were checked only on the -x slots, and only by the rerun round (no full re-sweep of all
  117 cases on the fixed agents and no organisers' simulation).
- PUB-05 judge artefact: not addressed (the agent is right; changing the local judge to pass would be a test that cannot fail).
- Possible next steps, not built: (a) an amount named with no day in a turn that also says "I can't pay today" still defaults to the
  proposal's day (the read-back is the only guard); (b) a cut-off amount at the end of a line ("three hundred and sixty") is acted on at
  once; (c) a loop guard on an identical agent line repeated many times (PUB-05[pieces] said the same sentence ~30 times before the fix).
- PUB-13[rambling_corrects] has no valid rerun (platform episode).
- Cost: about 136 chat-route calls in total (117 in the sweep incl. the 7 spoiled by the 503s and their reruns, 14 + 2 reruns), all at
  concurrency 2.
