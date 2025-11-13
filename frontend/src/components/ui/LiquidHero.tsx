export default function LiquidHero() {
  return (
    <section className="relative isolate overflow-hidden px-6 py-20 sm:py-28">
      <div aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_80%_at_50%_-20%,white/6%,transparent_50%)]" />
      <div className="mx-auto max-w-4xl rounded-xl2 border border-border/60 bg-glass-gradient backdrop-blur-md shadow-glass">
        <div className="p-8 text-center sm:p-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-muted">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            New tools just landed
          </div>
          <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-6xl">
            Data to enrich your{" "}
            <span className="bg-gradient-to-r from-primary via-primary-2 to-glow bg-clip-text text-transparent">online business</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-muted/90">
            Curated raid analytics in seconds. Stop guessing, start fixing.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <a
              href="#tiles"
              className="inline-flex items-center rounded-lg bg-primary px-5 py-2.5 font-medium text-slate-950 hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring ring-offset-2 ring-offset-surface transition"
            >
              Get started
            </a>
            <a
              href="#tiles"
              className="inline-flex items-center rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-content hover:bg-white/10 transition"
            >
              Learn more →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
