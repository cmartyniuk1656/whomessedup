import { Button } from "../atoms/Button";
import { ModalFrame } from "../atoms/ModalFrame";
import { SurfacePanel } from "../atoms/SurfacePanel";
import { useSpecAnalysisSorting } from "../../../hooks/useSpecAnalysisSorting";
import { SpecAnalysisChart } from "../molecules/SpecAnalysisChart";
import { ThemedSelectMenu } from "../molecules/ThemedSelectMenu";

export function SpecAnalysisModal({ analysis, onClose }) {
  const { sortId, setSortId, sortedSeries } = useSpecAnalysisSorting(analysis);

  if (!analysis) {
    return null;
  }

  const titleId = "spec-analysis-title";

  return (
    <ModalFrame titleId={titleId} onClose={onClose} closeLabel="Close spec analysis">
      <SurfacePanel className="mx-auto w-full max-w-[72rem] p-5 sm:p-6">
        <div className="mb-5 flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Spec Analysis</p>
            <h2 id={titleId} className="mt-2 text-2xl font-semibold tracking-tight text-white">
              {analysis.title}
            </h2>
            {analysis.subtitle ? <p className="mt-2 max-w-3xl text-sm text-slate-400">{analysis.subtitle}</p> : null}
            {analysis.basisLabel ? (
              <p className="mt-3 text-[11px] uppercase tracking-[0.16em] text-slate-500">{analysis.basisLabel}</p>
            ) : null}
          </div>

          <div className="w-full max-w-[14rem]">
            <ThemedSelectMenu
              id="spec-analysis-sort"
              label="Sort By"
              value={sortId}
              options={analysis.sortOptions ?? []}
              onChange={setSortId}
            />
          </div>
        </div>

        <SpecAnalysisChart analysis={analysis} series={sortedSeries} />

        <div className="mt-6 flex justify-end border-t border-white/10 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </SurfacePanel>
    </ModalFrame>
  );
}

