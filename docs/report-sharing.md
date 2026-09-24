# Sharing the current report view

**Share Report** copies a link to the currently displayed report, including:

- Aggregate subreport, pull/table view and nested mechanic selectors.
- Row, column, target and metric filters; sorting and expanded detail rows.
- Defensive player, This pull/Across pulls, mechanic alignment and occurrence, hidden players, boss icons and damage/health layers.
- Healer coverage pull, healer, boss icons, pressure and readiness controls.
- Graph scale, zoom, horizontal timeline position, inspected time, open cast/death details and full-width layout.

Existing input-only links continue to work. The report loads from its normal cache or runs again if necessary. Views refer to the report's data rather than storing a frozen copy of its measurements. Missing recorded events close their detail panel; invalid settings fall back to normal defaults.

`ReportViewProvider` owns a registry of mounted controls. `useReportViewState` retains the usual local React state behavior and registers committed values without broadcasting every update to the report. `ReportViewScope` separates child reports; `resetKey` separates pull/table controls. Only mounted controls enter the copied snapshot. `useReportViewScroll` reads the actual horizontal position at copy time. `useTimelineSelection` serializes small event references and resolves them against the loaded report, never embedding log payloads.

The versioned, UTF-8 view snapshot is in the `#view=` fragment. It stays out of report API requests and cache keys. Input identity, bounded size and control-specific validation prevent unrelated or malformed fragments from breaking the report. Hash navigation also restores the view when the report is already open.

Run `cd frontend && npm run test:sharing` for fresh-mount round trips through production components, including React Strict Mode, legacy links, malformed state and same-page hash changes.
