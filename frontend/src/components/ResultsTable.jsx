import { Fragment, useEffect, useRef, useState } from "react";
import { ROLE_BADGE_STYLES } from "../config/constants";
import { formatFloat, formatInt } from "../utils/numberFormat";

export function ResultsTable({
  mode,
  rows,
  phaseOrder,
  phaseLabels,
  metricColumns = [],
  playerEvents = {},
  mobileViewMode,
  onMobileViewModeChange,
  renderSortIcon,
  handleSort,
}) {
  const [expandedPlayers, setExpandedPlayers] = useState({});
  useEffect(() => {
    setExpandedPlayers({});
  }, [rows, playerEvents]);

  const showMobileToggle = mode !== "phase-damage" && mode !== "add-damage";

  const togglePlayerRow = (player) => {
    const events = playerEvents?.[player];
    if (!events || events.length === 0) {
      return;
    }
    setExpandedPlayers((prev) => ({
      ...prev,
      [player]: !prev[player],
    }));
  };

  return (
    <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/40">
      {mode === "phase-damage" ? (
        <PhaseDamageTable
          rows={rows}
          phaseOrder={phaseOrder}
          phaseLabels={phaseLabels}
          handleSort={handleSort}
          renderSortIcon={renderSortIcon}
        />
      ) : mode === "add-damage" ? (
        <AddDamageTable rows={rows} handleSort={handleSort} renderSortIcon={renderSortIcon} />
      ) : mode === "dimensius-phase1" ? (
        <>
          {showMobileToggle ? (
            <div className="sm:hidden mt-4 px-4">
              <label className="flex w-full flex-col text-sm font-medium text-slate-300">
                Mobile layout
                <select
                  className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-base text-content focus:border-primary focus:ring focus:ring-primary/40 focus:outline-none themed-select"
                  style={{ colorScheme: "dark" }}
                  value={mobileViewMode}
                  onChange={(event) => onMobileViewModeChange(event.target.value)}
                >
                  <option value="table">Table</option>
                  <option value="cards">Cards</option>
                </select>
                <span className="mt-1 text-xs text-slate-400">Choose how results display on smaller screens.</span>
              </label>
            </div>
          ) : null}
          <MetricTable
            rows={rows}
            metricColumns={metricColumns}
            playerEvents={playerEvents}
            expandedPlayers={expandedPlayers}
            onTogglePlayer={togglePlayerRow}
            mobileViewMode={mobileViewMode}
            handleSort={handleSort}
            renderSortIcon={renderSortIcon}
          />
        </>
      ) : mode === "dimensius-deaths" ? (
        <>
          {showMobileToggle ? (
            <div className="sm:hidden mt-4 px-4">
              <label className="flex w-full flex-col text-sm font-medium text-slate-300">
                Mobile layout
                <select
                  className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-base text-content focus:border-primary focus:ring focus:ring-primary/40 focus:outline-none themed-select"
                  style={{ colorScheme: "dark" }}
                  value={mobileViewMode}
                  onChange={(event) => onMobileViewModeChange(event.target.value)}
                >
                  <option value="table">Table</option>
                  <option value="cards">Cards</option>
                </select>
                <span className="mt-1 text-xs text-slate-400">Choose how results display on smaller screens.</span>
              </label>
            </div>
          ) : null}
          <DeathsTable
            rows={rows}
            playerEvents={playerEvents}
            expandedPlayers={expandedPlayers}
            onTogglePlayer={togglePlayerRow}
            mobileViewMode={mobileViewMode}
            handleSort={handleSort}
            renderSortIcon={renderSortIcon}
          />
        </>
      ) : (
        <>
          {showMobileToggle ? (
            <div className="sm:hidden mt-4 px-4">
              <label className="flex w-full flex-col text-sm font-medium text-slate-300">
                Mobile layout
                <select
                  className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-base text-content focus:border-primary focus:ring focus:ring-primary/40 focus:outline-none themed-select"
                  style={{ colorScheme: "dark" }}
                  value={mobileViewMode}
                  onChange={(event) => onMobileViewModeChange(event.target.value)}
                >
                  <option value="table">Table</option>
                  <option value="cards">Cards</option>
                </select>
                <span className="mt-1 text-xs text-slate-400">Choose how results display on smaller screens.</span>
              </label>
            </div>
          ) : null}
          <CombinedTable
            rows={rows}
            playerEvents={playerEvents}
            expandedPlayers={expandedPlayers}
            onTogglePlayer={togglePlayerRow}
            mobileViewMode={mobileViewMode}
            handleSort={handleSort}
            renderSortIcon={renderSortIcon}
          />
        </>
      )}
    </div>
  );
}

