import { Suspense, lazy, useState } from "react";
import { ReportsPage } from "./pages/ReportsPage";

const LegacyReportsPage = lazy(() => import("./pages/legacy/LegacyReportsPage"));

function LegacyPageFallback() {
  return (
    <div className="liquid-bg min-h-dvh text-content relative overflow-hidden" style={{ isolation: "isolate" }}>
      <div aria-hidden className="liquid-glow liquid-glow--top -z-30" />
      <div aria-hidden className="liquid-glow liquid-glow--bottom -z-30" />
      <div aria-hidden className="liquid-blob liquid-blob--emerald -z-20 opacity-70" />
      <div aria-hidden className="liquid-blob liquid-blob--cyan -z-20 opacity-65" />
      <div aria-hidden className="liquid-blob liquid-blob--magenta -z-20 opacity-55" />
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 mix-blend-overlay opacity-25 [background-image:var(--noise)]" />
      <main className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-300 shadow-lg shadow-emerald-500/10">
          Loading legacy UI...
        </div>
      </main>
    </div>
  );
}

function App() {
  const [mode, setMode] = useState("reports");

  if (mode === "reports") {
    return <ReportsPage onSwitchToLegacy={() => setMode("legacy")} />;
  }

  return (
    <Suspense fallback={<LegacyPageFallback />}>
      <LegacyReportsPage onSwitchToReports={() => setMode("reports")} />
    </Suspense>
  );
}

export default App;
