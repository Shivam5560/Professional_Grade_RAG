"use client";

import Link from "next/link";
import { useReducer, useState } from "react";
import { BarChart3, History, Play, Upload } from "lucide-react";
import { PageShell } from "@/components/layout/PageShell";
import { DataAnalystWorkspace } from "@/components/studios/data-analyst/DataAnalystWorkspace";
import { StudioPanel, StatusPill } from "@/components/studios/StudioPrimitives";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { dataAnalystClient } from "@/lib/studios/data-analyst/client";
import { analysisWorkspaceReducer, initialAnalysisWorkspace } from "@/lib/studios/data-analyst/reducer";
import type {
  ColumnProfile,
  Computation,
  DatasetProfile,
  Finding,
  PlanStep,
  StudioRunState,
} from "@/lib/studios/data-analyst/types";

type NormalizableColumnProfile = Omit<ColumnProfile, "inferred_type"> & {
  inferred_type?: string;
  semantic_type?: string;
  dtype?: string;
};

type NormalizableDatasetProfile = Omit<DatasetProfile, "columns" | "warnings"> & {
  columns: NormalizableColumnProfile[];
  warnings?: string[];
};

type NormalizablePlanStep = Omit<PlanStep, "title" | "state" | "depends_on"> & {
  title?: string;
  state?: PlanStep["state"];
  depends_on?: string[];
  rationale?: string;
  prerequisite_step_ids?: string[];
};

type NormalizablePlan = { steps?: NormalizablePlanStep[] } | NormalizablePlanStep[];

export default function AnalysisStudioPage() {
  const [state, dispatch] = useReducer(analysisWorkspaceReducer, initialAnalysisWorkspace);
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [computations, setComputations] = useState<Computation[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [limitations, setLimitations] = useState<string[]>([]);

  async function start() {
    if (!file || question.trim().length < 3) return;
    dispatch({ type: "loading" });
    try {
      const snapshot = await dataAnalystClient.createDataset(file);
      dispatch({ type: "profile-loaded", profile: normalizeProfile(snapshot.profile) });
      const response = await dataAnalystClient.createRun({ snapshot_id: snapshot.snapshot_id, question: question.trim() }, crypto.randomUUID());
      const run = { ...response.run, question: response.run.question ?? question.trim() };
      dispatch({ type: "run-loaded", run });
      setPlan(normalizePlan(response.plan, run.state));
      const [nextComputations, nextFindings, report] = await Promise.all([
        dataAnalystClient.getComputations(run.id),
        dataAnalystClient.getClaims(run.id),
        dataAnalystClient.getReport(run.id).catch(() => ({ limitations: run.warnings ?? [] })),
      ]);
      setComputations(nextComputations);
      setFindings(nextFindings);
      setLimitations(report.limitations ?? []);
    } catch (reason) {
      dispatch({ type: "failed", message: reason instanceof Error ? reason.message : "Unable to start analysis" });
    }
  }

  async function cancel() {
    if (!state.activeRun) return;
    try { await dataAnalystClient.cancelRun(state.activeRun.id); } finally { dispatch({ type: "cancelled", runId: state.activeRun.id }); }
  }

  return <PageShell title="Data Analyst Studio" eyebrow="Evidence-first analytics" description="Profile the dataset, inspect the chosen methods, and trace every published number to deterministic computation evidence." maxWidth="full" actions={<div className="flex gap-2"><Button asChild variant="outline"><Link href="/analysis/history"><History className="mr-2 h-4 w-4" />Run history</Link></Button>{state.activeRun && ["queued", "running"].includes(state.activeRun.state) ? <Button onClick={cancel} variant="destructive">Cancel run</Button> : null}</div>}>
    <div className="mb-5 grid gap-5 lg:grid-cols-[0.75fr_1.25fr]">
      <StudioPanel title="Start a governed analysis" description="CSV snapshots are immutable. Questions should name the decision or relationship you need to understand.">
        <label className="group flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-border bg-muted/20 p-4 hover:border-primary/40">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-background"><Upload className="h-4 w-4" /></span><span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{file?.name ?? "Choose a CSV dataset"}</span><span className="text-xs text-muted-foreground">UTF-8 CSV · maximum limits are enforced by the server</span></span><input className="sr-only" type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <Textarea className="mt-3 min-h-24 resize-none" aria-label="Analysis question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Which factors are associated with higher customer retention, and how stable is the evidence?" />
        {state.error ? <p className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-xs text-destructive">{state.error}</p> : null}
        <Button className="mt-3 w-full" disabled={!file || question.trim().length < 3 || state.loading} onClick={start}>{state.loading ? <><span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />Running verified workflow</> : <><Play className="mr-2 h-4 w-4" />Profile and analyze</>}</Button>
      </StudioPanel>
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Run contract</p><h2 className="mt-1 text-lg font-semibold">Reproducible by construction</h2></div>{state.activeRun ? <StatusPill state={state.activeRun.state} /> : <BarChart3 className="h-5 w-5 text-[hsl(var(--data))]" />}</div><div className="mt-5 grid gap-3 sm:grid-cols-3">{[["Profile", "Types, missingness, identifiers, sensitive fields"], ["Compute", "Registered methods, assumptions, versions, digests"], ["Verify", "Evidence-linked claims, limitations, no false causality"]].map(([title, body], index) => <div className="rounded-lg border border-border bg-muted/20 p-4" key={title}><span className="font-mono text-[10px] text-muted-foreground">0{index + 1}</span><p className="mt-2 text-xs font-semibold">{title}</p><p className="mt-1 text-[11px] leading-5 text-muted-foreground">{body}</p></div>)}</div></div>
    </div>
    <DataAnalystWorkspace profile={state.profile} run={state.activeRun} plan={plan} computations={computations} findings={findings} limitations={limitations} />
  </PageShell>;
}

function normalizeProfile(profile: NormalizableDatasetProfile): DatasetProfile {
  return {
    ...profile,
    warnings: profile.warnings ?? [],
    columns: profile.columns.map((column) => ({
      ...column,
      inferred_type: column.inferred_type ?? column.semantic_type ?? column.dtype ?? "unknown",
    })),
  };
}

function normalizePlan(value: NormalizablePlan | undefined, state: StudioRunState): PlanStep[] {
  const steps = Array.isArray(value) ? value : value?.steps ?? [];
  return steps.map((step) => ({
    id: step.id,
    method_id: step.method_id,
    title: step.title ?? step.rationale ?? step.method_id,
    state: step.state ?? (state === "succeeded" ? "completed" : "pending"),
    assumptions: step.assumptions ?? [],
    depends_on: step.depends_on ?? step.prerequisite_step_ids ?? [],
  }));
}
