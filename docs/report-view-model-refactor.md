# Report View Model Refactor Plan

## Purpose

This refactor moves report-specific data shaping out of the React app and into the backend. The frontend should become a model renderer: it requests report definitions, submits report runs, polls for results, and renders the returned view model using modular presentational components.

The target architecture is:

- Backend owns data fetching, joins, aggregation, labels, summaries, table structure, row details, and report-specific rules.
- Frontend owns request state, loading/error state, and generic rendering only.
- UI code follows `Pages > Regions > Organisms > Molecules > Atoms`.

## Why We Need This

The current repo already has good backend service modules under `who_messed_up/services/`, but the UI still rebuilds report semantics after the API returns.

Current coupling hot spots:

- `frontend/src/App.jsx`
  - Reshapes API payloads into per-report row models.
  - Builds summary metrics.
  - Builds filter tags.
  - Implements report-specific sort behavior.
- `frontend/src/components/ResultsTable.jsx`
  - Switches on report mode.
  - Contains report-specific table markup.
  - Contains mobile/card variants per report.
  - Contains row detail/event rendering behavior.
- `frontend/src/hooks/useCsvExporter.js`
  - Rebuilds CSV schemas with report-specific branches.
- `frontend/src/config/constants.js`
  - Mixes UI copy, endpoint wiring, config schema, default params, and report behavior in one file.
- `app.py`
  - Already shapes summaries into API responses, but those responses are still closer to domain summaries than to a stable UI model.

The result is that a new report or a change to an existing report usually requires touching both backend response code and frontend branching logic.

## Refactor Goals

1. Frontend components are presentational and reusable.
2. Backend returns report view models that the frontend can render directly.
3. All report-specific rules live on the backend.
4. The API contract is explicit, versionable, and testable.
5. Existing analysis services remain the source of truth for domain calculations.

## Non-Goals

- Rewriting the core Warcraft Logs analysis algorithms as part of this effort.
- Replacing the in-process job queue as part of this effort.
- Doing a TypeScript migration in the same change set.
- Forcing every future screen into one fully generic "render anything" schema.

## Target Architecture

### Backend responsibilities

The backend should have three layers:

1. Domain analysis layer
   - Existing modules in `who_messed_up/services/`
   - Responsible for fetching data and calculating report summaries

2. View model builder layer
   - New modules that convert domain summaries into UI-facing models
   - Responsible for labels, table columns, summary cards, tags, row details, and default sort metadata

3. API layer
   - Thin route handlers
   - Responsible for request validation, job creation, and returning typed models

Suggested backend structure:

```text
who_messed_up/
  services/
    ... existing analysis modules ...
    report_registry.py
    view_models/
      common.py
      report_definitions.py
      report_page.py
      nexus_phase1.py
      phase_damage.py
      dimensius_add_damage.py
      dimensius_phase1.py
      dimensius_deaths.py
      dimensius_priority_damage.py
```

`who_messed_up/service.py` should remain a re-export layer, per the repo playbook.

### Frontend responsibilities

The frontend should have two kinds of code:

1. Page/controller code
   - Report selection state
   - Form state
   - Job polling
   - Error/loading state

2. Presentational code
   - Renders the returned model
   - Uses generic table, summary, tag, drawer, and detail components
   - No report-specific `if (mode === ...)` branches

Suggested frontend structure:

```text
frontend/src/
  pages/
    ReportsPage.jsx
  regions/
    ReportSelectionRegion.jsx
    ReportRequestRegion.jsx
    ReportResultsRegion.jsx
  organisms/
    ReportCatalog/
    ReportRequestForm/
    ReportHeader/
    ReportTable/
    ReportDetailPanel/
  molecules/
    SummaryMetric.jsx
    FilterTag.jsx
    TableHeaderCell.jsx
    TableRow.jsx
    EmptyState.jsx
  atoms/
    Badge.jsx
    Button.jsx
    Checkbox.jsx
    Select.jsx
    TextInput.jsx
    NumberCell.jsx
    Spinner.jsx
  hooks/
    useReportDefinitions.js
    useReportJob.js
    useTableSorting.js
```

