import { AlertTriangle, ArrowRight, Braces, ShieldCheck } from "lucide-react";
import { EvidenceTag, EmptyStudioState, StatusPill, StudioPanel } from "../StudioPrimitives";
import type { Computation, DatasetProfile, Finding, PlanStep, StudioRun } from "@/lib/studios/data-analyst/types";

interface Props { profile: DatasetProfile | null; run: StudioRun | null; plan: PlanStep[]; computations: Computation[]; findings: Finding[]; limitations: string[] }

export function DataAnalystWorkspace({ profile, run, plan, computations, findings, limitations }: Props) {
  return <div className="space-y-5">
    {run ? <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card px-5 py-4 shadow-sm">
      <div><div className="flex items-center gap-2"><StatusPill state={run.state} /><span className="font-mono text-[11px] text-muted-foreground">{run.id}</span></div><p className="mt-2 text-sm font-medium">{run.question ?? "Analysis run"}</p></div>
      <div className="min-w-48"><div className="mb-1 flex justify-between text-[11px] text-muted-foreground"><span>Verified workflow</span><span>{Math.round(run.progress * 100)}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${Math.max(2, run.progress * 100)}%` }} /></div></div>
    </div> : null}
    <div className="grid gap-5 xl:grid-cols-[0.82fr_1.35fr_1fr]">
      <div className="space-y-5">
        <StudioPanel title="Dataset profile" description="Immutable snapshot and deterministic quality checks">
          {profile ? <><div className="grid grid-cols-2 gap-3"><Metric label="Rows" value={profile.row_count.toLocaleString()} /><Metric label="Columns" value={profile.column_count} /></div><div className="mt-4 space-y-2">{profile.columns.slice(0, 8).map((column) => <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3" key={column.name}><div className="min-w-0"><p className="truncate font-mono text-xs">{column.name}</p><p className="mt-1 text-[10px] text-muted-foreground">{column.unique_count.toLocaleString()} unique · {column.missing_count} missing</p></div><span className="text-[10px] font-semibold uppercase text-muted-foreground">{column.inferred_type}</span></div>)}</div></> : <EmptyStudioState title="No profile yet" description="Upload a CSV snapshot to inspect types, quality, and sensitive fields." />}
        </StudioPanel>
        {profile?.warnings.length ? <StudioPanel title="Data warnings"><ul className="space-y-2">{profile.warnings.map((warning) => <li className="flex gap-2 text-xs leading-5 text-amber-700 dark:text-amber-300" key={warning}><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{warning}</li>)}</ul></StudioPanel> : null}
      </div>
      <div className="space-y-5">
        <StudioPanel title="Analysis plan" description="Registered methods execute only after prerequisites pass">
          {plan.length ? <ol className="space-y-2">{plan.map((step, index) => <li className="flex items-start gap-3 rounded-lg border border-border p-3" key={step.id}><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-muted font-mono text-[10px]">{index + 1}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-semibold">{step.title}</p><StatusPill state={step.state} /></div><p className="mt-1 font-mono text-[10px] text-muted-foreground">{step.method_id}</p>{step.assumptions.length ? <p className="mt-2 text-[11px] text-muted-foreground">Assumes {step.assumptions.join(", ")}</p> : null}</div></li>)}</ol> : <EmptyStudioState title="Plan pending" description="The method planner will choose reproducible tools from the registered method catalog." />}
        </StudioPanel>
        <StudioPanel title="Computation notebook" description="Parameters, diagnostics, metrics, and evidence remain inspectable">
          {computations.length ? <div className="space-y-3">{computations.map((computation) => <article className="rounded-lg border border-border p-4" key={computation.id}><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><Braces className="h-4 w-4 text-[hsl(var(--data))]" /><p className="font-mono text-xs font-semibold">{computation.method_id}</p></div><EvidenceTag>{computation.evidence_id}</EvidenceTag></div><dl className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">{Object.entries(computation.metrics).map(([key, value]) => <div className="rounded-md bg-muted/60 p-2" key={key}><dt className="text-[10px] text-muted-foreground">{key.replaceAll("_", " ")}</dt><dd className="mt-1 font-mono text-xs font-semibold">{String(value)}</dd></div>)}</dl><div className="mt-3 flex flex-wrap gap-2">{computation.assumptions.map((item) => <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground" key={item.name}><ShieldCheck className={item.passed ? "h-3 w-3 text-emerald-500" : "h-3 w-3 text-destructive"} />{item.name}</span>)}</div></article>)}</div> : <EmptyStudioState title="No computations yet" description="Executed steps appear here with method versions and evidence identifiers." />}
        </StudioPanel>
      </div>
      <div className="space-y-5">
        <StudioPanel title="Verified findings" description="Every published claim resolves to computation evidence">
          {findings.length ? <div className="space-y-3">{findings.map((finding) => <article className="rounded-lg border border-border p-4" key={finding.id}><div className="flex items-center justify-between gap-3"><span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{finding.language_class}</span><span className="font-mono text-[10px]">{Math.round(finding.confidence * 100)}% confidence</span></div><p className="mt-2 text-sm leading-6">{finding.statement}</p><div className="mt-3 flex flex-wrap items-center gap-2"><ArrowRight className="h-3 w-3 text-muted-foreground" />{finding.evidence_ids.map((id) => <EvidenceTag key={id}>{id}</EvidenceTag>)}</div></article>)}</div> : <EmptyStudioState title="Findings pending" description="Only claims that pass analytical verification are shown here." />}
        </StudioPanel>
        <StudioPanel title="Limitations" description="What this analysis cannot safely conclude">
          {limitations.length ? <ul className="space-y-3">{limitations.map((limitation) => <li className="flex gap-2 text-xs leading-5 text-muted-foreground" key={limitation}><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />{limitation}</li>)}</ul> : <EmptyStudioState title="No limitations published" description="Method and scope limitations will be attached to the report." />}
        </StudioPanel>
      </div>
    </div>
  </div>;
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div className="rounded-lg border border-border bg-muted/30 p-3"><p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-xl font-semibold">{value}</p></div>; }
