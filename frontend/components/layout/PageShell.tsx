import type { ReactNode } from "react";

import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { cn } from "@/lib/utils";

type PageShellProps = {
  title?: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  maxWidth?: "5xl" | "6xl" | "7xl" | "full";
  className?: string;
  contentClassName?: string;
};

const maxWidthClass = {
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
  full: "max-w-none",
};

export function PageShell({
  title,
  description,
  eyebrow,
  actions,
  children,
  maxWidth = "6xl",
  className,
  contentClassName,
}: PageShellProps) {
  const label = title ?? eyebrow ?? "Application workspace";

  return (
    <FocusCanvas ariaLabel={label} className={cn("text-foreground", className)}>
      <div className={cn("mx-auto w-full", maxWidthClass[maxWidth], contentClassName)}>
        {title ? (
          <CanvasHeader
            eyebrow={eyebrow}
            title={title}
            description={description}
            actions={actions}
          />
        ) : null}
        <div className={title ? "mt-7" : undefined}>{children}</div>
      </div>
    </FocusCanvas>
  );
}

export function SectionPanel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("border-y border-border/70 py-5 md:py-6", className)}>
      {children}
    </section>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  className,
}: {
  label: string;
  value: string | number;
  detail?: string;
  className?: string;
}) {
  return (
    <div className={cn("border-l border-border/70 px-4 py-2", className)}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}