`App.jsx` should become thin composition glue.

Current v2 layout after the first modular pass:

```text
frontend/src/
  pages/
    ReportsPage.jsx
  components/
    v2/
      regions/
        ReportsHeroRegion.jsx
        ReportsWorkspaceRegion.jsx
      organisms/
        FightSelectionGrid.jsx
        ReportCatalog.jsx
        ReportConfigurationPanel.jsx
        ReportRequestForm.jsx
        ReportResultsPanel.jsx
        ReportPageView.jsx
        ReportSummaryGrid.jsx
        ReportTable.jsx
      molecules/
        DifficultyToggle.jsx
        ReportFieldControl.jsx
        ReportRunCard.jsx
        ReportPageHeader.jsx
        ReportTags.jsx
        SummaryMetricCard.jsx
        EventGroupList.jsx
        SortableColumnHeader.jsx
        TableCellContent.jsx
      atoms/
        Button.jsx
        CheckboxField.jsx
        FieldHint.jsx
        PanelMessage.jsx
        SelectInput.jsx
        StatusPill.jsx
        SurfacePanel.jsx
        TextInput.jsx
  hooks/
    useReportDefinitions.js
    useReportFormState.js
    useReportJob.js
    useTableSorting.js
  utils/
    reportFormValues.js
    reportTablePresentation.js
```

The top-level `frontend/src/components/v2/*.jsx` files remain as thin re-export compatibility entry points while the new hierarchy settles.

The current v2 shell now uses the hero region as the primary entry surface: the legacy-style `HK Logs` hero owns difficulty selection and fight selection, while the workspace region starts at report browsing, configuration, and results.

Current legacy containment status:

- `frontend/src/App.jsx` boots the v2 reports shell by default.
- The v1 shell lives in `frontend/src/pages/legacy/LegacyReportsPage.jsx`.
- The legacy shell is lazy-loaded and only fetched when the user explicitly opens it.
- Legacy-only components, hooks, config, and helpers now live under `frontend/src/pages/legacy/`.
- Shared UI presentation tokens used by both shells live in `frontend/src/config/presentation.js`.

Current legacy subtree:

```text
frontend/src/pages/legacy/
  LegacyReportsPage.jsx
  config/
    constants.js
  hooks/
    useCsvExporter.js
    useTileRunner.js
  utils/
    configOptions.js
  components/
    ConfigDrawer.jsx
    ReportControls.jsx
    ResultHeader.jsx
    ResultsTable.jsx
    TileCatalog.jsx
    ui/
      LiquidHero.tsx
      RotatingQuote.tsx
```

## Standard Model Strategy

Do not standardize on a different top-level response shape for every report. Standardize on a common page envelope, then allow a small set of content variants inside it.

For the current reports, one shared table model should cover almost everything.

### 1. Report definition model

This replaces the frontend-owned tile registry as the source of truth for available reports and input schema.

```json
{
  "id": "dimensius-add-damage",
  "title": "Dimensius - Phase 1 Add Damage",
  "description": "Average player damage into Living Mass adds during Stage One.",
  "fightId": "dimensius-the-all-devouring",
  "fightName": "Dimensius, the All-Devouring",
  "difficulty": "mythic",
  "defaultFight": "Dimensius, the All-Devouring",
  "footnotes": ["Optional ignore first 6 adds that spawn instantly on pull."],
  "requestSchema": {
    "fields": [
      {
        "id": "additional_report",
        "kind": "multi_text",
        "label": "Additional report codes or URLs",
        "required": false
      }
    ]
  }
}
```

Current v2 browsing flow:

1. Select difficulty.
2. Select fight.
3. Browse reports available for that fight and difficulty.
4. Click a report to open its configuration modal.

Current Midnight v2 report coverage:

