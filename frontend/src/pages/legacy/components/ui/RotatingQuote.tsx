import { ReactNode, useEffect, useMemo, useState } from "react";

type RotatingQuoteProps = {
  quotes: ReactNode[];
  interval?: number;
  fadeDuration?: number;
  className?: string;
};

export function RotatingQuote({ quotes, interval = 7000, fadeDuration = 600, className = "" }: RotatingQuoteProps) {
  const items = useMemo<ReactNode[]>(() => {
    return quotes
      .map((quote) => {
        if (quote == null) {
          return null;
        }
        if (typeof quote === "string") {
          const trimmed = quote.trim();
          return trimmed.length ? trimmed : null;
        }
        return quote;
      })
      .filter((quote): quote is ReactNode => Boolean(quote));
  }, [quotes]);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!items.length) {
      setActiveIndex(0);
      return;
    }
    if (activeIndex >= items.length) {
      setActiveIndex(0);
    }
  }, [items, activeIndex]);

  useEffect(() => {
    if (items.length <= 1) {
      return;
    }
    const effectiveDuration = Math.max(interval, fadeDuration);
    const swapTimer = window.setTimeout(() => {
      setActiveIndex((prev) => (prev + 1) % items.length);
    }, effectiveDuration);
    return () => {
      clearTimeout(swapTimer);
    };
  }, [items.length, activeIndex, interval, fadeDuration]);

  if (!items.length) {
    return null;
  }

  return (
    <div className={["relative grid", className].filter(Boolean).join(" ")} aria-live="polite">
      {items.map((quote, idx) => (
        <p
          key={`quote-${idx}`}
          className={[
            "col-start-1 row-start-1 m-0 transition-opacity ease-in-out",
            idx === activeIndex ? "opacity-100" : "opacity-0",
          ]
            .filter(Boolean)
            .join(" ")}
          style={{ transitionDuration: `${fadeDuration}ms` }}
          aria-hidden={idx === activeIndex ? undefined : true}
        >
          {quote}
        </p>
      ))}
    </div>
  );
}

export default RotatingQuote;
