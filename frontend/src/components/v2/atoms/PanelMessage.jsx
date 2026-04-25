const TONE_CLASSES = {
  neutral: "border-white/10 bg-[color:rgba(15,23,42,0.6)] text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]",
  danger: "border-rose-500/35 bg-rose-500/10 text-rose-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]",
};

export function PanelMessage({ tone = "neutral", children }) {
  if (!children) {
    return null;
  }

  return (
    <div className={`rounded-[20px] border px-4 py-3 text-sm backdrop-blur-sm ${TONE_CLASSES[tone] || TONE_CLASSES.neutral}`}>
      {children}
    </div>
  );
}
