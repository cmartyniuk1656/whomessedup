export default function LiquidHero() {
  return (
    <section className="relative isolate overflow-hidden px-6 pt-28 pb-24 sm:pt-32 sm:pb-32">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-white/10 via-transparent to-transparent blur-3xl opacity-40" />
      <div className="mx-auto flex max-w-5xl flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.35em] text-muted shadow-[0_0_40px_rgba(255,255,255,0.05)]">
          New pulse · Emerald intelligence
        </div>
        <h1 className="mt-8 text-4xl font-semibold leading-tight tracking-tight text-white sm:text-6xl sm:leading-tight lg:text-7xl">
          Data to enrich your{" "}
          <span className="bg-gradient-to-r from-primary via-primary-2 to-glow bg-clip-text text-transparent">online raids</span>
        </h1>
        <p className="mt-6 max-w-3xl text-lg text-muted">
          Diagnose wipes across every encounter with frosted telemetry and lightning-fast filters. Emerald glass visuals keep eyes
          sharp during late-night prog.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <a
            href="#tiles"
            className="inline-flex items-center rounded-full bg-primary px-6 py-3 text-base font-semibold text-slate-950 shadow-[0_10px_40px_rgba(16,185,129,0.35)] transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface"
          >
            Launch a tile
          </a>
          <a
            href="#tiles"
            className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-6 py-3 text-base font-semibold text-content transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface"
          >
            Explore features
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M5 12h14m0 0-6-6m6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}
