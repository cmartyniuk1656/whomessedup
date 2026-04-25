# Spec Analysis Modal for Damage Reports

## Goal

Add a reusable `Spec Analysis` experience for v2 damage reports.

When a user clicks `Spec Analysis` from the report header, the app should open a modal that visualizes how each specialization performed across three damage buckets:

- Boss Damage
- Priority Damage
- Pad Damage

The first implementation target is the Mythic Imperator Averzian damage report.

## Initial Encounter Mapping

For Imperator Averzian, classify targets as:

- `Imperator Averzian` -> `boss`
- `Abyssal Voidshaper` -> `priority_add`
- `Voidbound Annihilator` -> `pad_add`
- `Abyssal Malus` -> `pad_add`
- `Voidmaw` -> `pad_add`

This classification should live in backend-owned encounter target metadata so future damage reports can reuse the same analysis path.

## Current State

The repo already has most of the raw inputs needed for this feature:

- Target-damage reports are backed by shared services in `who_messed_up/services/target_damage.py`.
- Report pages are built from backend-owned view models in `who_messed_up/services/view_models/target_damage.py`.
- The target-damage summary already derives:
  - player class
  - player role
  - player spec
  - per-target total damage
  - per-target average damage per pull
- The frontend already has:
  - report header actions
  - modal infrastructure
  - reusable filter controls
  - a generic v2 report page shell

## Warcraft Logs Data Notes

No new upstream API surface appears to be required for player specialization.

The current backend already pulls `playerDetails(fightIDs: ...)` from Warcraft Logs in `who_messed_up/api.py`, and `_infer_player_roles()` in `who_messed_up/services/common.py` extracts spec data from the returned player entries.

Current spec derivation path:

1. Read `entry.specs[].spec` when present.
2. Fall back to parsing the player `icon` field when `specs` is absent.

This is consistent with Warcraft Logs' `Report.playerDetails` schema and their documented player `spec` field in event/filter docs.

## Product Requirements

### Entry point

- Add a `Spec Analysis` button to the report header beside the existing report actions.
- Show the button only when the backend page model includes spec-analysis data.

### Modal behavior

- Clicking the button opens a modal.
- The modal should not replace the table.
- Closing the modal returns the user to the same report state.

### Visualization

- Use a grouped vertical bar chart.
- Each spec gets one group.
- Each group contains three bars:
  - Boss
  - Priority
  - Pad
- Bars should compare specs relative to one another within the same metric.

### Sorting

- Provide basic sorting controls in the modal.
- Initial supported sorts:
  - Boss Damage descending
  - Priority Damage descending
  - Pad Damage descending
  - Default order

### Scope

- This feature should be reusable across future damage reports.
- The frontend should remain presentational.
- Report-specific aggregation and classification rules should stay in the backend.

## Recommended Backend Design

### 1. Extend encounter target metadata

Extend `EncounterTargetConfig` with a reusable classification field.

Suggested enum:

- `boss`
- `priority_add`
- `pad_add`

Important: this should support many targets mapping into the same bucket. Future encounters may have multiple priority or pad enemies.

### 2. Add a reusable spec-analysis domain summary

Add a shared backend summary path for target-damage reports that aggregates player rows into per-spec buckets.

Recommended aggregation input:

- the existing per-player target totals already calculated by `target_damage.py`
- player class
- player spec
- target classification metadata

Recommended output per spec:

- class name
- spec name
- player count
- boss damage
- priority damage
- pad damage
- optional per-pull averages for each of the above

### 3. Keep the frontend out of report math

The frontend should not derive spec group totals from table columns.

Reason:

- target classification is domain logic
- future damage reports may not expose a 1:1 table-to-chart mapping
- the current refactor direction is backend-owned report semantics

The frontend can still own lightweight UI state such as:

- modal open/close
- sort selection
- chart hover state

## Recommended View-Model Contract

Add an optional `specAnalysis` block to the report page model.

Suggested shape:

