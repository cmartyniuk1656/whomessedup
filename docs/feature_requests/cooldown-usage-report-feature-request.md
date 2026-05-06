# Cooldown Usage Report Feature Request

## Purpose

Add a reusable cooldown-usage report family that checks player cooldown casts against an NSRT cooldown-reminders plan.

Initial implementation targets:

- Report name: `Cooldown Usage Report`
- Bosses: all Midnight Season 1 bosses listed in the app
- Difficulty: `Mythic`
- Report ids: one per boss, using the pattern `<fight-id>-cooldowns`

This should become a standard report type for future bosses, with boss-specific metadata limited to encounter identity, supported difficulties, and any phase-timing rules needed to align reminder timestamps to Warcraft Logs pulls.

## Problem Statement

Raid cooldown plans are usually authored outside HK Logs, then reviewed manually after pulls. Users need a report that can answer:

- Was each assigned cooldown cast by the assigned player?
- Was it cast close enough to the assigned time?
- Was the assignment invalid because the player was dead?
- Did a healer death make later cooldown deviations intentionally messy enough to ignore?
- Which players consistently follow assignments across all pulls, and which individual pull events need review?

The report should let users paste the plan directly into the app, run it against the selected Warcraft Logs pulls, and inspect both aggregate performance and per-pull outcomes.

## Input Reminder Format

Users paste an NSRT cooldown-reminders string into a textarea.

Example shape:

```text
EncounterID:3180;Name:Vanguard - Mythic;Difficulty:Mythic
time:11;ph:1;bossSpell:1255738;tag:Malandru;spellid:31884;
time:16;ph:1;tag:Owneege;spellid:97462;
time:18;ph:1;bossSpell:1246497;tag:Solaraeda;spellid:196718;
```

Required fields:

- Header `EncounterID`
- Header `Difficulty`
- Assignment `time`
- Assignment `ph`
- Assignment `tag`
- Assignment `spellid`

Optional fields to parse and preserve:

- Header `Name`
- Assignment `bossSpell`
- Assignment `glowunit`
- Unknown future keys, preserved only if useful for debugging

Confirmed scope:

- Score every cooldown assignment in the note, not only healer cooldowns.
- The first expected real-world usage is healer cooldowns only, but the matcher should not assume that.
- Do not include players in the report unless they appear in at least one NSRT assignment.
- If an assigned player is in the note but was not present in a specific pull, ignore that player's assignments for that pull.

## Reminder Validation

The backend should validate the pasted reminder against the selected report definition.

For the first report family:

- `Difficulty` must normalize to `Mythic`.
- The selected app fight must match the report definition fight.
- When Warcraft Logs fight encounter metadata is available, the selected pull's encounter id must match the NSRT `EncounterID`.
- The report definition difficulty must be `mythic`.

Validation failures should stop the job early with a clear user-facing error, for example:

- `This reminder is for EncounterID 3190, but selected fight is EncounterID 3180.`
- `This reminder is for Heroic, but this report only supports Mythic.`
- `No cooldown assignments were found in the pasted reminder.`

## Phase Timing Requirement

NSRT assignment `time` is phase-relative when `ph` is present.

Rules:

- `ph:1` means seconds from the start of phase 1.
- `ph:2` means seconds from the start of phase 2.
- Additional phases follow the same pattern.
- The report must convert each assignment to an absolute timestamp per pull before matching casts.

Implementation note:

- Add a reusable phase-timing resolver under `who_messed_up/services/`.
- Resolve each pull's phase start timestamps from Warcraft Logs data or encounter phase transitions.
- If a pasted assignment references a phase that cannot be resolved for a pull, mark that assignment as ignored for that pull with reason `missing_phase`.
- For single-phase encounters, `ph:1` can map to fight start.

This phase resolver is the main implementation risk and should be proven on real multi-phase cooldown notes before broadening phase-specific behavior.

## Matching Rules

The core matcher should compare each eligible assignment against player cast events.

Inputs per assignment:

- assigned player from `tag`
- assigned cooldown from `spellid`
- phase-relative assignment time from `time` and `ph`
- optional boss mechanic from `bossSpell`

