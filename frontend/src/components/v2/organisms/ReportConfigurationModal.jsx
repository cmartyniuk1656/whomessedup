import { ModalFrame } from "../atoms/ModalFrame";
import { SurfacePanel } from "../atoms/SurfacePanel";
import { ReportRequestForm } from "./ReportRequestForm";

export function ReportConfigurationModal({
  report,
  values,
  isSubmitting,
  pendingJob,
  onClose,
  onSubmit,
  onValueChange,
  onMultiTextChange,
  onAddMultiTextRow,
  onRemoveMultiTextRow,
}) {
  if (!report) {
    return null;
  }

  const titleId = `${report.id}-configuration-title`;

  return (
    <ModalFrame titleId={titleId} onClose={onClose}>
      <SurfacePanel className="mx-auto w-full max-w-[32rem] p-4 sm:p-5">
        <div className="mb-4 border-b border-white/10 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Report Configuration</p>
            <h2 id={titleId} className="mt-2 text-2xl font-semibold text-white">
              {report.title}
            </h2>
            <p className="mt-1.5 max-w-2xl text-sm text-slate-400">
              Adjust settings before running {report.title}.
            </p>
          </div>
        </div>

        <ReportRequestForm
          report={report}
          values={values}
          isSubmitting={isSubmitting}
          pendingJob={pendingJob}
          onSubmit={onSubmit}
          onCancel={onClose}
          onValueChange={onValueChange}
          onMultiTextChange={onMultiTextChange}
          onAddMultiTextRow={onAddMultiTextRow}
          onRemoveMultiTextRow={onRemoveMultiTextRow}
          layout="modal"
        />
      </SurfacePanel>
    </ModalFrame>
  );
}
