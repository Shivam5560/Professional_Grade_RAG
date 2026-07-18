import type { ReactNode } from "react";

export function ContextRibbon({
  children,
  label = "Active context",
}: {
  children: ReactNode;
  label?: string;
}): JSX.Element {
  return (
    <section aria-label={label} className="border-b border-border/60 py-3">
      <div className="flex min-h-9 w-full items-center gap-2 overflow-x-auto overscroll-x-contain pb-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <span className="sticky left-0 z-10 shrink-0 bg-workspace pr-2 text-[10px] font-semibold uppercase text-muted-foreground">
          {label}
        </span>
        <div className="flex min-w-max items-center gap-2">{children}</div>
      </div>
    </section>
  );
}