Configurable tolerance:

- UI control: slider
- Range: `0` to `15` seconds
- Default: `7.5` seconds
- Suggested step: `0.5` seconds

For each pull, each assignment produces one of these statuses:

- `correct`: assigned player cast the assigned `spellid` within the tolerance window.
- `incorrect`: assigned player cast the assigned `spellid` in the pull, but outside the tolerance window.
- `missed`: assigned player did not cast the assigned `spellid` in the tolerance window and had no out-of-window same-spell cast to attribute to that assignment.
- `ignored_dead`: assigned player was dead at the scheduled assignment time.
- `ignored_after_healer_death`: assignment occurred after the optional healer-death cutoff.
- `ignored_after_death_count`: assignment occurred after the optional global death-count cutoff.
- `ignored_missing_phase`: assignment phase could not be resolved for the pull.
- `ignored_not_in_pull`: assigned player was not present in that pull.
- `ignored_after_pull_end`: assignment was scheduled after the pull had already ended.

When multiple assignments use the same player and spell in one pull:

- Match casts to assignments one-to-one.
- Prefer the nearest unmatched cast inside the tolerance window.
- If no in-window cast exists, use the nearest unmatched same-spell cast in the pull to report an `incorrect` delta.
- If no same-spell cast exists in the pull, report the assignment as `missed`.
- Do not let one cast satisfy multiple assignments.

For successful and incorrect matches, store:

- scheduled timestamp
- actual cast timestamp
- delta in seconds
- pull id and pull index
- report code
- ability id and label
- optional boss spell id and label

## Death Filtering

Assignments should not penalize a player who was already dead at the scheduled assignment time.

Recommended behavior:

- Build per-pull player life state from Warcraft Logs death and resurrection events where available.
- Treat an assignment as `ignored_dead` when the assigned player is dead at the scheduled timestamp.
- Battle resurrection should make the assigned player eligible again later in the pull.
- Give credit if the assigned player casts correctly inside the tolerance window, even if they die around the scheduled assignment time.
- If no in-window cast exists and the player was dead during the scheduled usage point, ignore that assignment instead of marking it missed or incorrect.
- If resurrection state cannot be derived reliably in the first slice, document the fallback and prefer not to over-penalize ambiguous cases.

The implementation can reuse the existing death-event fetching patterns from `who_messed_up/services/common.py` and `who_messed_up/services/lightblinded_vanguard_dispels.py`, but the helper should stay generic enough for future cooldown reports.

## Global Death Count Cutoff Option

Add an option:

- Label: `Ignore events after deaths`
- Kind: number
- Default: blank / no limit

When set:

- For each pull, find the timestamp when the Nth player death occurs.
- Ignore cooldown assignments scheduled after that timestamp.
- Mark those assignments as `ignored_after_death_count`.
- If the assigned player was already dead at the assignment time, `ignored_dead` should remain the more specific status.

When both global death count and healer-death cutoff options are enabled:

- Apply the earliest applicable cutoff per pull.
- Preserve the more specific ignore reason in details.

## Healer Death Cutoff Option

Add an option:

- Label: `Ignore events after a healer dies`
- Kind: checkbox
- Default: `false`

When enabled:

- For each pull, find the first healer death timestamp.
- Ignore cooldown assignments scheduled after that timestamp.
- If the assigned player is the healer who died, `ignored_dead` should remain the more specific status.
- If a different healer died first, mark later assignments as `ignored_after_healer_death`.

Reason:

After a healer dies, remaining healers may intentionally move cooldowns to cover gaps. The report should support excluding those later assignments from compliance scoring.

## Aggregate And Pull Views

The results page needs a view selector:

- `Aggregate`
- One option per counted pull, for example `Pull 1`, `Pull 2`, `Pull 3`

Aggregate view:

- Condenses all eligible pulls.
- Shows one row per player.
- Uses all non-ignored assignments as the denominator.

Individual pull view:

- Shows the same player rows, scoped to one pull.
- Per-row details should only show events from that selected pull.

Current frontend note:

