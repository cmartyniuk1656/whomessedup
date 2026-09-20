/** Pull selection and filtering for the backend-owned coverage timeline. */
import { useState } from "react";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { PullTimeline } from "./PullTimeline";
import "./coverage.css";

export function CooldownCoverageReport({ page, shareUrl }) {
  const timeline = page.content.timeline;
  const [pullId, setPullId] = useState(timeline.pulls[0]?.id);
  const pull =
    timeline.pulls.find((entry) => entry.id === pullId) || timeline.pulls[0];
  return (
    <section className="coverage-report">
      <ReportPageHeader page={page} shareUrl={shareUrl} rows={[]} />
      <div className="coverage-pull-bar">
        <label>
          Pull{" "}
          <select
            value={pull?.id || ""}
            onChange={(event) => setPullId(event.target.value)}
          >
            {timeline.pulls.map((entry) => (
              <option value={entry.id} key={entry.id}>
                {entry.label}
              </option>
            ))}
          </select>
        </label>
        <span>
          {timeline.pulls.length} pulls loaded · {timeline.boss}
        </span>
        {pull && (
          <a href={pull.url} target="_blank" rel="noreferrer">
            Open pull in Warcraft Logs ↗
          </a>
        )}
      </div>
      {pull ? (
        <PullTimeline
          key={pull.id}
          pull={pull}
          binSeconds={timeline.binSeconds}
        />
      ) : (
        <p>No matching pulls were found.</p>
      )}
      <details className="coverage-notes">
        <summary>How to read this report · timing and data notes</summary>
        {page.footnotes.map((note) => (
          <p key={note}>{note}</p>
        ))}
      </details>
    </section>
  );
}
