import { useEffect, useMemo, useRef, useState } from "react";

function ChevronDownIcon({ className = "" }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      focusable="false"
      viewBox="0 0 20 20"
    >
      <path
        d="M5.75 7.5 10 11.75 14.25 7.5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.75"
      />
    </svg>
  );
}

function clampIndex(index, optionCount) {
  if (optionCount <= 0) {
    return 0;
  }
  return Math.min(Math.max(index, 0), optionCount - 1);
}

export function ThemedSelectMenu({
  id,
  label,
  options = [],
  value,
  onChange,
  className = "",
}) {
  const rootRef = useRef(null);
  const buttonRef = useRef(null);
  const optionRefs = useRef([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const normalizedOptions = useMemo(() => (Array.isArray(options) ? options : []), [options]);
  const selectedIndex = useMemo(
    () => normalizedOptions.findIndex((option) => option.id === value),
    [normalizedOptions, value]
  );
  const selectedOption = selectedIndex >= 0 ? normalizedOptions[selectedIndex] : normalizedOptions[0];
  const menuId = `${id}-menu`;

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handlePointerDown = (event) => {
      if (!rootRef.current?.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const nextIndex = clampIndex(activeIndex, normalizedOptions.length);
    optionRefs.current[nextIndex]?.focus();
  }, [activeIndex, isOpen, normalizedOptions.length]);

  const openMenu = (preferredIndex = selectedIndex) => {
    if (!normalizedOptions.length) {
      return;
    }
    const nextIndex = preferredIndex >= 0 ? preferredIndex : 0;
    setActiveIndex(clampIndex(nextIndex, normalizedOptions.length));
    setIsOpen(true);
  };

  const closeMenu = ({ restoreFocus = false } = {}) => {
    setIsOpen(false);
    if (restoreFocus) {
      window.requestAnimationFrame(() => buttonRef.current?.focus());
    }
  };

  const selectOption = (option) => {
    onChange?.(option.id);
    closeMenu({ restoreFocus: true });
  };

  const handleButtonKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      openMenu(selectedIndex + 1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      openMenu(selectedIndex > 0 ? selectedIndex - 1 : normalizedOptions.length - 1);
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    }
  };

  const handleMenuKeyDown = (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu({ restoreFocus: true });
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => clampIndex(current + 1, normalizedOptions.length));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => clampIndex(current - 1, normalizedOptions.length));
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      setActiveIndex(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      setActiveIndex(Math.max(normalizedOptions.length - 1, 0));
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const option = normalizedOptions[activeIndex];
      if (option) {
        selectOption(option);
      }
    }
  };

  return (
    <div ref={rootRef} className={["relative", className].filter(Boolean).join(" ")}>
      <label
        className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400"
        htmlFor={id}
      >
        {label}
      </label>
      <button
        ref={buttonRef}
        id={id}
        type="button"
        aria-controls={menuId}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        className={[
          "mt-1 flex h-11 w-full items-center justify-between gap-2 rounded-lg border bg-slate-950/70 px-3 text-left text-sm text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/30 disabled:cursor-not-allowed disabled:opacity-60",
          isOpen
            ? "border-emerald-300/70 ring-2 ring-emerald-400/20"
            : "border-white/10 hover:border-emerald-300/35 hover:bg-slate-950/85",
        ]
          .filter(Boolean)
          .join(" ")}
        disabled={!normalizedOptions.length}
        onClick={() => (isOpen ? closeMenu() : openMenu())}
        onKeyDown={handleButtonKeyDown}
      >
        <span className="truncate">{selectedOption?.label ?? "Select option"}</span>
        <ChevronDownIcon
          className={[
            "h-4 w-4 shrink-0 text-slate-400 transition",
            isOpen ? "rotate-180 text-emerald-200" : null,
          ]
            .filter(Boolean)
            .join(" ")}
        />
      </button>

      {isOpen ? (
        <div
          id={menuId}
          role="listbox"
          aria-labelledby={id}
          className="absolute right-0 z-50 mt-1 w-full overflow-hidden rounded-lg border border-emerald-400/25 bg-slate-950/95 p-1 shadow-[0_24px_70px_-30px_rgba(16,185,129,0.85)] ring-1 ring-white/10 backdrop-blur-xl"
          onKeyDown={handleMenuKeyDown}
        >
          {normalizedOptions.map((option, index) => {
            const isSelected = option.id === value;
            const isActive = index === activeIndex;
            return (
              <button
                key={option.id}
                ref={(element) => {
                  optionRefs.current[index] = element;
                }}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={[
                  "flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm transition focus-visible:outline-none",
                  isSelected
                    ? "bg-emerald-400/15 text-emerald-100"
                    : isActive
                      ? "bg-white/[0.07] text-white"
                      : "text-slate-200 hover:bg-white/[0.06] hover:text-white",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => selectOption(option)}
                onFocus={() => setActiveIndex(index)}
              >
                <span className="truncate">{option.label}</span>
                {isSelected ? (
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.9)]" />
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
