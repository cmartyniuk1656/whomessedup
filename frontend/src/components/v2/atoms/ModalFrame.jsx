import { useEffect } from "react";
import { createPortal } from "react-dom";

export function ModalFrame({ titleId, onClose, closeLabel = "Close dialog", children }) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return createPortal(
    <>
      <button
        type="button"
        aria-label={closeLabel}
        className="fixed inset-0 z-50 bg-slate-950/72 backdrop-blur-md"
        onClick={onClose}
      />
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
        aria-hidden="true"
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          className="relative z-10 w-full"
          onClick={(event) => event.stopPropagation()}
        >
          {children}
        </div>
      </div>
    </>,
    document.body
  );
}