```json
{
  "specAnalysis": {
    "buttonLabel": "Spec Analysis",
    "title": "Spec Analysis",
    "subtitle": "Compare specialization output across boss, priority, and pad targets.",
    "defaultSort": "boss",
    "sortOptions": [
      { "id": "default", "label": "Default order" },
      { "id": "boss", "label": "Boss Damage" },
      { "id": "priority", "label": "Priority Damage" },
      { "id": "pad", "label": "Pad Damage" }
    ],
    "metrics": [
      { "id": "boss", "label": "Boss Damage" },
      { "id": "priority", "label": "Priority Damage" },
      { "id": "pad", "label": "Pad Damage" }
    ],
    "series": [
      {
        "id": "rogue-outlaw",
        "className": "Rogue",
        "specName": "Outlaw",
        "colorToken": "class-rogue",
        "playerCount": 2,
        "values": {
          "boss": 123456789,
          "priority": 45678901,
          "pad": 9876543
        }
      }
    ]
  }
}
```

Notes:

- `series` should contain raw values, not formatted strings.
- The frontend can sort by these raw values.
- The frontend can normalize bar heights for display from the raw values.
- If we want stricter frontend/presentation separation later, we can also add precomputed `relativeValue` fields.

## Visualization Recommendation

Do not add a charting dependency for the first pass.

Reason:

- the frontend currently has no chart library
- the requested chart is simple
- grouped bars can be built cleanly with existing React + Tailwind primitives
- avoiding a new dependency keeps the bundle and maintenance surface smaller

Recommended first-pass rendering:

- custom grouped bar chart
- fixed metric colors:
  - Boss -> one color
  - Priority -> one color
  - Pad -> one color
- spec label under each group
- actual values available in labels or hover text

## Aggregation Basis

For the chart, raw totals by spec are misleading if one spec is represented by more players or more pulls.

Confirmed metric basis:

- average damage per player per counted pull, aggregated by spec

Why:

- better apples-to-apples comparison across specs
- does not over-reward specs with more player slots in the raid
- aligns better with the user question of "how well each spec performed"

If needed, we can still carry both:

- `total`
- `averagePerPull`

and choose which one the chart renders.

## Frontend Work

### Header

- add `Spec Analysis` action to `ReportPageHeader.jsx`
- render only when `page.specAnalysis` exists

### Modal

- add a dedicated `SpecAnalysisModal` organism
- reuse the existing modal frame

### Chart

- add a reusable grouped-bar visualization component under `frontend/src/components/v2`
- keep it generic to any report page that provides the `specAnalysis` contract

### Sorting UI

- add a small select or segmented control inside the modal
- default sort comes from the backend model

## Backend Work

### Shared domain layer

- extend encounter target config with classification metadata
- add reusable per-spec aggregation for target-damage summaries

### View-model layer

- add shared spec-analysis view-model models under `who_messed_up/services/view_models/common.py`
- teach target-damage page builders to emit `specAnalysis` when configured

### Imperator report

- mark Imperator targets with:
  - boss
  - priority_add
  - pad_add
- enable spec analysis on the Imperator damage page as the first consumer

## Tracking Checklist

- [x] Extend target metadata with reusable damage-bucket classification
- [x] Build shared per-spec aggregation service for target-damage reports
- [x] Add spec-analysis models to the v2 report view-model contract
- [x] Emit spec-analysis payload for Imperator Averzian damage
- [x] Add `Spec Analysis` report-header action
- [x] Build modal shell and sorting controls
- [x] Build grouped bar visualization
- [ ] Verify mixed-class/spec logs produce stable output
- [ ] Verify tanks/healers/pets are handled correctly
- [x] Add documentation breadcrumb to the main refactor doc after implementation starts

## Open Questions Before Implementation

### 1. Spec population

Assumption: include any real player spec that appears in the report, including tank/healer specs if they are present.

If the intended chart should only show DPS specs, we should lock that down before implementation.

### 2. Labels in the chart

Assumption: the x-axis label is the spec name, and class color is enough visual identity for the first pass.

If we want spec icons in the chart, that should be treated as a follow-up enhancement.

## Proposed First Slice

Implement the full path for `imperator-averzian-damage` only:

1. classify targets
2. aggregate spec metrics on the backend
3. emit the new view-model block
4. render the modal + grouped bar chart
5. add sorting controls

If that lands cleanly, lift the shared pieces into the generic damage-report path for future encounters.
