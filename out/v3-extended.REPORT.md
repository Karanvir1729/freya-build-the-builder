# v3 (policy as code) on the extended case sets: report

10 Oct 2026, cloud worker, branch `cloud/v3-extended`. Local simulator only (`builder/sim.py --concurrency 2`, customer
`gpt-5-mini`, judge `gpt-5`, OpenAI key checked: HTTP 200). `tools/run_cases.py` was not run.

| Slot | workflow_id | agent_id | versions |
|---|---|---|---|
| `brief-a-v3` | `f278ab9e-e94b-41c3-8b91-07bf2cca2e83` | `70e4b01f-e9e8-4c08-905a-1bcf6c7b9122` | v1 = round 1, v5 = round 2, v6 = final |
| `brief-b-v3` | `b030ebb0-ab59-49d7-9352-2414bd10662b` | `4ff79460-e3e6-483f-abcb-34a8c8a85a9b` | v1 = round 1, v3 = round 2, v4 = final |

`.freya-agents.json` had no entry for either slot in this container, so the first save created two new workflows.
Round 1 ran the generators exactly as committed on `main` (regenerating gave no diff).

## Headline

| | Round 1 (as committed) | Round 2 (failures only, fixed agents) | Best estimate after round 2 |
|---|---|---|---|
| Brief A extended (42) | **35 / 42** (v2 reference: 34/42) | 4 / 7 | 39 / 42 (the 3 left: 1 case error, 2 simulator artefacts) |
| Brief B extended (14) | **8 / 14** | 5 / 6 | 13 / 14 (the 1 left: a judge artefact) |

"Best estimate" assumes the round-1 passes still pass. **That was not measured**: the instructions allow reruns of failed
cases only, and the fixes touch shared paths (a new extraction field on negotiate/confirm/hardship, new multi-product
logic). See "Not done" below.

No failing call had a `validation_errors` or `extraction_failed` event in the platform's call log (all 13 round-1
failures checked through `freya.get_call(call_id)['messages']`): none of the failures came from a dropped write or a
discarded extraction.

## Round 1 (`out/sim/v3-ext/a-ext1/`, `b-ext1/`)

### Brief A: 35 / 42

| Case | What happened | Class |
|---|---|---|
| EXT-A-02 | The customer asked "am I talking to a robot?". The agent answered "I am Freya Bank's digital assistant. Am I speaking with Mr Park?". The customer asked the same question again, and the second ask closed the call as `not_reached/unclear`. | **simulator artefact** (the script says "After the answer, say 'Yes, that's me.'"). Hedged in the wording, see the post-round-2 changes. |
| EXT-A-03 | Same pattern with "Is this a scam?". | **simulator artefact** (passed in round 2) |
| EXT-A-11 | Read-back "420, on Thursday 15 October" after "the full amount tomorrow" (call date Wed 14 Oct). The customer said "No, I don't confirm. I'll pay the full amount tomorrow" three times. The agent read back the same line twice, then took it as a no, and attempt 1 (Fri 16) was recorded. | **simulator artefact**: the kit's `PERSONA` text never gives the customer the call's date, so "tomorrow" cannot be matched to a date (reproduced in round 2). The agent-side loop is fixed (see fix 3). |
| EXT-A-13 | Asked "What is this call about?" twice instead of answering. The agent said "I can explain that right after the security questions" and closed `declined` on the second question, but never said that the questions protect the account. | **agent bug**, A rule 15 ("explain once that the questions protect their account"; asking what the call is about counts as declining). Mechanism: a question back goes to `qb_<stage>` and then the model's prompt, never through the refusal path that carries the explanation. Fix 6. |
| EXT-A-17 | Below the floor, then refused the floor. Attempt 2 named the floor again on the deadline, and the judge failed it for "offered 400 twice". | **case error** (already marked in docs/ext-a-v2-failures.md): A rule 26 "Attempt 2 may name the floor again, on the deadline"; rule 30 "Attempt 2 … the floor amount on the deadline". |
| EXT-A-35 | The customer said its post-promise line ("Can I move that to Monday instead?") in its very first turn, then said "No, that's all" at the wrap-up. | **simulator artefact** (passed in round 2) |
| EXT-A-36 | "The full amount is too much, but I can pay the minimum today." went to `offer_kind=exact` with no number (the extractor does not know the floor; stance came out `offer`), so the guard read back the **full** 365. Every "No, the minimum today" was then `confirm=change` with no new value, and the same read-back was spoken **28 times** until max turns. | **agent bug**, A rules 26, 27 and 35. Fixes 1, 2 and 3. |

### Brief B: 8 / 14

