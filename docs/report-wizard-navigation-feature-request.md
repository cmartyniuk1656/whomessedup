# Report Wizard Navigation Feature Request

## Purpose

Create a guided v2 report workflow that moves users through report setup one clear step at a time:

1. select difficulty and boss
2. select a report
3. configure the report
4. run the report
5. view results

The current v2 page exposes most of this functionality, but the flow is still presented as a hero plus workspace with report cards, configuration modal, run status, and results all competing for space. A wizard flow should make the path more deliberate, easier to follow, and easier to navigate backward.

## Problem Statement

Users need a clearer sense of where they are in the report-running process and what action comes next.

Current friction:

- Difficulty and boss selection live in the hero area, while report selection and configuration live below it.
- Selecting a report opens configuration as a modal instead of feeling like the next step in the process.
- Running state and completed results appear in the same workspace area instead of being explicit steps.
- Users can change earlier choices, but there is no breadcrumb navigation that shows the current path or allows quick return to a prior step.

## Desired User Flow

### Step 1 - Boss Select

The user selects:

- difficulty
- boss

After a boss is selected, the boss selection view animates out and the report selection view animates in.

### Step 2 - Report Select

The user selects one report available for the selected boss and difficulty.

After a report is selected, the report selection view animates out and the report configuration view animates in.

### Step 3 - Report Configuration

The user configures the selected report using the report definition schema.

When the user clicks **Run report**, the configuration view animates out and the running feedback view animates in.

### Step 4 - Running Feedback

The UI clearly communicates that the report has been queued or is running.

Running feedback should include:

- selected report name
- selected boss and difficulty
- queued/running status
- queue position when available
- job id when available
- error state if the job fails

Once the job completes successfully, the running view animates out and the report results animate in.

### Step 5 - Results

The completed report table appears as the final wizard step.

Users should still be able to navigate back through breadcrumbs to change:

- boss/difficulty
- report
- configuration

Changing an earlier step should clear or invalidate later state as appropriate.

## Breadcrumb Navigation

Add breadcrumb navigation for the wizard steps.

Suggested labels:

- Boss
- Report
- Configure
- Running
- Results

Rules:

- Breadcrumbs should be visible throughout the wizard.
- Completed prior steps are clickable.
- The current step is visually active.
- Future steps are disabled until reachable.
- If a completed report exists, `Results` is clickable.
- If a job is currently running, `Running` is clickable.
- Navigating back to `Boss` or `Report` should not leave stale results visible as if they still apply.

## Animation Requirements

Each major step transition should animate:

- outgoing step fades/slides out
- incoming step fades/slides in
- motion should be quick and restrained

Suggested interaction style:

- use CSS transitions or existing Tailwind animation utilities
- prefer opacity plus small horizontal/vertical movement
- respect `prefers-reduced-motion`
- avoid large page jumps

The animation should make the flow feel guided without slowing down repeated report runs.

## State Model

Suggested wizard steps:

```js
const WIZARD_STEPS = {
  BOSS: "boss",
  REPORT: "report",
  CONFIGURE: "configure",
  RUNNING: "running",
  RESULTS: "results",
};
```

State should derive from existing report selection and job state where possible:

- selected difficulty
- selected boss/fight id
- selected report id
- form values
- pending job
- job error
- completed page model

The wizard should have an explicit active step so users can navigate back without losing valid prior state.

## Reset / Invalid State Rules

Changing difficulty should clear:

- selected boss
- selected report
- report form values for the old report
- pending job
- completed result

Changing boss should clear:

- selected report
- report form values for the old report
- pending job
- completed result

Changing report should clear:

- pending job
- completed result
- old report form values

Changing configuration values after a report has completed should either:

- clear the completed result immediately, or
- mark the result as stale

Recommendation for first slice:

- clear completed result when report, boss, or difficulty changes
- do not clear completed result on every configuration field change until the user runs again, unless stale-result UX becomes confusing

