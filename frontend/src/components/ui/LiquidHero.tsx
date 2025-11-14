import RotatingQuote from "./RotatingQuote";

const HERO_QUOTES = [
  "Alone we can do so little; together we can do so much.",
  "WHO'S TALKING? DID SOMEONE SAY SOMETHING?",
  "Death is no more than passing from one room into another. But there's a difference for me, you know. Because in that other room I shall be able to see.",
  "WATURRR! WATURRRR!",
  "Avoiding danger is no safer in the long run than outright exposure. The fearful are caught as often as the bold.",
  "We can do anything we want to if we stick to it long enough.",
];

export default function LiquidHero() {
  return (
    <section className="relative isolate overflow-hidden px-6 pt-28 pb-24 sm:pt-32 sm:pb-32">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-white/10 via-transparent to-transparent blur-3xl opacity-40" />
      <div className="mx-auto flex max-w-5xl flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.35em] text-muted shadow-[0_0_40px_rgba(255,255,255,0.05)]">
          Log Analysis · Mythic Raid Tools
        </div>
        <h1 className="mt-8 text-4xl font-semibold leading-tight tracking-tight text-white sm:text-6xl sm:leading-tight lg:text-7xl">
          {" "}
          <span className="bg-gradient-to-r from-primary via-primary-2 to-glow bg-clip-text text-transparent">HK Logs</span>
        </h1>
        <RotatingQuote className="mt-6 max-w-3xl text-lg text-muted" quotes={HERO_QUOTES} interval={8000} fadeDuration={800} />
        <p className="mt-2 text-base text-muted/80 italic font-bold">- Helen Keller</p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        </div>
      </div>
    </section>
  );
}
