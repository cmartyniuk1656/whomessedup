import { SurfacePanel } from "../atoms/SurfacePanel";
import { ReportPageView } from "./ReportPageView";

export function ReportResultsPanel({ page, shareUrl }) {
  if (!page) {
    return null;
  }

  return (
    <SurfacePanel className="p-6" tone="muted">
      <ReportPageView page={page} shareUrl={shareUrl} />
    </SurfacePanel>
  );
}