- `imperator-averzian-damage` is the first Midnight Season 1 report on the new contract.
- It uses backend-owned target toggles for `Imperator Averzian`, `Abyssal Voidshaper`, and `Voidbound Annihilator`.
- Backend report execution now also enforces the report definition difficulty when a log contains the same encounter across multiple difficulties.
- Shared target-damage reports can now aggregate a primary Warcraft Logs report plus `additional_reports`, with the backend merging pulls before it returns the page model.
- The Imperator report request schema now uses one required multi-text `report_codes` field; the backend treats the first entry as primary and the rest as additional reports.
- Target-damage tables now expose reusable `damageFilterConfig` metadata so the frontend can generically filter visible targets and totals/averages while recalculating the combined selected-damage columns from the model.

Recommended endpoint:

- `GET /api/v2/report-definitions`

### 2. Report page model

This is the result model the frontend renders.

```json
{
  "reportId": "dimensius-add-damage",
  "title": "Dimensius - Phase 1 Add Damage",
  "reportCode": "W4cZgnxQfR2AH1dT",
  "header": {
    "subtitle": "Report W4cZgnxQfR2AH1dT",
    "tags": [
      { "id": "fight", "label": "Fight", "value": "Dimensius, the All-Devouring" }
    ]
  },
  "summary": [
    { "id": "pulls", "label": "Pulls counted", "value": 42, "format": "integer" },
    { "id": "total_damage", "label": "Combined add damage", "value": 1234567, "format": "integer" }
  ],
  "content": {
    "variant": "table",
    "table": {
      "defaultSort": { "columnId": "average_damage", "direction": "desc" },
      "columns": [],
      "rows": []
    }
  },
  "footnotes": []
}
```

### 3. Shared table model

This is the key contract. The backend decides the columns and row cells. The frontend renders them generically.

```json
{
  "defaultSort": { "columnId": "role", "direction": "asc" },
  "columns": [
    { "id": "player", "label": "Player", "align": "left", "sortable": true, "cellKind": "player" },
    { "id": "role", "label": "Role", "align": "left", "sortable": true, "cellKind": "badge" },
    { "id": "pulls", "label": "Pulls", "align": "right", "sortable": true, "cellKind": "number", "format": "integer" }
  ],
  "rows": [
    {
      "id": "player-name",
      "cells": {
        "player": { "value": "PlayerName", "display": "PlayerName", "colorToken": "mage" },
        "role": { "value": "Ranged", "sortValue": 3, "display": "Ranged", "tone": "ranged" },
        "pulls": { "value": 15, "display": "15" }
      },
      "details": null
    }
  ],
  "emptyState": "No events matched the filters."
}
```

Shared table rules:

- Every cell must include a canonical `value`.
- `display` is optional. The frontend should render `value` by default and only use `display` when the backend needs rendered text that differs from the sort/filter value.
- `sortValue` is optional. The frontend sorts by `sortValue` when present, otherwise by `value`.
- `cellKind` decides what optional metadata a cell may include. For example:
  - `text` or `number` cells may only need `value`
  - `player` cells may include a `colorToken`
  - `badge` cells may include a `tone`
  - `link` cells may include an `href`
- Styling metadata should stay semantic, not presentational. The backend should send small enums or tokens such as class/role/tone identifiers, and the frontend should map those tokens to actual colors and badge styles.
- Do not send raw CSS classes or arbitrary inline styling in the API contract.

### 4. Row details model

Expandable event content should also be backend-shaped. Each table row represents a report entity, and that row may optionally carry a `details` object. For the current use cases, `details` should start as grouped event data tied to that entity.

```json
{
  "variant": "event_groups",
  "groups": [
    {
      "id": "fight-12-pull-3",
      "title": "Pull 3",
      "subtitle": "1:48 - Fight 12",
      "link": "https://www.warcraftlogs.com/reports/ABC#fight=12",
      "items": [
        {
          "id": "death-1",
          "label": "Death",
          "timestampLabel": "34.22s (1234567)",
          "description": "via Dark Energy"
        }
      ]
    }
  ]
}
```

Row details rules:

- `details` lives on the row model for that entity.
- `details` is optional; rows without expandable content should set it to `null`.
- The initial supported details variant is grouped events, which covers the current death/ghost/metric event use cases.
- Groups should usually be organized by pull, with optional fight metadata and an optional Warcraft Logs link.
- This model should be allowed to grow later with new detail variants instead of forcing all future detail content into one event-only structure.

