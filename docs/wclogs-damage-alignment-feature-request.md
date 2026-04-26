# Warcraft Logs Damage Alignment Feature Request

## Purpose

Bring the v2 damage reports into much closer alignment with the numbers shown in the Warcraft Logs UI so users can trust that HK Logs is reporting the same damage totals they see on the source report.

This request is driven by a verified mismatch in the current Imperator Averzian damage report path.

## Problem Statement

The current target-damage implementation in HK Logs does not match Warcraft Logs' displayed damage totals for the same fight, target, and player.

Example report used during investigation:

- Report: `Xt8vWdnjJ26LCR4V`
- Fight: `42`
- Target: `Imperator Averzian`
- Player: `Pilgrimm`

Observed values:

- Warcraft Logs UI: `24,930,369`
- HK Logs current result: `26,030,302`

This is a trust problem. If users compare a player row in HK Logs against the corresponding Warcraft Logs target view and the values differ, they will assume the tool is wrong.

## Current Implementation

The current Imperator target-damage path is built on raw event aggregation:

- `who_messed_up/services/target_damage.py`
  - `_collect_target_damage()`
  - `_event_damage_amount()`

The implementation currently:

1. pulls `events(dataType: DamageDone)` for the fight window
2. filters by `target.name`
3. resolves the source back to the owning player
4. sums several raw event fields together

Current event sum:

- `amount`
- `absorbed`
- `overkill`
- `blocked`
- `resisted`
- `mitigated`

This is not WCLogs table math.

## Investigation Summary

### Sample reproduction

Using the exact report/fight/player/target above, the following totals were reproduced from the current code path:

- Raw events, `amount` only: `25,544,101`
- Raw events, `amount + absorbed`: `25,732,939`
- Current repo formula: `26,030,302`

Warcraft Logs target table for the same row:

- `total`: `24,930,369`
- `totalRDPSTaken`: `802,570`

Important identity from the sample:

- `24,930,369 + 802,570 = 25,732,939`

That exactly matches the raw `amount + absorbed` total from the event stream.

### What this tells us

There are two separate issues:

1. Our current event math is definitely wrong for UI parity.
   - We are overcounting by summing raw combat-log fields that WCLogs does not surface as the displayed source total.

2. Even after removing the obvious overcount, raw events still do not equal the Warcraft Logs table.
   - WCLogs is applying its own table-layer attribution/filtering semantics.
   - Therefore, event reconstruction is the wrong source if the product goal is “match the WCLogs UI.”

## Diagnosis

For damage-report parity, HK Logs should stop rebuilding player target damage from raw `events(DamageDone)` and instead use the Warcraft Logs `table(dataType: DamageDone)` resolver.

Reason:

- `events()` is raw combat-log data
- `table()` is the WCLogs-calculated report view
- the UI totals align with `table()` semantics, not our raw event reconstruction

This repo already has an existing pattern for `table()` usage in:

- `who_messed_up/api.py`
- `who_messed_up/services/phase_damage.py`

## Scope

### In scope

- Replace the shared target-damage aggregation path with WCLogs table-based aggregation.
- Ensure Imperator Averzian damage report rows line up with the WCLogs target view.
- Ensure totals, averages, filters, CSV output, and spec analysis all derive from the same corrected numbers.
- Preserve existing report configuration options:
  - selected targets
  - additional report merging
  - kill-only pulls
  - omit dead-player pulls

### Out of scope

- Rewriting unrelated report families that already use different data sources unless they are explicitly found to be wrong.
- Reworking the frontend table architecture.
- Building a dual-mode “raw vs WCLogs-matched” report variant.

## Proposed Change

### 1. Change the shared target-damage source of truth

Update `who_messed_up/services/target_damage.py` so that per-fight, per-target player totals come from Warcraft Logs `table(dataType: DamageDone)` instead of raw damage events.

Recommended approach:

1. keep the current fight selection, difficulty filtering, player-role/spec derivation, and pull bookkeeping
2. for each selected fight and each selected target:
   - call `table(dataType: DamageDone, fightIDs: [...])`
   - use a target filter expression that reproduces the WCLogs target view
3. consume the returned `entries`
4. aggregate those entry totals into the existing shared summary structure

### 2. Use table totals, not raw event sums

For parity with the visible WCLogs table:

- use the table entry `total` field as the primary source value
- do not recompute totals from `amount`, `absorbed`, `mitigated`, etc.

### 3. Preserve owner attribution behavior

If a table entry represents a pet/owned actor:

- resolve it back to the owning player the same way existing table-based code already does in `phase_damage.py`
- ensure player rows still represent players, not pets

### 4. Keep shared report consumers unchanged where possible

