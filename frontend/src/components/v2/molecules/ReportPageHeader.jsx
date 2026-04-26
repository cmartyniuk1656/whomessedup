import { Button } from "../atoms/Button";
import { downloadReportTableCsv } from "../../../utils/reportTablePresentation";
import { ReportTags } from "./ReportTags";

export function ReportPageHeader({ page, rows, onOpenSpecAnalysis }) {
  const hasSpecAnalysis = Boolean(page?.specAnalysis?.series?.length);

  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Report result</p>
        <h2 className="mt-2 text-[2rem] font-semibold tracking-tight text-slate-50">{page.title}</h2>
        {page.header?.subtitle ? <p className="mt-2 max-w-3xl text-sm text-slate-400">{page.header.subtitle}</p> : null}
        <ReportTags tags={page.header?.tags} />
      </div>
      <div className="flex shrink-0 flex-row items-center gap-2 self-start lg:justify-end">
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
