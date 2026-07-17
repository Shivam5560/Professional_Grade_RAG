import type { ReactNode } from "react";
import { CheckCircle2, CircleDashed, XCircle, Clock3 } from "lucide-react";
import { cn } from "@/lib/utils";

export function StudioPanel({ title, description, action, children, className }: { title: string; description?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={cn("rounded-xl border border-border bg-card shadow-sm", className)}>
    <header className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
      <div><h2 className="text-sm font-semibold tracking-tight">{title}</h2>{description ? <p className="mt-1 text-xs leading-5 text-muted-foreground">{description}</p> : null}</div>{action}
    </header>
    <div className="p-5">{children}</div>
  </section>;
}

export function StatusPill({ state }: { state: string }) {
  const tone = state === "succeeded" || state === "completed" || state === "verified" || state === "approved" || state === "published"
    ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
    : state === "failed" || state === "rejected" || state === "critical"
      ? "border-destructive/25 bg-destructive/10 text-destructive"
      : state === "running" || state === "awaiting_approval" || state === "inferred" || state === "pending"
        ? "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
        : "border-border bg-muted text-muted-foreground";
  const Icon = state === "succeeded" || state === "completed" || state === "verified" || state === "approved" || state === "published" ? CheckCircle2 : state === "failed" || state === "rejected" || state === "critical" ? XCircle : state === "running" ? CircleDashed : Clock3;
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize", tone)}><Icon className={cn("h-3 w-3", state === "running" && "animate-spin")} />{state.replaceAll("_", " ")}</span>;
}

export function EvidenceTag({ children }: { children: ReactNode }) { return <span className="inline-flex rounded-md border border-[hsl(var(--data)/0.28)] bg-[hsl(var(--data)/0.08)] px-2 py-1 font-mono text-[10px] text-[hsl(var(--data))]">{children}</span>; }

export function EmptyStudioState({ title, description }: { title: string; description: string }) { return <div className="rounded-lg border border-dashed border-border bg-muted/30 p-7 text-center"><p className="text-sm font-medium">{title}</p><p className="mx-auto mt-1 max-w-md text-xs leading-5 text-muted-foreground">{description}</p></div>; }
