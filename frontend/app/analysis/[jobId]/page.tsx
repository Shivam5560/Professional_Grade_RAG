"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/PageShell";
import { DataAnalystWorkspace } from "@/components/studios/data-analyst/DataAnalystWorkspace";
import { Button } from "@/components/ui/button";
import { dataAnalystClient } from "@/lib/studios/data-analyst/client";
import type { Computation, DatasetProfile, Finding, PlanStep, StudioRun } from "@/lib/studios/data-analyst/types";

export default function AnalysisRunPage() {
  const { jobId } = useParams() as { jobId: string };
  const [model, setModel] = useState<{ run: StudioRun | null; profile: DatasetProfile | null; plan: PlanStep[]; computations: Computation[]; findings: Finding[]; limitations: string[]; error: string | null }>({ run: null, profile: null, plan: [], computations: [], findings: [], limitations: [], error: null });
  useEffect(() => { let active = true; async function load() { try { const response = await dataAnalystClient.getRun(jobId); const planValue: any = response.plan; const steps = (Array.isArray(planValue) ? planValue : planValue?.steps ?? []).map((step: any) => ({ ...step, title: step.title ?? step.rationale ?? step.method_id, state: step.state ?? (response.run.state === "succeeded" ? "completed" : "pending"), depends_on: step.prerequisite_step_ids ?? [] })); const [computations, findings, report] = await Promise.all([dataAnalystClient.getComputations(jobId), dataAnalystClient.getClaims(jobId), dataAnalystClient.getReport(jobId).catch(() => ({ limitations: [] }))]); if (active) setModel({ run: response.run, profile: response.profile ?? null, plan: steps, computations, findings, limitations: report.limitations ?? [], error: null }); } catch (reason) { if (active) setModel((current) => ({ ...current, error: reason instanceof Error ? reason.message : "Unable to load run" })); } } void load(); const timer = setInterval(() => { if (!model.run || ["queued", "running"].includes(model.run.state)) void load(); }, 4000); return () => { active = false; clearInterval(timer); }; }, [jobId]);
  return <PageShell title="Analysis run" eyebrow="Data Analyst Studio" description={jobId} maxWidth="full" actions={model.run && ["queued", "running"].includes(model.run.state) ? <Button variant="destructive" onClick={async () => { await dataAnalystClient.cancelRun(jobId); setModel((current) => current.run ? { ...current, run: { ...current.run, state: "cancelled" } } : current); }}>Cancel run</Button> : undefined}>{model.error ? <p className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{model.error}</p> : <DataAnalystWorkspace profile={model.profile} run={model.run} plan={model.plan} computations={model.computations} findings={model.findings} limitations={model.limitations} />}</PageShell>;
}