- The v2 table model currently supports damage-specific filters, but not a generic aggregate/pull view selector.
- Add a generic report table view-control model rather than hard-coding cooldown behavior into `ReportPageView.jsx`.

## Table Requirements

Recommended aggregate columns:

- Player
- Role
- Pulls
- Assignments
- Correct
- Incorrect
- Missed
- Ignored
- On-time %
- Average delta

Scoring:

- `eligible_assignments = correct + incorrect + missed`
- `on_time_rate = correct / eligible_assignments`
- Ignored assignments are excluded from the denominator.
- Average delta should be calculated from matched casts only.

Sorting:

- Default sort should put the lowest `On-time %` first, then highest missed count, then player name.
- Role sorting should follow existing role priority patterns.

Summary metrics:

- Pulls counted
- Assignments checked
- On-time casts
- Missed cooldowns
- Ignored assignments
- Raid on-time %

## Row Details

Clicking a player row should show per-pull assignment outcomes.

Each detail group should represent one pull:

- Pull number
- Warcraft Logs pull link
- Pull duration
- Optional healer-death cutoff note

Each detail item should represent one assignment:

- Status: correct, incorrect, missed, ignored
- Assignment time label, phase, and phase-relative time
- Cooldown ability label and spell id
- Assigned player
- Actual cast time and delta when available
- Boss spell label or id when available
- Ignore reason when ignored

Suggested tones:

- `correct`: positive
- `incorrect`: warning
- `missed`: danger
- `ignored_*`: neutral

## Backend Design

Add a shared service module:

```text
who_messed_up/services/cooldown_usage.py
```

Responsibilities:

- Parse NSRT reminder text into a typed plan.
- Validate encounter id and difficulty against the report definition.
- Select Warcraft Logs fights by fight name and difficulty.
- Resolve phase start timestamps per pull.
- Fetch cast events for all referenced cooldown spell ids.
- Fetch player details for role, class, spec, and healer detection.
- Fetch death/life-state events for assigned players and healer-death cutoffs.
- Match assignments to casts.
- Aggregate player summaries.
- Preserve per-pull details for row expansion.

Add thin boss/report wrappers only where needed:

```text
who_messed_up/services/cooldown_usage.py
```

Responsibilities:

- Define fight/report constants.
- Call the shared cooldown-usage service with the selected fight name and difficulty `mythic`.
- Keep future per-boss entry points thin.

Re-export public entry points through:

```text
who_messed_up/service.py
```

## View-Model Design

Add a report page builder:

```text
who_messed_up/services/view_models/lightblinded_vanguard_cooldowns.py
```

Responsibilities:

- Convert the shared cooldown summary into the existing v2 `ReportPageModel`.
- Use a table content variant.
- Populate row details with grouped event data.
- Add generic aggregate/pull view metadata if the shared page model is extended.

Potential shared model additions:

```json
{
  "content": {
    "table": {
      "viewControl": {
        "id": "pull_view",
        "label": "View",
        "defaultValue": "aggregate",
        "options": [
          { "value": "aggregate", "label": "Aggregate" },
          { "value": "pull:12", "label": "Pull 1" }
        ]
      }
    }
  }
}
```

Rows can either:

- include all rows with per-view cell values, letting the frontend switch views generically, or
- include row metadata that allows the frontend to filter by selected view.

Recommendation:

- Keep scoring and aggregation backend-owned.
- Let the frontend only select which backend-provided view to display.

## Report Registry Work

Add a new v2 report definition in `who_messed_up/services/report_registry.py`.

Suggested fields:

- `report_codes`: existing multi-text field
- `nsrt_reminders`: new textarea field
- `tolerance_seconds`: new slider/range field, default `7.5`
- `ignore_after_deaths`: number field, default blank
- `ignore_after_healer_death`: checkbox, default `false`
- `fresh_run`: checkbox, default `false`

Current schema gap:

- `RequestFieldKind` does not include `textarea` or `range`.
- Add those field kinds to `who_messed_up/services/view_models/report_definitions.py`.
- Add matching controls to `frontend/src/components/v2/molecules/ReportFieldControl.jsx`.

Suggested report definition:

