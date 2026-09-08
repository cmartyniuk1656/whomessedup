import { useEffect, useState } from "react";
import { Button } from "../atoms/Button";
import { SurfacePanel } from "../atoms/SurfacePanel";
import { RealtimeReportControl } from "../molecules/RealtimeReportControl";
import { ReportPageView } from "./ReportPageView";

function FullWidthIcon({ expanded }) {
  return expanded ? (
    <svg aria-hidden="true" className="h-6 w-6" viewBox="0 0 24 24" fill="none">
      <path
        d="M9 3v6H3M15 3v6h6M9 21v-6H3M15 21v-6h6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.2"
      />
    </svg>
  ) : (
    <svg aria-hidden="true" className="h-6 w-6" viewBox="0 0 24 24" fill="none">
      <path
        d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.2"
      />
    </svg>
  );
}

export function ReportResultsPanel({ page, shareUrl, realtime }) {
  const [isFullWidth, setIsFullWidth] = useState(false);

  useEffect(() => {
    setIsFullWidth(false);
  }, [page?.reportCode, page?.reportId]);

  if (!page) {
    return null;
  }

  return (
    <SurfacePanel
      className={[
        "relative p-6 transition-[width] duration-300 ease-out motion-reduce:transition-none",
        isFullWidth
          ? "left-1/2 w-[calc(100vw-3rem)] max-w-none -translate-x-1/2"
          : "w-full",
      ].join(" ")}
      tone="muted"
    >
      <div className="absolute left-0 top-0 z-10 hidden lg:block">
        <Button
          type="button"
          variant={isFullWidth ? "accent" : "secondary"}
          size="sm"
          className="h-10 w-10 p-0"
          aria-label={isFullWidth ? "Exit full width" : "Expand report to full width"}
          aria-pressed={isFullWidth}
          title={isFullWidth ? "Exit full width" : "Full width"}
          onClick={() => setIsFullWidth((current) => !current)}
        >
          <FullWidthIcon expanded={isFullWidth} />
        </Button>
      </div>
      {realtime?.isVisible ? (
        <div className="mb-5 flex justify-end lg:absolute lg:right-0 lg:top-0 lg:z-10 lg:mb-0">
          <RealtimeReportControl realtime={realtime} />
        </div>
      ) : null}
      <div className="lg:pt-14">
        <ReportPageView page={page} shareUrl={shareUrl} realtime={realtime} />
      </div>
    </SurfacePanel>
  );
}
