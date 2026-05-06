import { useState } from "react";
import { Button } from "../atoms/Button";
import { downloadReportTableCsv } from "../../../utils/reportTablePresentation";
import { ReportTags } from "./ReportTags";

export function ReportPageHeader({ page, rows, shareUrl, onOpenSpecAnalysis }) {
  const [copyStatus, setCopyStatus] = useState("");
  const hasSpecAnalysis = Boolean(page?.specAnalysis?.series?.length);
  const hasShareUrl = Boolean(shareUrl);

  const handleCopyLink = async () => {
    if (!shareUrl) {
      return;
    }
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopyStatus("Copied");
      window.setTimeout(() => setCopyStatus(""), 1800);
    } catch (_err) {
      setCopyStatus("Copy failed");
      window.setTimeout(() => setCopyStatus(""), 1800);
    }
  };

  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Report result</p>
        <h2 className="mt-2 text-[2rem] font-semibold tracking-tight text-slate-50">{page.title}</h2>
        {page.header?.subtitle ? <p className="mt-2 max-w-3xl text-sm text-slate-400">{page.header.subtitle}</p> : null}
        <ReportTags tags={page.header?.tags} />
      </div>
      <div className="flex shrink-0 flex-row items-center gap-2 self-start lg:justify-end">
        {hasShareUrl ? (
          <Button type="button" variant="secondary" size="sm" onClick={handleCopyLink}>
            {copyStatus || "Copy Link"}
          </Button>
        ) : null}
        {hasSpecAnalysis ? (
          <Button type="button" variant="accent" size="sm" onClick={onOpenSpecAnalysis}>
            {page.specAnalysis.buttonLabel || "Spec Analysis"}
          </Button>
        ) : null}
        <Button
          type="button"
          variant={hasSpecAnalysis ? "secondary" : "accent"}
          size="sm"
          onClick={() => downloadReportTableCsv(page, rows, page?.content?.table)}
        >
          Download CSV
        </Button>
      </div>
    </div>
  );
}