- `id`: `<fight-id>-cooldowns`
- `title`: `Cooldown Usage Report`
- `description`: `Check assigned NSRT cooldown reminders against Warcraft Logs casts.`
- `fightId`: selected app fight id
- `fightName`: selected app fight name
- `difficulty`: `mythic`

## API And Job Work

Add a new job type:

```python
JOB_V2_COOLDOWN_USAGE = "v2_report_cooldown_usage"
```

Add an app handler that:

1. Builds the payload from report registry values.
2. Runs the shared cooldown-usage summary.
3. Builds the v2 report page model.
4. Returns the model with aliases.

The cache key should include:

- normalized report codes
- reminder text or a stable hash of it
- tolerance seconds
- ignore-after-deaths value
- ignore-after-healer-death option
- fight and difficulty

## Frontend Work

Request form:

- Render large pasted reminder text with a textarea.
- Render tolerance with a slider that also shows the selected seconds value.
- Preserve existing multi-report-code and fresh-run behavior.

Results:

- Add a generic aggregate/pull selector for report pages that provide view-control metadata.
- Keep `ReportPageView.jsx` orchestration thin.
- Keep cooldown-specific copy and metrics in the backend page model.
- Reuse `ReportTable`, `EventGroupList`, `ReportSummaryGrid`, and `ReportPageHeader`.

## Parser Notes

Parser should be permissive about line endings and whitespace:

- Accept CRLF and LF.
- Ignore blank lines.
- Ignore trailing semicolons.
- Normalize keys case-insensitively if NSRT exports vary.
- Report line-level parse errors with line numbers.

Typed parser output should keep numeric fields numeric:

```python
CooldownReminderAssignment(
    line_number=2,
    time_seconds=11.0,
    phase=1,
    player="Malandru",
    spell_id=31884,
    boss_spell_id=1255738,
)
```

## Open Product Decisions

These do not block drafting, but should be confirmed before implementation:

- Should `bossSpell` be shown as a grouping/label in details even when it is not needed for matching?
- Should the aggregate table include ignored counts by reason as separate columns, or keep one `Ignored` column with detail breakdowns?

## Testing And Verification

Backend:

- Unit-test NSRT parser with valid input, blank lines, unknown keys, invalid header, invalid assignment lines, and missing required fields.
- Unit-test assignment matching with exact casts, early casts, late casts, missed casts, duplicate same-spell assignments, and duplicate casts.
- Unit-test participant filtering so players outside the note are excluded and assigned players absent from a pull are ignored for that pull.
- Unit-test dead-player filtering, including battle resurrection eligibility later in the same pull.
- Unit-test global death-count cutoff behavior.
- Unit-test healer-death cutoff behavior.
- Add a v2 report page model snapshot for cooldown usage.

Frontend:

- Add tests or focused coverage for textarea and slider request fields if the test setup supports it.
- Add a small test for generic aggregate/pull view switching if introduced.
- Run `npm run build`.

Regression:

- Add the new cooldown usage report to `scripts/capture_regressions.py` once stable sample reports and reminder fixtures are available.

## Acceptance Criteria

- Users can select any Mythic Midnight Season 1 boss and choose a cooldown-usage report.
- Users can paste an NSRT reminder string into a textarea.
- The backend rejects reminders for the wrong encounter id or difficulty.
- Users can set matching tolerance from `0` to `15` seconds, defaulting to `7.5`.
- The report scores assigned cooldowns across all selected pulls.
- The report includes only players who appear in the pasted NSRT reminder.
- Assignments for players who are not present in a specific pull are ignored for that pull.
- Assignments where the player was dead are excluded from scoring.
- Battle-rezzed players become eligible again for later assignments in the same pull.
- Optional global death-count cutoff excludes later assignments after the configured death count in each pull.
- Optional healer-death cutoff excludes later assignments after the first healer death in each pull.
- Aggregate view reports per-player on-time rate and supporting counts.
- Pull view reports per-player data for one selected pull.
- Row expansion shows correct, incorrect, missed, and ignored assignment details by pull.
- The first implementation works for all Mythic Midnight Season 1 bosses exposed in the app.