## Why One Table Model Is Enough For Now

All current report screens are still player-centric tables with the same outer structure:

- report header
- filter tags
- summary metrics
- ranked rows
- optional row details

Even the reports with dynamic columns (`phase-damage`, `priority-damage`, `dimensius-phase1`) are still tables. That means we should avoid creating separate frontend table implementations per report unless the shared model starts to distort.

Recommended rule:

- Standardize on one table model first.
- Allow row detail variants.
- Add a second content variant only when a report truly stops being table-shaped.

## Recommended API Direction

Do this as a versioned addition during migration, then remove v1 once v2 is complete and proven.

Recommended new endpoints:

- `GET /api/v2/report-definitions`
- `POST /api/v2/reports/{report_id}/jobs`
- `GET /api/jobs/{job_id}`

Why:

- Keeps existing endpoints stable during migration.
- Lets the new frontend consume a single request/response contract.
- Makes rollback easy.

The existing analysis endpoints can keep powering regression tests until the new view-model API is proven. Backward compatibility is only a migration aid here, not a long-term requirement. Once all report flows are migrated and verified, the old v1 contract should be deleted rather than maintained indefinitely.

## Sorting

Sorting will stay client-side, but it should not remain report-specific frontend logic.

Chosen target:

- Backend supplies `defaultSort`.
- Backend supplies sortable columns.
- Frontend sorting is generic and operates on `columnId` plus `cell.sortValue` when present, otherwise `cell.value`.

This keeps the interaction in the UI without reintroducing report-specific logic.

## CSV Export

The current CSV exporter duplicates report schema knowledge in the frontend. That should go away, but the export itself can remain client-generated.

Chosen target:

- Generate CSV generically from the shared table model.
- Do not add a backend CSV endpoint unless future requirements make the shared client-side export insufficient.

The important part is that the frontend should not branch on report type to export.

## Migration Map

Map current code to target ownership:

- `frontend/src/config/constants.js`
  - Move report definitions and input schema to backend report registry.
- `frontend/src/hooks/useTileRunner.js`
  - Replace with `useReportJob` that submits a definition-driven request and polls for a view model.
- `frontend/src/App.jsx`
  - Remove row shaping, summary construction, filter-tag construction, and report-specific sorting.
- `frontend/src/components/ResultsTable.jsx`
  - Replace with a generic `ReportTable` organism plus smaller presentational pieces.
- `frontend/src/hooks/useCsvExporter.js`
  - Replace with generic export from table model.
- `app.py`
  - Move response/view-model classes out of the route file.
  - Keep route handlers thin.

## Incremental Delivery Plan

### Phase 0 - Freeze the contract

1. Inventory every current report and capture example JSON responses.
2. Define `ReportDefinitionModel`, `ReportPageModel`, `TableModel`, and `RowDetailsModel`.
3. Decide whether any current report does not fit the shared table model.
4. Add view-model fixtures for at least one simple report and one event-detail report.

Exit criteria:

- The team agrees on the new contract before touching the renderer.

### Phase 1 - Backend foundation

1. Create a backend report registry.
2. Move API response models out of `app.py`.
3. Add view-model builder modules beside the existing analysis services.
4. Introduce `/api/v2/report-definitions`.
5. Introduce `/api/v2/reports/{report_id}/jobs`.

Exit criteria:

- Backend can return the new definition model and at least one full page model.

### Phase 2 - Frontend foundation

1. Create `pages/`, `regions/`, `organisms/`, `molecules/`, and `atoms/`.
2. Build a thin `ReportsPage`.
3. Build generic catalog, request form, report header, summary list, tag list, table, and row-detail organisms.
4. Replace `TILES` usage with fetched report definitions.
5. Scope the initial renderer to responsive table output only; do not carry forward mobile cards mode in the first migration.

Exit criteria:

- Frontend can render a report page model with no report-specific branches.

### Phase 3 - Pilot migration