The target-damage summary object and the target-damage page model should remain stable enough that:

- report tables
- CSV export
- spec analysis modal
- target filters

can continue consuming the same summary shape without a frontend rewrite.

## Important Implementation Detail

During investigation, not every `table()` query shape produced the same result.

What matched the UI sample:

- target-filtered source table behavior equivalent to filtering the fight to `Imperator Averzian`

What did **not** match the UI sample during the same investigation:

- a more explicit `table(... sourceID, targetID, viewBy: Source)` variant

Because of that, implementation should not assume every table query shape is interchangeable. The first implementation pass should reproduce the exact WCLogs UI behavior using the query shape that matches the observed table totals.

## Proposed Backend Work

### API layer

Potentially extend `who_messed_up/api.py` table helper support if needed so the target-damage service can query the exact table shape required for parity.

Current helper:

- `fetch_table(...)`

Possible extension points:

- `view_by`
- `source_id`
- `target_id`
- additional explicit filter controls if the plain filter expression path is not sufficient

### Service layer

Update:

- `who_messed_up/services/target_damage.py`

Key changes:

- replace `_collect_target_damage()` event aggregation with table aggregation
- remove raw event-field summation from damage-report parity paths
- reuse owner-resolution logic for pet attribution
- keep per-fight participation and denominator logic for:
  - kill-only pulls
  - omit-dead-player pulls

### View-model layer

Minimal expected change.

The current shared target-damage view-model builders should remain valid if the summary contract is preserved.

## UI / Product Impact

The main expected product change is accuracy, not presentation.

Users should see:

- player totals that match the WCLogs target table
- averages based on those corrected totals
- spec-analysis rankings derived from corrected values

No major frontend behavior changes are required for this slice if the backend summary shape remains stable.

## Acceptance Criteria

### Primary accuracy criteria

For report `Xt8vWdnjJ26LCR4V`, fight `42`, target `Imperator Averzian`:

- Pilgrimm's Imperator damage in HK Logs must match Warcraft Logs' displayed target-table value of `24,930,369`

### Report-level criteria

For the Imperator report:

- each per-target player total should align with WCLogs target-table totals
- combined selected-target columns should be the sum of corrected target totals
- averages should be computed from corrected totals
- CSV export should reflect corrected totals
- spec analysis should reflect corrected totals

### Behavioral criteria

Existing report options must still work:

- multi-report merge
- kill-only pulls
- omit dead-player pulls
- selected target toggles

## Verification Plan

### Direct parity checks

Use live Warcraft Logs reports and compare:

1. HK Logs row total
2. WCLogs target-table total

Start with:

- Imperator Averzian
- multiple players
- at least one pet class/spec
- at least one multi-report merged case if available

### Technical validation

- compare current event-based result against new table-based result for the same sample logs
- confirm pet entries are still attributed to players
- confirm no player rows are lost unexpectedly

### Regression checks

- `python -m compileall who_messed_up app.py`
- `npm run build`

## Risks

### 1. Table query shape mismatch

If we switch to `table()` but use the wrong combination of arguments, we can still fail to match the UI.

Mitigation:

- validate the exact query shape against real WCLogs rows before generalizing

### 2. Pet/owner attribution differences

Table entries may represent owned actors differently from event streams.

Mitigation:

- explicitly test specs/classes with pet damage
- reuse existing table ownership resolution patterns

### 3. Hidden semantic differences across report families

Some current reports may rely on event-level flexibility for calculations that table data cannot reproduce exactly.

Mitigation:

- limit the first implementation slice to the target-damage family
- audit other damage reports separately before changing them

## Proposed First Slice

Implement the parity fix only for the shared target-damage family, starting with the current Imperator Averzian damage report.

Suggested order:

1. refactor the target-damage service to use WCLogs table data
2. validate the sample report against the WCLogs UI
3. validate additional Imperator logs
4. confirm spec analysis and CSV output remain consistent

## Tracking Checklist

- [x] Replace target-damage raw event aggregation with WCLogs table aggregation
- [x] Remove raw event-field summation from the parity path
- [x] Preserve player/pet ownership attribution
- [x] Validate Imperator sample report parity against WCLogs UI
- [x] Validate kill-only and omit-dead-player filters after the data-source change
- [ ] Validate CSV output against corrected table values
- [ ] Validate spec-analysis output against corrected table values
- [x] Add a short breadcrumb to the main refactor doc after implementation starts

## Recommendation

Proceed with a backend-only first slice that swaps the target-damage family from raw `events()` aggregation to WCLogs `table()` aggregation, using the exact query shape that reproduces the visible WCLogs target table.

No code changes have been made under this feature request yet.
