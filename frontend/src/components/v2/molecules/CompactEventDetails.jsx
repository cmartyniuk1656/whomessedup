// Progressive disclosure: key metrics and contributions first, full evidence on demand.
import { EventGroupList } from "./EventGroupList";
import { MetricList } from "./MetricList";
import { RelativeBarChart } from "./RelativeBarChart";

export function CompactEventDetails({ details }) {
  return (
    <div className="min-w-0 space-y-4">
      {details.metrics?.length ? <MetricList metrics={details.metrics} panel /> : null}
      {details.barChart ? <RelativeBarChart chart={details.barChart} standalone compact /> : null}
      <div className="space-y-2">
        {details.groups.map((group) => (
          <details key={group.id} className="min-w-0 rounded-xl border border-white/10 bg-slate-950/20">
            <summary className="cursor-pointer break-words px-3 py-2.5 text-sm font-medium text-slate-200 marker:text-emerald-300">
              {group.title} <span className="ml-1 text-xs font-normal text-slate-400">({group.items.length})</span>
            </summary>
            <div className="min-w-0 px-2 pb-2">
              <EventGroupList details={{ groups: [group] }} compact />
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
