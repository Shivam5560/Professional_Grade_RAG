"use client";

import { motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";

export function Inspector({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange(open: boolean): void;
  title: string;
  children: ReactNode;
}): JSX.Element {
  const titleId = useId();
  const panelRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);
  const onOpenChangeRef = useRef(onOpenChange);
  const reduceMotion = useReducedMotion();
  onOpenChangeRef.current = onOpenChange;

  useEffect(() => {
    if (!open) {
      if (wasOpenRef.current) returnFocusRef.current?.focus();
      wasOpenRef.current = false;
      return;
    }

    wasOpenRef.current = true;
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const containKeyboardFocus = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChangeRef.current(false);
        return;
      }
      if (event.key !== "Tab") return;

      const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", containKeyboardFocus);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", containKeyboardFocus);
    };
  }, [open]);

  return (
    <div
      aria-hidden={!open}
      className={open ? "fixed inset-0 z-[70]" : "pointer-events-none fixed inset-0 z-[70]"}
    >
      {open ? (
        <button
          aria-label={`Close ${title}`}
          className="absolute inset-0 hidden cursor-default bg-background/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring lg:block"
          onClick={() => onOpenChange(false)}
          type="button"
        />
      ) : null}
      <motion.aside
        ref={panelRef}
        aria-labelledby={titleId}
        aria-modal="true"
        className="absolute inset-0 flex h-[100svh] w-full flex-col border-l border-border/70 bg-overlay shadow-2xl lg:inset-y-0 lg:left-auto lg:right-0 lg:w-[min(30rem,42vw)]"
        hidden={!open}
        initial={false}
        animate={{ opacity: open ? 1 : 0, x: open ? 0 : 32 }}
        transition={reduceMotion ? { duration: 0 } : { duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
        role="dialog"
      >
        <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border/70 px-4 sm:px-6">
          <h2 id={titleId} className="min-w-0 truncate text-sm font-semibold text-foreground">
            {title}
          </h2>
          <button
            ref={closeButtonRef}
            aria-label={`Close ${title}`}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={() => onOpenChange(false)}
            type="button"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-5 sm:px-6">
          {children}
        </div>
      </motion.aside>
    </div>
  );
}
