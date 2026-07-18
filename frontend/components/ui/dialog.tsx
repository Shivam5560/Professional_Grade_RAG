"use client";

import {
  createContext,
  useContext,
  useEffect,
  useId,
  useRef,
  type HTMLAttributes,
  type MutableRefObject,
  type ReactNode,
} from "react";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

type DialogContextValue = {
  descriptionId: string;
  onOpenChange(open: boolean): void;
  open: boolean;
  returnFocusRef: MutableRefObject<HTMLElement | null>;
  titleId: string;
};

const DialogContext = createContext<DialogContextValue | null>(null);

function useDialogContext(): DialogContextValue {
  const value = useContext(DialogContext);
  if (!value) throw new Error("Dialog components must be used inside Dialog");
  return value;
}

export function Dialog({
  children,
  onOpenChange,
  open,
}: {
  children: ReactNode;
  onOpenChange(open: boolean): void;
  open: boolean;
}): JSX.Element {
  const titleId = useId();
  const descriptionId = useId();
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  useEffect(() => {
    if (open) {
      if (!returnFocusRef.current) returnFocusRef.current = document.activeElement as HTMLElement | null;
      wasOpenRef.current = true;
      return;
    }
    if (wasOpenRef.current) {
      returnFocusRef.current?.focus();
      returnFocusRef.current = null;
    }
    wasOpenRef.current = false;
  }, [open]);

  return (
    <DialogContext.Provider value={{ descriptionId, onOpenChange, open, returnFocusRef, titleId }}>
      {children}
    </DialogContext.Provider>
  );
}

export function DialogContent({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>): JSX.Element | null {
  const { descriptionId, onOpenChange, open, returnFocusRef, titleId } = useDialogContext();
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    if (!returnFocusRef.current) returnFocusRef.current = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusable = contentRef.current?.querySelector<HTMLElement>(
      'input:not([disabled]), textarea:not([disabled]), select:not([disabled]), button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    );
    focusable?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onOpenChange(false);
        return;
      }
      if (event.key !== "Tab") return;
      const items = contentRef.current?.querySelectorAll<HTMLElement>(
        'input:not([disabled]), textarea:not([disabled]), select:not([disabled]), button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
      );
      if (!items?.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onOpenChange, open, returnFocusRef]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] grid place-items-center px-4 py-8">
      <button
        aria-label="Close dialog"
        className="absolute inset-0 cursor-default bg-background/80"
        onClick={() => onOpenChange(false)}
        type="button"
      />
      <div
        ref={contentRef}
        aria-describedby={descriptionId}
        aria-labelledby={titleId}
        aria-modal="true"
        className={cn(
          "relative z-10 w-full max-w-lg rounded-xl border border-border bg-overlay p-5 text-foreground shadow-2xl",
          className,
        )}
        role="dialog"
        {...props}
      >
        {children}
        <button
          aria-label="Close dialog"
          className="absolute right-3 top-3 inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onClick={() => onOpenChange(false)}
          type="button"
        >
          <X aria-hidden="true" className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function DialogHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("space-y-1.5 pr-10", className)} {...props} />;
}

export function DialogTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>): JSX.Element {
  const { titleId } = useDialogContext();
  return <h2 id={titleId} className={cn("text-lg font-semibold", className)} {...props} />;
}

export function DialogDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>): JSX.Element {
  const { descriptionId } = useDialogContext();
  return <p id={descriptionId} className={cn("text-sm leading-6 text-muted-foreground", className)} {...props} />;
}

export function DialogFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("mt-6 flex flex-wrap justify-end gap-2", className)} {...props} />;
}