function PhaseDamageTable({ rows, phaseOrder, phaseLabels, handleSort, renderSortIcon }) {
  return (
    <>
      <div className="hidden sm:block overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
            <tr>
              <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
              {phaseOrder.length > 1 ? (
                <SortableHeader
                  label="Avg / Pull - Combined"
                  column="combinedAverage"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                />
              ) : null}
              {phaseOrder.map((phaseId) => (
                <Fragment key={`phase-header-${phaseId}`}>
                  <SortableHeader
                    label={`Total - ${phaseLabels[phaseId] || phaseId}`}
                    column={`total_phase_${phaseId}`}
                    handleSort={handleSort}
                    renderSortIcon={renderSortIcon}
                    align="right"
                  />
                  <SortableHeader
                    label={`Avg / Pull - ${phaseLabels[phaseId] || phaseId}`}
                    column={`avg_phase_${phaseId}`}
                    handleSort={handleSort}
                    renderSortIcon={renderSortIcon}
                    align="right"
                  />
                </Fragment>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
            {rows.map((row) => (
              <tr key={`${row.player}-${row.role}`}>
                <td className="px-4 py-3 font-medium">
                  <span style={{ color: row.color }}>{row.player}</span>
                </td>
                <td className="px-4 py-3">
                  <RoleBadge role={row.role} />
                </td>
                <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                {phaseOrder.length > 1 ? (
                  <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.combinedAverage ?? 0, 2)}</td>
                ) : null}
                {phaseOrder.map((phaseId) => (
                  <Fragment key={`metric-${row.player}-${row.role}-${phaseId}`}>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.phaseTotals?.[phaseId] ?? 0)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">
                      {formatFloat(row.phaseAverages?.[phaseId] ?? 0, 2)}
                    </td>
                  </Fragment>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={3 + (phaseOrder.length > 1 ? 1 : 0) + phaseOrder.length * 2}
                  className="px-4 py-6 text-center text-slate-400"
                >
                  No events matched the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="sm:hidden p-4">
        {rows.length === 0 ? (
          <EmptyMessage />
        ) : (
          rows.map((row) => (
            <div
              key={`${row.player}-${row.role}-phase-card`}
              className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold" style={{ color: row.color }}>
                  {row.player}
                </span>
                <RoleBadge role={row.role} />
              </div>
              <p className="mt-1 text-xs text-slate-400">Pulls: {formatInt(row.pulls)}</p>
              {phaseOrder.length > 1 ? (
                <p className="text-xs text-emerald-200">Avg / pull (combined): {formatFloat(row.combinedAverage ?? 0, 2)}</p>
              ) : null}
              <div className="mt-3 space-y-2 text-sm text-slate-200">
                {phaseOrder.map((phaseId) => (
                  <div key={`phase-card-${row.player}-${row.role}-${phaseId}`} className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                    <p className="text-xs uppercase tracking-widest text-slate-400">{phaseLabels[phaseId] || `Phase ${phaseId}`}</p>
                    <div className="mt-1 flex justify-between text-xs">
                      <span>Total</span>
                      <span>{formatInt(row.phaseTotals?.[phaseId] ?? 0)}</span>
                    </div>
                    <div className="mt-1 flex justify-between text-xs">
                      <span>Avg / Pull</span>
                      <span>{formatFloat(row.phaseAverages?.[phaseId] ?? 0, 2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}

function AddDamageTable({ rows, handleSort, renderSortIcon }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
          <tr>
            <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
            <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
            <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
            <SortableHeader
              label="Total Add Damage"
              column="addTotalDamage"
              handleSort={handleSort}
              renderSortIcon={renderSortIcon}
              align="right"
            />
            <SortableHeader
              label="Avg Add Damage / Pull"
              column="addAverageDamage"
              handleSort={handleSort}
              renderSortIcon={renderSortIcon}
              align="right"
            />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
          {rows.map((row) => (
            <tr key={`${row.player}-${row.role}`}>
              <td className="px-4 py-3 font-medium">
                <span style={{ color: row.color }}>{row.player}</span>
              </td>
              <td className="px-4 py-3">
                <RoleBadge role={row.role} />
              </td>
              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.addTotalDamage ?? 0)}</td>
              <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.addAverageDamage ?? 0, 3)}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                No events matched the filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="sm:hidden p-4">
        {rows.length === 0 ? (
          <EmptyMessage />
        ) : (
          rows.map((row) => (
            <div key={`${row.player}-${row.role}-add-mobile`} className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5">
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold" style={{ color: row.color }}>
                  {row.player}
                </span>
                <RoleBadge role={row.role} />
              </div>
              <dl className="mt-3 space-y-1 text-sm text-slate-200">
                <div className="flex justify-between">
                  <span>Pulls</span>
                  <span>{formatInt(row.pulls)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Add Damage</span>
                  <span>{formatInt(row.addTotalDamage ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Add Damage / Pull</span>
                  <span>{formatFloat(row.addAverageDamage ?? 0, 3)}</span>
                </div>
              </dl>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function MetricTable({
  rows,
  metricColumns = [],
  playerEvents = {},
  expandedPlayers = {},
  onTogglePlayer,
  mobileViewMode,
  handleSort,
  renderSortIcon,
}) {
  const totalColumns = 4 + Math.max(metricColumns.length, 0);
  return (
    <>
      <div className="hidden sm:block overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
            <tr>
              <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
              {metricColumns.map((metric) => (
                <SortableHeader
                  key={`metric-header-${metric.id}`}
                  label={metric.label || metric.id}
                  column={`metric_total_${metric.id}`}
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                />
              ))}
              <SortableHeader label="Fuck-up Rate" column="fuckupRate" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
            {rows.map((row) => {
              const events = playerEvents?.[row.player] ?? [];
              const hasEvents = events.length > 0;
              const isExpanded = !!expandedPlayers[row.player];
              return (
                <Fragment key={`${row.player}-${row.role}`}>
                  <tr
                    className={
                      hasEvents
                        ? "cursor-pointer transition-colors duration-200 hover:bg-emerald-500/10 hover:text-white focus-within:bg-emerald-500/10 focus-within:text-white"
                        : ""
                    }
                    onClick={() => hasEvents && onTogglePlayer?.(row.player)}
                  >
                    <td className="px-4 py-3 font-medium">
                      <span style={{ color: row.color }}>{row.player}</span>
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={row.role} />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                    {metricColumns.map((metric) => (
                      <td key={`metric-row-${row.player}-${metric.id}`} className="px-4 py-3 text-right text-slate-200">
                        {formatInt(row.metricTotals?.[metric.id] ?? 0)}
                      </td>
                    ))}
                    <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.fuckupRate ?? 0, 3)}</td>
                  </tr>
                  {hasEvents ? <EventDetailsRow colSpan={totalColumns} events={events} isExpanded={isExpanded} /> : null}
                </Fragment>
              );
            })}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={totalColumns} className="px-4 py-6 text-center text-slate-400">
                  No events matched the filters.
                </td>
              </tr>
            ) : metricColumns.length === 0 ? (
              <tr>
                <td colSpan={totalColumns} className="px-4 py-6 text-center text-slate-400">
                  Enable at least one option in the tile configuration to see metrics.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <div className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}>
        {rows.length === 0 ? (
          <EmptyMessage />
        ) : mobileViewMode === "cards" ? (
          rows.map((row) => (
            <div
              key={`${row.player}-${row.role}-metric-card`}
              className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold" style={{ color: row.color }}>
                  {row.player}
                </span>
                <RoleBadge role={row.role} />
              </div>
              <dl className="mt-3 space-y-1 text-sm text-slate-200">
                <div className="flex justify-between">
                  <span>Pulls</span>
                  <span>{formatInt(row.pulls)}</span>
                </div>
                {metricColumns.length === 0 ? (
                  <p className="text-xs text-slate-400">Enable at least one option to see detailed metrics.</p>
                ) : (
                  metricColumns.map((metric) => (
                    <div key={`metric-card-${row.player}-${metric.id}`} className="flex justify-between">
                      <span>{metric.label || metric.id}</span>
                      <span>{formatInt(row.metricTotals?.[metric.id] ?? 0)}</span>
                    </div>
                  ))
                )}
                <div className="flex justify-between">
                  <span>Fuck-up Rate</span>
                  <span>{formatFloat(row.fuckupRate ?? 0, 3)}</span>
                </div>
                {playerEvents?.[row.player]?.length ? (
                  <div className="pt-2">
                    <button
                      type="button"
                      className="text-xs font-medium text-primary underline decoration-transparent transition hover:decoration-current focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface"
                      onClick={() => onTogglePlayer?.(row.player)}
                    >
                      {expandedPlayers[row.player] ? "Hide events" : "Show events"}
                    </button>
                    {expandedPlayers[row.player] ? (
                      <div className="mt-2 rounded-lg border border-slate-800/60 bg-slate-900/50 p-2">
                        <EventList events={playerEvents[row.player]} />
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </dl>
            </div>
          ))
        ) : (
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900/60 text-xs uppercase tracking-widest text-slate-400">
              <tr>
                <th className="px-4 py-2 text-left">Player</th>
                <th className="px-4 py-2 text-right">Pulls</th>
                {metricColumns.map((metric) => (
                  <th key={`metric-compact-${metric.id}`} className="px-4 py-2 text-right">
                    {metric.label || metric.id}
                  </th>
                ))}
                <th className="px-4 py-2 text-right">Fuck-up Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/30 text-slate-200">
              {rows.map((row) => (
                <tr key={`${row.player}-${row.role}-metric-compact`}>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span style={{ color: row.color }}>{row.player}</span>
                      <RoleBadge role={row.role} />
                    </div>
                  </td>
                  <td className="px-4 py-2 text-right">{formatInt(row.pulls)}</td>
                  {metricColumns.map((metric) => (
                    <td key={`metric-compact-value-${row.player}-${metric.id}`} className="px-4 py-2 text-right">
                      {formatInt(row.metricTotals?.[metric.id] ?? 0)}
                    </td>
                  ))}
                  <td className="px-4 py-2 text-right">{formatFloat(row.fuckupRate ?? 0, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function DeathsTable({ rows, playerEvents = {}, expandedPlayers = {}, onTogglePlayer, mobileViewMode, handleSort, renderSortIcon }) {
  return (
    <>
      <div className="hidden sm:block overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
            <tr>
              <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
              <SortableHeader label="Deaths" column="deaths" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
              <SortableHeader label="Death Rate" column="deathRate" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
            {rows.map((row) => {
              const events = playerEvents?.[row.player] ?? [];
              const hasEvents = events.length > 0;
              const isExpanded = !!expandedPlayers[row.player];
              return (
                <Fragment key={`${row.player}-${row.role}-death`}>
                  <tr
                    className={
                      hasEvents
                        ? "cursor-pointer transition-colors duration-200 hover:bg-emerald-500/10 hover:text-white focus-within:bg-emerald-500/10 focus-within:text-white"
                        : ""
                    }
                    onClick={() => hasEvents && onTogglePlayer?.(row.player)}
                  >
                    <td className="px-4 py-3 font-medium">
                      <span style={{ color: row.color }}>{row.player}</span>
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={row.role} />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.deaths ?? 0)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.deathRate ?? 0, 3)}</td>
                  </tr>
                  {hasEvents ? <EventDetailsRow colSpan={5} events={events} isExpanded={isExpanded} /> : null}
                </Fragment>
              );
            })}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No events matched the filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <div className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}>
        {rows.length === 0 ? (
          <EmptyMessage />
        ) : mobileViewMode === "cards" ? (
          rows.map((row) => (
            <div
              key={`${row.player}-${row.role}-death-card`}
              className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold" style={{ color: row.color }}>
                  {row.player}
                </span>
                <RoleBadge role={row.role} />
              </div>
              <dl className="mt-3 space-y-1 text-sm text-slate-200">
                <div className="flex justify-between">
                  <span>Pulls</span>
                  <span>{formatInt(row.pulls)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Deaths</span>
                  <span>{formatInt(row.deaths ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Death Rate</span>
                  <span>{formatFloat(row.deathRate ?? 0, 3)}</span>
                </div>
                {playerEvents?.[row.player]?.length ? (
                  <div className="pt-2">
                    <button
                      type="button"
                      className="text-xs font-medium text-primary underline decoration-transparent transition hover:decoration-current focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface"
                      onClick={() => onTogglePlayer?.(row.player)}
                    >
                      {expandedPlayers[row.player] ? "Hide events" : "Show events"}
                    </button>
                    {expandedPlayers[row.player] ? (
                      <div className="mt-2 rounded-lg border border-slate-800/60 bg-slate-900/50 p-2">
                        <EventList events={playerEvents[row.player]} />
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </dl>
            </div>
          ))
        ) : (
          <table className="min-w-full divide-y divide-slate-800 text-xs">
            <thead className="bg-slate-900/80 text-[11px] uppercase tracking-widest text-slate-400">
              <tr>
                <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" small />
                <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" small />
                <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" small />
                <SortableHeader label="Deaths" column="deaths" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" small />
                <SortableHeader label="Death Rate" column="deathRate" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" small />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
              {rows.map((row) => (
                <tr key={`${row.player}-${row.role}-death-table`}>
                  <td className="px-3 py-2 font-medium" style={{ color: row.color }}>
                    {row.player}
                  </td>
                  <td className="px-3 py-2">
                    <RoleBadge role={row.role} small />
                  </td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.pulls)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.deaths ?? 0)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatFloat(row.deathRate ?? 0, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function CombinedTable({
  rows,
  playerEvents = {},
  expandedPlayers = {},
  onTogglePlayer,
  mobileViewMode,
  handleSort,
  renderSortIcon,
}) {
  return (
    <>
      <div className="hidden sm:block overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
            <tr>
              <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" />
              <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
              <SortableHeader
                label="Besiege Hits"
                column="besiegeHits"
                handleSort={handleSort}
                renderSortIcon={renderSortIcon}
                align="right"
              />
              <SortableHeader
                label="Besiege / Pull"
                column="besiegePerPull"
                handleSort={handleSort}
                renderSortIcon={renderSortIcon}
                align="right"
              />
              <SortableHeader
                label="Ghost Misses"
                column="ghostMisses"
                handleSort={handleSort}
                renderSortIcon={renderSortIcon}
                align="right"
              />
              <SortableHeader
                label="Ghost / Pull"
                column="ghostPerPull"
                handleSort={handleSort}
                renderSortIcon={renderSortIcon}
                align="right"
              />
              <SortableHeader label="Fuck-up Rate" column="fuckupRate" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
            {rows.map((row) => {
              const events = playerEvents?.[row.player] ?? [];
              const hasEvents = events.length > 0;
              const isExpanded = !!expandedPlayers[row.player];
              return (
                <Fragment key={`${row.player}-${row.role}`}>
                  <tr
                    className={
                      hasEvents
                        ? "cursor-pointer transition-colors duration-200 hover:bg-emerald-500/10 hover:text-white focus-within:bg-emerald-500/10 focus-within:text-white"
                        : ""
                    }
                    onClick={() => hasEvents && onTogglePlayer?.(row.player)}
                  >
                    <td className="px-4 py-3 font-medium">
                      <span style={{ color: row.color }}>{row.player}</span>
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={row.role} />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.besiegeHits ?? 0)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.besiegePerPull ?? 0, 3)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.ghostMisses ?? 0)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.ghostPerPull ?? 0, 3)}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.fuckupRate ?? 0, 3)}</td>
                  </tr>
                  {hasEvents ? <EventDetailsRow colSpan={8} events={events} isExpanded={isExpanded} /> : null}
                </Fragment>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-slate-400">
                  No events matched the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}>
        {rows.length === 0 ? (
          <EmptyMessage />
        ) : mobileViewMode === "cards" ? (
          rows.map((row) => (
            <div
              key={`${row.player}-${row.role}-card`}
              className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-semibold" style={{ color: row.color }}>
                  {row.player}
                </span>
                <RoleBadge role={row.role} />
              </div>
              <dl className="mt-3 space-y-1 text-sm text-slate-200">
                <div className="flex justify-between">
                  <span>Pulls</span>
                  <span>{formatInt(row.pulls)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Besiege Hits</span>
                  <span>{formatInt(row.besiegeHits ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Besiege / Pull</span>
                  <span>{formatFloat(row.besiegePerPull ?? 0, 3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ghost Misses</span>
                  <span>{formatInt(row.ghostMisses ?? 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ghost / Pull</span>
                  <span>{formatFloat(row.ghostPerPull ?? 0, 3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Fuck-up Rate</span>
                  <span>{formatFloat(row.fuckupRate ?? 0, 3)}</span>
                </div>
                {playerEvents?.[row.player]?.length ? (
                  <div className="pt-2">
                    <button
                      type="button"
                      className="text-xs font-medium text-primary underline decoration-transparent transition hover:decoration-current focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface"
                      onClick={() => onTogglePlayer?.(row.player)}
                    >
                      {expandedPlayers[row.player] ? "Hide events" : "Show events"}
                    </button>
                    {expandedPlayers[row.player] ? (
                      <div className="mt-2 rounded-lg border border-slate-800/60 bg-slate-900/50 p-2">
                        <EventList events={playerEvents[row.player]} />
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </dl>
            </div>
          ))
        ) : (
          <table className="min-w-full divide-y divide-slate-800 text-xs">
            <thead className="bg-slate-900/80 text-[11px] uppercase tracking-widest text-slate-400">
              <tr>
                <SortableHeader label="Player" column="player" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" small />
                <SortableHeader label="Role" column="role" handleSort={handleSort} renderSortIcon={renderSortIcon} align="left" small />
                <SortableHeader label="Pulls" column="pulls" handleSort={handleSort} renderSortIcon={renderSortIcon} align="right" small />
                <SortableHeader
                  label="Besiege Hits"
                  column="besiegeHits"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                  small
                />
                <SortableHeader
                  label="Besiege / Pull"
                  column="besiegePerPull"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                  small
                />
                <SortableHeader
                  label="Ghost Misses"
                  column="ghostMisses"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                  small
                />
                <SortableHeader
                  label="Ghost / Pull"
                  column="ghostPerPull"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                  small
                />
                <SortableHeader
                  label="Fuck-up Rate"
                  column="fuckupRate"
                  handleSort={handleSort}
                  renderSortIcon={renderSortIcon}
                  align="right"
                  small
                />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
              {rows.map((row) => (
                <tr key={`${row.player}-${row.role}-mobile-table`}>
                  <td className="px-3 py-2 font-medium" style={{ color: row.color }}>
                    {row.player}
                  </td>
                  <td className="px-3 py-2">
                    <RoleBadge role={row.role} small />
                  </td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.pulls)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.besiegeHits ?? 0)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatFloat(row.besiegePerPull ?? 0, 3)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.ghostMisses ?? 0)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatFloat(row.ghostPerPull ?? 0, 3)}</td>
                  <td className="px-3 py-2 text-right text-slate-200">{formatFloat(row.fuckupRate ?? 0, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function EventDetailsRow({ colSpan, events, isExpanded }) {
  if (!events || events.length === 0) {
    return null;
  }
  const [contentHeight, setContentHeight] = useState(0);
  const contentRef = useRef(null);

  useEffect(() => {
    if (isExpanded && contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    } else {
      setContentHeight(0);
    }
  }, [isExpanded, events]);

  return (
    <tr aria-hidden={!isExpanded}>
      <td colSpan={colSpan} className="px-0">
        <div
          className={`overflow-hidden px-6 transition-all duration-300 ease-out ${isExpanded ? "opacity-100 py-3" : "opacity-0 py-0"}`}
          style={{ maxHeight: isExpanded ? `${contentHeight}px` : "0px" }}
          aria-hidden={!isExpanded}
        >
          <div ref={contentRef} className="rounded-2xl bg-slate-950/60 px-6 py-4 text-sm text-slate-200 shadow-inner shadow-black/20">
            <EventList events={events} />
          </div>
        </div>
      </td>
    </tr>
  );
}

function EventList({ events }) {
  if (!events || events.length === 0) {
    return null;
  }
  const sorted = [...events].sort((a, b) => (a.timestamp ?? 0) - (b.timestamp ?? 0));
  const grouped = sorted.reduce((acc, event) => {
    const fightId = event.fight_id ?? "unknown";
    const pull = event.pull ?? "?";
    const key = `${fightId}-${pull}`;
    if (!acc[key]) {
      acc[key] = { fightName: event.fight_name, fightId: event.fight_id, pull, events: [] };
    }
    acc[key].events.push(event);
    return acc;
  }, {});
  return (
    <div className="space-y-3">
      {Object.entries(grouped).map(([key, group]) => {
        const reference = group.events[0];
        const pullLabel = `Pull ${group.pull}`;
        const fightLabel = group.fightName
          ? `[${group.fightName}${group.fightId ? ` - Fight ${group.fightId}` : ""}]`
          : group.fightId
          ? `[Fight ${group.fightId}]`
          : "";
        return (
          <div key={key} className="rounded-lg border border-white/5 bg-white/5 px-4 py-3">
            <p className="text-sm font-semibold text-slate-100">
              {pullLabel} - {formatSeconds(reference.offset_ms)} ({formatInt(Math.round(reference.timestamp ?? 0))}) {fightLabel}
            </p>
            <ul className="mt-2 ml-5 list-disc space-y-1 text-slate-300">
              {group.events
                .slice()
                .sort((a, b) => {
                  const aIsDeath = (a.label || "").toLowerCase() === "death";
                  const bIsDeath = (b.label || "").toLowerCase() === "death";
                  if (aIsDeath && !bIsDeath) return -1;
                  if (!aIsDeath && bIsDeath) return 1;
                  return (a.timestamp ?? 0) - (b.timestamp ?? 0);
                })
                .map((event, idx) => (
                <li key={`${key}-${idx}`}>
                  <span className="font-semibold text-emerald-300">{event.label || "Event"}</span>{" "}
                  {event.description ? (
                    <span className="text-slate-200">{event.description}</span>
                  ) : event.ability_label ? (
                    <span className="text-slate-200">via {event.ability_label}</span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

const formatSeconds = (value) => {
  if (!Number.isFinite(value)) {
    return "?";
  }
  return `${(value / 1000).toFixed(2)}s`;
};

const SortableHeader = ({ label, column, handleSort, renderSortIcon, align = "left", small }) => {
  const paddingClass = small ? "px-3 py-2" : "px-4 py-3";
  const textClass = align === "right" ? "text-right" : "text-left";
  const justifyClass = align === "right" ? "justify-end" : "justify-start";

  return (
    <th className={`${paddingClass} ${textClass}`}>
      <button
        type="button"
        className={`flex w-full items-center gap-1 ${justifyClass} ${textClass} text-muted transition hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface`}
        onClick={() => handleSort(column)}
      >
        {align === "right" ? (
          <>
            {renderSortIcon(column)}
            {label}
          </>
        ) : (
          <>
            {label}
            {renderSortIcon(column)}
          </>
        )}
      </button>
    </th>
  );
};

const RoleBadge = ({ role, small }) => (
  <span
    className={`inline-flex rounded-full px-2 py-1 ${small ? "text-[11px]" : "text-xs"} font-medium ${
      ROLE_BADGE_STYLES[role] || ROLE_BADGE_STYLES.Unknown
    }`}
  >
    {role}
  </span>
);

const EmptyMessage = () => (
  <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400">No events matched the filters.</div>
);