| Case | What happened | Class |
|---|---|---|
| EXT-B-02 | One answer to "Can you pay all of them today?": the card is not mine, I paid the loan, the car loan in full today. `topic=dispute` with no single `offer_for` target settled **all three** products as dispute (3 dispute notes) and closed `no_promise/dispute`. | **agent bug**, B rules 8 and 9. Mechanism: one `topic` per turn cannot express different claims for different products. Fix 4. |
| EXT-B-06 | Card promised, loan refused twice, then "For the loan I need lower instalments" in the wrap-up. A `refused` note for the loan was written right after the promise, before the restructuring transfer. | **agent bug**, B rule 10 ("On any transfer (restructuring, support, human) add no notes at all, before or after it"). Fix 5. |
| EXT-B-09 | "Card and loan in full today, the car loan on Monday the 26th of October": the one extracted date (26 Oct) was applied to every product, so the two "today" products were moved to their deadline (23 Oct). | **agent bug**, B rule 4/6 (one date for everything is the only case where one date applies to all). Fix 4. |
| EXT-B-10 | One product, refused twice; `add_note refused`, `no_promise/refused`. The judge counted the mandatory opening "Can you make this payment today?" (A rule 28) as a persuasion attempt. | **judge artefact** (same as EXT-A-25 in docs/ext-a-v2-failures.md) |
| EXT-B-12 | Paid card, refused loan, disputed car loan: same mechanism as EXT-B-02, all three noted `dispute`, closed `dispute` (expected `refused`, the first non-paid note). | **agent bug**, B rules 8, 9 and closing. Fix 4. |
| EXT-B-14 | (a) Card today, loan on Monday 26 October (a holiday): same as EXT-B-09, both moved to 27 Oct. (b) The customer's correction at the read-back named both products' days; `change_offer` applied the loan's 900 to the card ("the past-due amount is 300, so that is the most I can record") in a loop. (c) The moved holiday was only tagged ", the next business day" and never explained. (d) From turn 24 a cascade of 504/503 answers, with replies recovered out of order: the engine ran the confirm node again after the promises were recorded, `create_promise` was called again for both products ("this product already has a promise"), and the call closed `service_error`. | (a)–(c) **agent bug** (B rule 6/7, A rules 20 and 35): fixes 4 and 7. (d) **simulator/platform artefact** (gateway errors under load), but the agent must never re-record a product: fix 8. |

## Round 2 (`out/sim/v3-ext/a-ext2/`, `b-ext2/`): reruns of the round-1 failures only

| Case | Result | Reason / class |
|---|---|---|
| EXT-A-02 | FAIL | the same repeated robot question (2/2 runs). Simulator artefact; post-round wording hedge below |
| EXT-A-03 | PASS | |
| EXT-A-11 | FAIL | the customer again called the "tomorrow" read-back "not correct" (2/2 runs); the new loop guard closed it as a refusal. Simulator artefact; post-round hedge below |
| EXT-A-13 | **PASS** | fix 6: "these questions protect your account" is said once, then the call closes on the second question |
| EXT-A-17 | FAIL | case error (unchanged, as expected) |
| EXT-A-35 | PASS | |
| EXT-A-36 | **PASS** | fixes 1–3: "I understand. The lowest amount I can accept is 109.50, your minimum payment. The rest stays overdue. To confirm: … 109.50, today." The first `create_promise` fails (the mock's fault), the retry is recorded, then the text-message sentence |
| EXT-B-02 | **PASS** | card disputed, loan paid, car loan read back and recorded; notes `dispute`, `paid`; `promise` |
| EXT-B-06 | **PASS** | promise, restructuring transfer, **no** note |
| EXT-B-09 | **PASS** | card and loan today, car loan 27 Oct, one read-back |
| EXT-B-10 | FAIL | judge artefact (unchanged, as expected) |
| EXT-B-12 | **PASS** | notes `paid`, `refused` (after two attempts on the loan), `dispute`; closed `refused` |
| EXT-B-14 | **PASS** | "Monday 26 October is not a business day, so I cannot record it. The next business day is Tuesday 27 October." in the one read-back; one `create_promise` per product |

## The generic fixes and why they transfer

All of them are in `builder/policy.py` (brief-agnostic, signatures kept: only new keyword arguments) or the skill. The
brief's wording goes into the generators. Every fix has a unit test in `builder/tests/test_policy.py` (40/40 pass;
`test_lint` 29/29, `test_normalise` 144/144; the three `out/compare_*.py` summaries are unchanged from `main`).