## Proposed Frontend Work

### Page orchestration

Update:

- `frontend/src/pages/ReportsPage.jsx`

Responsibilities:

- own `activeWizardStep`
- advance steps after valid selections
- navigate via breadcrumbs
- clear result/job state when upstream selections change
- submit reports and move to running/results steps

### New components

Suggested additions:

```text
frontend/src/components/v2/
  molecules/
    WizardBreadcrumbs.jsx
  organisms/
    ReportWizardStepFrame.jsx
    ReportRunningPanel.jsx
```

Potential responsibilities:

- `WizardBreadcrumbs`: step labels, active state, clickable prior steps
- `ReportWizardStepFrame`: animated wrapper for step transitions
- `ReportRunningPanel`: queued/running/error feedback

### Existing components to reuse

Reuse instead of rebuilding:

- `DifficultyToggle`
- `FightSelectionGrid`
- `ReportCatalog`
- `ReportRequestForm`
- `ReportResultsPanel`
- `PanelMessage`
- `StatusPill`
- `Button`

### Region changes

Current:

- `ReportsHeroRegion` owns difficulty and boss selection.
- `ReportsWorkspaceRegion` owns report selection, configuration modal, run state, and results.

Proposed:

- Convert the top-level page into a wizard shell.
- Keep difficulty and boss selection as the first wizard step instead of a persistent hero.
- Replace the configuration modal with an in-flow configuration step.
- Keep results as a dedicated final step.

## UI Copy Guidelines

Avoid implementation-facing terms such as:

- backend
- manifest
- view model
- job internals, except job id when useful for support/debugging

Use user-facing terms such as:

- Boss
- Report
- Configure
- Running
- Results
- Damage sources
- Pulls
- Warcraft Logs report codes

## Non-Goals

- Reworking backend report definitions.
- Changing report calculation behavior.
- Replacing the v2 report page model.
- Redesigning tables, row details, or spec analysis.
- Removing the legacy UI switch.
- Adding browser route persistence for each wizard step in the first slice.

## Accessibility Requirements

- Breadcrumbs should use semantic navigation markup.
- Current step should expose `aria-current="step"`.
- Disabled future steps should not be focusable as active controls.
- Step changes should move focus to the new step heading or another sensible target.
- Running status should be readable by assistive tech.
- Animations must respect `prefers-reduced-motion`.

## Acceptance Criteria

- User starts at boss/difficulty selection.
- Selecting a boss advances to report selection.
- Selecting a report advances to configuration.
- Running a report advances to a running feedback step.
- Successful completion advances to results.
- Breadcrumb navigation allows returning to completed prior steps.
- Future breadcrumbs are disabled until the user reaches those steps.
- Changing boss or difficulty clears stale report/result state.
- Report configuration is rendered in-flow, not as the primary workflow modal.
- Running feedback is visible while a report is queued or running.
- The report table animates in once the job completes.
- Existing report APIs continue to work unchanged.
- `npm run build` passes.

## Verification Plan

Manual:

- Select Mythic Imperator Averzian, choose Damage Report, configure, run, and view results.
- Select Mythic Vorasius, choose Damage Report, configure, run, and view results.
- Navigate backward from Results to Configure, Report, and Boss.
- Change boss after results are shown and confirm stale results clear.
- Confirm job errors appear in the running/configuration flow.
- Confirm reduced-motion mode does not produce disruptive animations.

Technical:

- `npm run build`
- Targeted lint on touched files if the full lint suite still has unrelated existing failures.

## Proposed First Slice

1. Add wizard step state and breadcrumb UI.
2. Move boss selection into the first wizard step.
3. Move report selection into the second wizard step.
4. Render report configuration in-flow as the third step.
5. Add running feedback as the fourth step.
6. Render existing report results as the fifth step.
7. Preserve existing data hooks and backend APIs.

No implementation work has been done under this feature request yet.
