"use client";

import { RotateCcw, StopCircle } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AnalysisRunCanvas } from "@/components/analysis/AnalysisRunCanvas";
import { ActionDock } from "@/components/shell/ActionDock";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Button } from "@/components/ui/button";
import { dataAnalystClient } from "@/lib/studios/data-analyst/client";
import type { Computation, DatasetProfile, Finding, PlanStep, StudioRun } from "@/lib/studios/data-analyst/types";

type NormalizablePlanStep = Omit<PlanStep, "title" | "state" | "depends_on"> & {
  title?: string;
  state?: PlanStep["state"];
  depends_on?: string[];
  rationale?: string;
  prerequisite_step_ids?: string[];
};

type NormalizablePlan = { steps?: NormalizablePlanStep[] } | NormalizablePlanStep[];

interface AnalysisRunModel {
  run: StudioRun | null;
  profile: DatasetProfile | null;
  plan: PlanStep[];
  computations: Computation[];
  findings: Finding[];
  limitations: string[];
  error: string | null;
}

const initialModel: AnalysisRunModel = { run: null, profile: null, plan: [], computations: [], findings: [], limitations: [], error: null };

export default function AnalysisRunPage() {
  const { jobId } = useParams() as { jobId: string };
  const [model, setModel] = useState<AnalysisRunModel>(initialModel);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function load() {
      try {
        const response = await dataAnalystClient.getRun(jobId);
        const steps = normalizePlan(response.plan, response.run.state);
        const [computations, findings, report] = await Promise.all([
          dataAnalystClient.getComputations(jobId),
          dataAnalystClient.getClaims(jobId),
          dataAnalystClient.getReport(jobId).catch(() => ({ limitations: [] })),
        ]);
        if (active) {
          setModel({ run: response.run, profile: response.profile ?? null, plan: steps, computations, findings, limitations: report.limitations ?? [], error: null });
          if (["queued", "running"].includes(response.run.state)) timer = setTimeout(() => void load(), 4000);
        }
      } catch (reason) {
        if (active) setModel((current) => ({ ...current, error: reason instanceof Error ? reason.message : "Unable to load run" }));
      }
    }

    void load();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [jobId]);

  async function cancel() {
    await dataAnalystClient.cancelRun(jobId);
    setModel((current) => current.run ? { ...current, run: { ...current.run, state: "cancelled" } } : current);
  }

  return (
    <FocusCanvas ariaLabel="Analysis run">
      <CanvasHeader
        description={model.run?.question ?? "Follow the current verified phase without losing the decision context."}
        eyebrow="Data Analyst Studio"
        status={<span className="font-mono text-[10px] text-muted-foreground">{jobId}</span>}
        title="Live analysis"
      />
      <ContextRibbon label="Run context">
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">Immutable snapshot</span>
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">Evidence-linked methods</span>
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">Auto-refresh · 4s</span>
      </ContextRibbon>

      {model.error ? (
        <section className="mx-auto flex min-h-[50svh] max-w-2xl items-center justify-center text-center">
          <div><p className="text-sm text-destructive" role="alert">{model.error}</p><Button asChild className="mt-5" variant="outline"><Link href="/analysis"><RotateCcw aria-hidden="true" className="mr-2 h-4 w-4" />Start a new analysis</Link></Button></div>
        </section>
      ) : (
        <AnalysisRunCanvas
          computations={model.computations}
          findings={model.findings}
          limitations={model.limitations}
          plan={model.plan}
          profile={model.profile}
          recoveryAction={<Button asChild variant="outline"><Link href="/analysis"><RotateCcw aria-hidden="true" className="mr-2 h-4 w-4" />New brief</Link></Button>}
          run={model.run}
        />
      )}

      {model.run && ["queued", "running"].includes(model.run.state) ? (
        <ActionDock primary={<Button onClick={cancel} variant="destructive"><StopCircle aria-hidden="true" className="mr-2 h-4 w-4" />Cancel run</Button>} />
      ) : null}
    </FocusCanvas>
  );
}

function normalizePlan(value: NormalizablePlan | undefined, runState: StudioRun["state"]): PlanStep[] {
  const steps = Array.isArray(value) ? value : value?.steps ?? [];
  return steps.map((step) => ({
    id: step.id,
    method_id: step.method_id,
    title: step.title ?? step.rationale ?? step.method_id,
    state: step.state ?? (runState === "succeeded" ? "completed" : "pending"),
    assumptions: step.assumptions ?? [],
    depends_on: step.depends_on ?? step.prerequisite_step_ids ?? [],
  }));
}
