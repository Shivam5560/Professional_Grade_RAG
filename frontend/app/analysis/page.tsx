"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { BarChart3, FileSpreadsheet, RotateCcw, Settings2, StopCircle } from "lucide-react";
import { useReducer, useState } from "react";

import { AnalysisRunCanvas } from "@/components/analysis/AnalysisRunCanvas";
import { FileDropzone } from "@/components/analysis/FileDropzone";
import { ActionDock } from "@/components/shell/ActionDock";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Inspector } from "@/components/shell/Inspector";
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
  const [guardrailsOpen, setGuardrailsOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const hasRun = Boolean(state.activeRun);

  async function start() {
    if (!file || question.trim().length < 3) return;
    dispatch({ type: "loading" });
    try {
      const snapshot = await dataAnalystClient.createDataset(file);
      dispatch({ type: "profile-loaded", profile: normalizeProfile(snapshot.profile) });
      const response = await dataAnalystClient.createRun(
        { snapshot_id: snapshot.snapshot_id, question: question.trim() },
        crypto.randomUUID(),
      );
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
    try {
      await dataAnalystClient.cancelRun(state.activeRun.id);
    } finally {
      dispatch({ type: "cancelled", runId: state.activeRun.id });
    }
  }

  function resetBrief() {
    setFile(null);
    setQuestion("");
    setPlan([]);
    setComputations([]);
    setFindings([]);
    setLimitations([]);
    window.location.assign("/analysis");
  }

  return (
    <FocusCanvas ariaLabel="Analysis workspace">
      <CanvasHeader
        actions={
          !hasRun ? (
            <Button onClick={() => setGuardrailsOpen(true)} size="sm" variant="outline">
              <Settings2 aria-hidden="true" className="mr-2 h-4 w-4" />
              Method guardrails
            </Button>
          ) : undefined
        }
        description={hasRun ? state.activeRun?.question : "Bring one dataset and one decision. The studio profiles, computes, and verifies every published signal."}
        eyebrow="Data Analyst Studio"
        status={hasRun ? <span className="text-[11px] font-medium text-[hsl(var(--data))]">Live workspace</span> : undefined}
        title={hasRun ? "Analysis in motion" : "See the signal inside the noise."}
      />

      <ContextRibbon label="Analysis context">
        <ContextItem icon={<FileSpreadsheet className="h-3.5 w-3.5" />} label={file?.name ?? (hasRun ? "Immutable snapshot" : "No dataset selected")} />
        <ContextItem icon={<BarChart3 className="h-3.5 w-3.5" />} label="Evidence-linked output" />
        <ContextItem label="No causal overclaiming" />
      </ContextRibbon>

      <AnimatePresence mode="wait">
        {!hasRun ? (
          <motion.section
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto flex w-full max-w-4xl flex-1 items-center py-8 sm:py-12 lg:py-16"
            exit={{ opacity: 0, y: reduceMotion ? 0 : -12 }}
            initial={{ opacity: 0, y: reduceMotion ? 0 : 16 }}
            key="brief"
            transition={reduceMotion ? { duration: 0 } : { duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="w-full border-y border-border/70 bg-background/62 px-5 py-6 backdrop-blur-xl sm:px-8 sm:py-9">
              <div className="grid gap-7 lg:grid-cols-[minmax(0,0.78fr)_minmax(0,1.22fr)] lg:gap-10">
                <div>
                  <p className="text-[11px] font-semibold uppercase text-muted-foreground">01 · Dataset</p>
                  <h2 className="mt-2 text-xl font-semibold">Choose the evidence.</h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">A snapshot is created before analysis so results remain reproducible.</p>
                  <div className="mt-5">
                    <FileDropzone onFileSelect={setFile} selectedFile={file} />
                  </div>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase text-muted-foreground">02 · Objective</p>
                  <label className="mt-2 block text-xl font-semibold" htmlFor="analysis-question">Name the decision.</label>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">Ask for a relationship, comparison, trend, or forecast that can be tested against the data.</p>
                  <Textarea
                    aria-label="Analysis question"
                    className="mt-5 min-h-40 resize-none border-border/80 bg-background/75 text-base leading-7 shadow-none focus-visible:ring-[hsl(var(--data))]"
                    id="analysis-question"
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Which factors are associated with higher customer retention, and how stable is the evidence?"
                    value={question}
                  />
                </div>
              </div>
              {state.error ? <p className="mt-6 border-l-2 border-destructive bg-destructive/5 px-4 py-3 text-sm text-destructive" role="alert">{state.error}</p> : null}
            </div>
          </motion.section>
        ) : (
          <motion.div animate={{ opacity: 1 }} initial={{ opacity: 0 }} key="run">
            <AnalysisRunCanvas
              computations={computations}
              findings={findings}
              limitations={limitations}
              plan={plan}
              profile={state.profile}
              recoveryAction={<Button onClick={resetBrief} variant="outline"><RotateCcw aria-hidden="true" className="mr-2 h-4 w-4" />New brief</Button>}
              run={state.activeRun}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {!hasRun ? (
        <ActionDock
          primary={<Button disabled={!file || question.trim().length < 3 || state.loading} onClick={start}>{state.loading ? "Preparing analysis…" : "Profile and analyze"}</Button>}
          secondary={<span className="hidden text-xs text-muted-foreground sm:inline">CSV snapshot · verified methods</span>}
        />
      ) : state.activeRun && ["queued", "running"].includes(state.activeRun.state) ? (
        <ActionDock primary={<Button onClick={cancel} variant="destructive"><StopCircle aria-hidden="true" className="mr-2 h-4 w-4" />Cancel run</Button>} />
      ) : null}

      <Inspector open={guardrailsOpen} onOpenChange={setGuardrailsOpen} title="Method guardrails">
        <div className="space-y-7">
          {[
            ["Profile before compute", "Types, missingness, identifiers, and sensitive fields are inspected before a method can run."],
            ["Registered methods only", "Every computation records its method version, assumptions, parameters, and evidence identifier."],
            ["Verified language", "Claims distinguish observations, associations, predictions, and hypotheses. Association is never presented as causation."],
          ].map(([title, body], index) => (
            <section className="grid grid-cols-[2rem_minmax(0,1fr)] gap-3 border-b border-border pb-6" key={title}>
              <span className="font-mono text-[10px] text-[hsl(var(--data))]">0{index + 1}</span>
              <div><h2 className="text-sm font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p></div>
            </section>
          ))}
        </div>
      </Inspector>
    </FocusCanvas>
  );
}

function ContextItem({ icon, label }: { icon?: React.ReactNode; label: string }) {
  return <span className="inline-flex h-8 items-center gap-2 border border-border/70 bg-background/65 px-3 text-xs text-muted-foreground">{icon}{label}</span>;
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