1. **Amount by reference (`offer_ref` none|floor|full).** Any bank has a floor and customers name it by its name ("the
   minimum", "the instalment"), not as a number. The extractor cannot turn that into a number because it does not know
   the value. The reference is now extracted on the negotiate, confirm and hardship nodes and resolved in code against
   that product's floor or full amount, and it routes to the guard like a named amount. The generator passes the brief's
   own names for its floor (`ref_desc=`). Test: `test_amount_by_reference`.
2. **"Too much, but I can pay <day>" / the floor asked for by name.** The too-much rule applies to the amount and the
   named day still goes through the date guard. The floor is offered once, with the brief's `too_much_floor` sentence,
   on that day, and never the full amount. Test: `test_too_much_with_a_date_offers_the_floor`.
3. **A read-back `change` that names nothing new is not a loop.** It is read back once more. The second one in a row
   counts as a no to the read-back offer, and the ladder decides what comes next. Before this, `change_offer` reset the
   per-product check counter on every change, so `max_checks` could never trip. Any brief has a read-back with a
   change route. Test: `test_unchanged_change_is_not_a_loop`.
4. **Per-product claims in one turn (`per_product`, multi only).** One string extraction
   (`first=dispute;second=paid;third=pay@<the customer's words for that day>`) parsed in code (`claims`,
   `settle_claims`, `pay_claimed`, `change_claims`). Paid and disputed products are settled one by one with the
   brief's sentences, each `pay` product gets its own day, and the rest goes one by one from the first **open**
   product (`to_one_by_one` used to restart at product 1 whatever its state). It is automatic for `Policy(multi=True)`
   on the negotiate and confirm nodes. It holds for any brief with more than one product, because a customer answering
   "all of them?" answers per product. Tests: `test_per_product_claims_in_one_turn`, `test_per_product_days_in_one_turn`,
   `test_change_per_product_and_recorded_guard`.
5. **`Policy(notes_on_transfer=False)`.** When a brief adds no notes on a call that ends in a transfer, the notes wait
   until the wrap-up after a recorded promise has ended without one. A restructuring or human request from the wrap-up
   then adds none, and "nothing else" writes them. The default keeps the old order. The Brief B generator passes False
   (B rule 10). Test: `test_no_notes_before_a_later_transfer`.
6. **A question back at an identity question carries the brief's decline explanation.** It is routed away from the
   refusal path by design (fl.question_back_node), so the explanation the refusal path gives was never said. This
   holds for any brief that counts a question back as declining. It lives in the skill and the
   `question_back_node` docstring, and the wording is in the generators' identity prompts.
7. **A moved weekend/holiday is explained before the read-back** (`moved_note`: the brief's `weekend_or_holiday`
   sentence), not only tagged ", the next business day". The customer then knows why their day changed.
8. **One promise per product, enforced in code (`recorded_guard`).** `check_one`, `ev_change` and `ev_confirm_no` never
   reopen a recorded product: they speak the brief's change sentence and go to the wrap-up. This covers any engine
   replay of a confirm turn (seen under 504s), so a recorded promise can no longer be turned into `service_error` by an
   "already has a promise" answer.
9. **`resolve_when("Monday the 26th")`** resolves by the day number. The weekday alone had given next Monday.

### After round 2 (unit-tested, not re-simulated: the 2-round limit)

- **Optional `tomorrow_when` text** ('' = off): the generators pass `"tomorrow, [date]"`, so the read-back says
  "tomorrow, Thursday 15 October" when the day is tomorrow. This echoes the customer's own word. It is aimed at
  EXT-A-11, where the simulated customer does not know the call's date, and it also helps a real customer. Test:
  `test_tomorrow_when_text`.
- **Yes/no side questions answered with the yes first** ("Yes, I am Freya Bank's digital assistant."): this is in the
  generators' opening-retry prompt, system prompt and robot aside, plus a skill note. It is aimed at EXT-A-02. The scam
  answer is unchanged.

## Remaining failures, classified

| Case | Class | Note |
|---|---|---|
| EXT-A-17 | case error | contradicts A rules 26 and 30 (the floor may be named again on attempt 2) |
| EXT-B-10 | judge artefact | counts the mandatory first ask (A rule 28) as a persuasion attempt; same as EXT-A-25 |
| EXT-A-11 | simulator artefact | the persona has no call date (kit `PERSONA` in `tools/run_cases.py`, which `sim.py` reuses). Agent hedge applied after round 2, unverified |
| EXT-A-02 | simulator artefact (reproducible with gpt-5-mini) | rule 3 makes a question at the second ask close the call. Agent hedge applied after round 2, unverified |

## Not done / caveats

- **No regression run of the round-1 passes.** Fixes 1–4 add extraction fields: negotiate goes 7→8 variables on A and
  8→10 on B, confirm 6→7 on A and 6→8 on B (`lint --budget` warns above 4 on all three nodes, as before). More
  variables mean slower extraction and a little more risk of mislabelling. A full rerun of both extended sets, plus one
  organisers' public pass when the simulator is free, should come before these versions are trusted over `main`.
- The two post-round-2 changes were not simulated.
- Round 2 was started once on agent versions 4/2 and stopped after about 3 minutes to add the "floor asked for by name"
  case (the platform's stance for A-36 was `offer`, not `too_much`). The chat calls it had opened were abandoned and not
  ended. Its partial output was deleted, and the round-2 tables above are the complete rerun on versions 5/3.
- Fix 4 relies on the extractor filling `per_product` when one answer covers several products. The two measured cases
  (B-02, B-12) and the two date cases (B-09, B-14) did. With no claims, the old single-topic behaviour applies.
- Open from earlier (not touched): a cap on repeating the identical spoken line in the negotiate node (the read-back
  loop is now capped); the speech normaliser is still attached nowhere.