Migrate reports in increasing complexity.

Recommended order:

1. `dimensius-add-damage`
2. `dimensius-deaths`
3. `dimensius-priority-damage`
4. `nexus-phase-damage`
5. `dimensius-phase1`
6. `nexus-phase1`

Why this order:

- Start with a simple fixed-column report.
- Validate row details next.
- Validate dynamic columns after that.
- Leave the combined Nexus report for last because it currently drives the most frontend logic.

Exit criteria:

- First migrated reports no longer require frontend result shaping.

### Phase 4 - Remove legacy branches

1. Delete mode-based branching from `App.jsx`.
2. Delete report-specific table branches from `ResultsTable.jsx`.
3. Delete report-specific CSV branches.
4. Remove duplicated endpoint metadata from the frontend.
5. Keep backward compatibility only where still needed for regression comparison.

Exit criteria:

- The frontend only knows how to render the model, not how to construct it.

### Phase 5 - Retire v1

1. Remove legacy v1 frontend wiring and endpoint references.
2. Remove superseded v1 response models and route handlers.
3. Update regression coverage to point at v2 contracts.
4. Update README and developer docs to describe v2 as the only supported contract.

Exit criteria:

- The repo no longer maintains the old frontend/backend contract.
- There is one supported API contract for report rendering.

## Acceptance Criteria

The refactor is complete when all of the following are true:

- No report-specific row shaping exists in the frontend.
- No report-specific summary/tag construction exists in the frontend.
- No report-specific table markup switching exists in presentational components.
- Report definitions come from the backend.
- A report can add or remove columns without frontend code changes.
- CSV export does not branch on report type.
- `App.jsx` is orchestration glue, not a report transformer.
- `app.py` is route wiring, not the home of all API/view-model code.
- v1 report-rendering endpoints and legacy UI wiring are removed after v2 parity is proven.
- The first migrated report is `dimensius-add-damage`, establishing the base pattern for the damage-report family.

## Verification Strategy

Backend:

- Keep existing regression snapshots for the current analysis endpoints.
- Add new regression snapshots for `/api/v2/report-definitions`.
- Add new regression snapshots for each migrated report page model.
- Add focused tests for each view-model builder.

Frontend:

- Run `npm run build` after each migration slice.
- Add component tests for:
  - report definition form rendering
  - shared report table rendering
  - row detail rendering
  - generic sort behavior
- Add one fixture-driven test per migrated report family.

Manual:

- Compare old and new screens against the same regression reports before deleting legacy code.
- Confirm responsive table behavior still works on smaller viewports from the shared model.

## Guardrails For Implementation

- Keep the existing backend summary services intact; add adapters before replacing anything.
- Do not do the backend contract rewrite and the frontend atomic re-org in one unreviewable change.
- Land the report registry and view-model builders before deleting current UI logic.
- Migrate one report family at a time and prove the pattern before continuing.
- Preserve existing regression coverage and add view-model coverage before removing old paths.

## Decisions Made

The following implementation choices are now fixed for this refactor:

1. Sorting stays client-side, using generic sortable cell values from the backend model.
2. We use one shared table model rather than a separate specialized matrix wrapper for phase reports.
3. CSV export stays client-generated from the shared table model.
4. The new contract ships under `/api/v2/`.
5. v1 is a temporary migration surface only and should be removed after v2 is working and verified.
6. Every table cell has a canonical `value`; `display` is optional and only used when rendered text must differ from that value.
7. Links, colors, and badges are represented by semantic enums/tokens in the model, not raw presentation classes.
8. `sortValue` is optional on cells and is used when semantic display values need a different generic sort order, such as role badges.
9. Expandable report events live on the row model as an optional `details` object, starting with grouped event data.
10. The initial v2 frontend scope is responsive table rendering only; mobile cards mode can be revisited later.
11. The first migration slice is `dimensius-add-damage`.
12. Damage-report pages may emit an optional `specAnalysis` block for modal visualizations; the first consumer is `imperator-averzian-damage`, using average damage per player per counted pull across boss, priority, and pad buckets.
