"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useRef } from "react";

import {
  AuthPanel,
  type LoginValues,
  type RegisterValues,
} from "@/components/auth/AuthPanel";

interface AuthOverlayProps {
  open: boolean;
  mode: "login" | "register";
  onOpenChange(open: boolean): void;
  onLogin(values: LoginValues): Promise<void>;
  onRegister(values: RegisterValues): Promise<void>;
}

export function AuthOverlay({
  open,
  mode,
  onOpenChange,
  onLogin,
  onRegister,
}: AuthOverlayProps) {
  const reducedMotion = useReducedMotion();
  const closeRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    const containFocus = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
      if (event.key !== "Tab") return;

      const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
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
    window.addEventListener("keydown", containFocus);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", containFocus);
    };
  }, [onOpenChange, open]);

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-[100] flex justify-end bg-black/55 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reducedMotion ? 0 : 0.28 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onOpenChange(false);
          }}
        >
          <motion.section
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="auth-overlay-title"
            className="relative flex min-h-svh w-full max-w-[34rem] flex-col overflow-y-auto border-l border-white/10 bg-[hsl(var(--background)/.94)] px-6 pb-10 pt-24 shadow-2xl backdrop-blur-2xl sm:px-10 lg:px-14"
            initial={reducedMotion ? false : { x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={
              reducedMotion
                ? { duration: 0 }
                : { type: "spring", stiffness: 240, damping: 30, mass: 0.9 }
            }
          >
            <button
              ref={closeRef}
              type="button"
              aria-label="Close authentication"
              onClick={() => onOpenChange(false)}
              className="absolute right-6 top-6 grid size-11 place-items-center rounded-full border border-border/70 bg-background/55 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X aria-hidden className="size-5" />
            </button>
            <div className="my-auto py-8">
              <p className="font-mono text-xs font-semibold uppercase text-[hsl(var(--signal))]">
                Private workspace
              </p>
              <h2
                id="auth-overlay-title"
                className="mt-5 max-w-md text-4xl font-bold leading-tight sm:text-5xl"
              >
                Enter NexusMind.
              </h2>
              <p className="mt-4 max-w-md text-sm leading-6 text-muted-foreground">
                Continue into your connected research, data, analysis, and career workspaces.
              </p>
              <div className="mt-10">
                <AuthPanel
                  key={mode}
                  initialMode={mode}
                  onLogin={onLogin}
                  onRegister={onRegister}
                />
              </div>
            </div>
          </motion.section>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
