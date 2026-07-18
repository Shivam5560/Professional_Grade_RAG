"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  Braces,
  CheckCircle2,
  CircleDashed,
  FileSearch,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";

import { Inspector } from "@/components/shell/Inspector";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  Computation,
  DatasetProfile,
  Finding,
  PlanStep,
  StudioRun,
} from "@/lib/studios/data-analyst/types";
import { cn } from "@/lib/utils";

interface AnalysisRunCanvasProps {
  profile: DatasetProfile | null;
  run: StudioRun | null;
  plan: PlanStep[];
  computations: Computation[];
  findings: Finding[];
  limitations: string[];
  recoveryAction?: ReactNode;
}

const terminalStates = new Set<StudioRun["state"]>([
  "succeeded",
  "failed",
  "cancelled",
]);

export function AnalysisRunCanvas({
  profile,
  run,
  plan,
  computations,
  findings,
  limitations,
  recoveryAction,
}: AnalysisRunCanvasProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const reduceMotion = useReducedMotion();

  if (!run) {
    return <RunWaitingState />;
  }

  const runningStep = plan.find((step) => step.state === "running");
  const pendingStep = plan.find((step) => step.state === "pending");
  const lastComplete = [...plan].reverse().find((step) => step.state === "completed");
  const currentStep = runningStep ?? pendingStep ?? lastComplete;
  const progress = Math.max(0, Math.min(100, Math.round(run.progress * 100)));
  const isComplete = run.state === "succeeded";
  const hasStopped = terminalStates.has(run.state);
  const headline = isComplete
    ? "Your verified analysis is ready."
    : run.state === "failed"
      ? "The run needs attention."
      : run.state === "cancelled"
        ? "This run was cancelled."
        : currentStep?.title ?? "Preparing the analysis plan";
  const detail = isComplete
    ? `${findings.length} evidence-linked ${findings.length === 1 ? "finding" : "findings"} passed verification.`
    : run.state === "failed"
      ? run.failure_code ?? "The run stopped before a verified report could be produced."
      : run.state === "cancelled"
        ? "No further methods will execute. You can return to the brief and launch a new run."
        : currentStep
          ? `Running ${currentStep.method_id.replaceAll("_", " ")} under the registered method contract.`
          : "The dataset profile is complete. The method planner is selecting reproducible steps.";

  return (
    <>
      <section className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center py-8 sm:py-12 lg:py-16">
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden border-y border-border/70 bg-background/64 px-5 py-8 backdrop-blur-xl sm:px-8 sm:py-10 lg:px-12 lg:py-14"
          initial={{ opacity: 0, y: reduceMotion ? 0 : 18 }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <div aria-hidden="true" className="absolute inset-y-0 left-0 w-1 bg-[hsl(var(--data))]" />
          <div className="flex flex-col gap-10 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <div className="flex flex-wrap items-center gap-2">
                <RunState state={run.state} />
                <span className="font-mono text-[10px] text-muted-foreground">{run.id}</span>
              </div>
              <p className="mt-8 text-[11px] font-semibold uppercase text-muted-foreground">
                {isComplete ? "Verified outcome" : hasStopped ? "Recovery state" : "Current phase"}
              </p>
              <h2 className="mt-2 text-balance text-2xl font-semibold leading-tight sm:text-4xl">
                {headline}
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
                {detail}
              </p>
            </div>

            <div className="w-full max-w-sm shrink-0">
              <div className="mb-2 flex items-end justify-between gap-4">
                <span className="text-xs text-muted-foreground">Verified workflow</span>
                <span className="font-mono text-2xl font-semibold">{progress}%</span>
              </div>
              <div className="h-1 overflow-hidden bg-muted" aria-label={`${progress}% complete`} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
                <motion.div
                  animate={{ width: `${Math.max(progress, hasStopped ? 0 : 2)}%` }}
                  className={cn(
                    "h-full",
                    run.state === "failed" ? "bg-destructive" : "bg-[hsl(var(--data))]",
                  )}
                  initial={false}
                  transition={reduceMotion ? { duration: 0 } : { duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                <Button onClick={() => setDetailsOpen(true)} variant="outline">
                  <FileSearch aria-hidden="true" className="mr-2 h-4 w-4" />
                  Inspect run details
                </Button>
                {isComplete ? (
                  <Button asChild>
                    <Link href={`/analysis/${run.id}/report`}>
                      Open report
                      <ArrowRight aria-hidden="true" className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                ) : null}
                {hasStopped && !isComplete ? recoveryAction : null}
              </div>
            </div>
          </div>
        </motion.div>

        {isComplete && findings.length > 0 ? (
          <div className="mt-8">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h3 className="text-sm font-semibold">Strongest verified signals</h3>
              <span className="text-xs text-muted-foreground">Evidence linked</span>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {findings.slice(0, 3).map((finding, index) => (
                <motion.article
                  animate={{ opacity: 1, y: 0 }}
                  className="border-l border-border bg-background/52 px-4 py-3 backdrop-blur-md"
                  initial={{ opacity: 0, y: reduceMotion ? 0 : 10 }}
                  key={finding.id}
                  transition={reduceMotion ? { duration: 0 } : { delay: index * 0.06, duration: 0.32 }}
                >
                  <div className="flex items-center justify-between gap-3 text-[10px] font-semibold uppercase text-muted-foreground">
                    <span>{finding.language_class}</span>
                    <span>{Math.round(finding.confidence * 100)}%</span>
                  </div>
                  <p className="mt-2 text-sm leading-6">{finding.statement}</p>
                </motion.article>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <Inspector open={detailsOpen} onOpenChange={setDetailsOpen} title="Run details">
        <Tabs defaultValue="dataset">
          <TabsList className="grid h-auto w-full grid-cols-4">
            <TabsTrigger className="px-2 text-xs" value="dataset">Dataset</TabsTrigger>
            <TabsTrigger className="px-2 text-xs" value="methods">Methods</TabsTrigger>
            <TabsTrigger className="px-2 text-xs" value="evidence">Evidence</TabsTrigger>
            <TabsTrigger className="px-2 text-xs" value="limits">Limits</TabsTrigger>
          </TabsList>
          <TabsContent className="pt-4" value="dataset">
            <DatasetDetails profile={profile} />
          </TabsContent>
          <TabsContent className="pt-4" value="methods">
            <MethodDetails plan={plan} computations={computations} />
          </TabsContent>
          <TabsContent className="pt-4" value="evidence">
            <EvidenceDetails findings={findings} />
          </TabsContent>
          <TabsContent className="pt-4" value="limits">
            <LimitDetails limitations={limitations} profile={profile} />
          </TabsContent>
        </Tabs>
      </Inspector>
    </>
  );
}

function RunWaitingState() {
  return (
    <section className="mx-auto flex min-h-[52svh] w-full max-w-4xl items-center justify-center py-12 text-center">
      <div>
        <CircleDashed aria-hidden="true" className="mx-auto h-6 w-6 animate-spin text-[hsl(var(--data))]" />
        <h2 className="mt-5 text-xl font-semibold">Preparing the run</h2>
        <p className="mt-2 text-sm text-muted-foreground">The first verified phase will appear here.</p>
      </div>
    </section>
  );
}

function RunState({ state }: { state: StudioRun["state"] }) {
  const complete = state === "succeeded";
  const failed = state === "failed";
  const Icon = complete ? CheckCircle2 : failed ? AlertTriangle : CircleDashed;
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 border px-2.5 py-1 text-[11px] font-semibold capitalize",
      complete && "border-emerald-500/30 bg-emerald-500/10 text-emerald-600",
      failed && "border-destructive/30 bg-destructive/10 text-destructive",
      !complete && !failed && "border-[hsl(var(--data)/0.3)] bg-[hsl(var(--data)/0.08)] text-[hsl(var(--data))]",
    )}>
      <Icon aria-hidden="true" className={cn("h-3 w-3", !terminalStates.has(state) && "animate-spin")} />
      {state.replaceAll("_", " ")}
    </span>
  );
}

function DatasetDetails({ profile }: { profile: DatasetProfile | null }) {
  if (!profile) return <EmptyDetails label="Dataset profile is not available yet." />;
  return (
    <div>
      <div className="grid grid-cols-2 gap-px overflow-hidden border bg-border">
        <Metric label="Rows" value={profile.row_count.toLocaleString()} />
        <Metric label="Columns" value={profile.column_count.toLocaleString()} />
      </div>
      <h3 className="mt-6 text-xs font-semibold uppercase text-muted-foreground">Dataset columns</h3>
      <div className="mt-2 divide-y divide-border border-y border-border">
        {profile.columns.map((column) => (
          <div className="flex items-center justify-between gap-4 py-3" key={column.name}>
            <div className="min-w-0">
              <p className="truncate font-mono text-xs">{column.name}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">{column.missing_count} missing · {column.unique_count.toLocaleString()} unique</p>
            </div>
            <span className="shrink-0 text-[10px] font-semibold uppercase text-muted-foreground">{column.inferred_type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MethodDetails({ plan, computations }: { plan: PlanStep[]; computations: Computation[] }) {
  if (!plan.length) return <EmptyDetails label="The method plan is still being prepared." />;
  return (
    <div className="space-y-5">
      <ol className="divide-y divide-border border-y border-border">
        {plan.map((step, index) => (
          <li className="flex gap-3 py-3" key={step.id}>
            <span className="font-mono text-[10px] text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
            <div className="min-w-0">
              <p className="text-sm font-medium">{step.title}</p>
              <p className="mt-1 font-mono text-[10px] text-muted-foreground">{step.method_id} · {step.state}</p>
              {step.assumptions.length ? <p className="mt-2 text-xs text-muted-foreground">Assumes {step.assumptions.join(", ")}</p> : null}
            </div>
          </li>
        ))}
      </ol>
      {computations.map((computation) => (
        <article className="border-b border-border pb-5" key={computation.id}>
          <div className="flex items-center gap-2">
            <Braces aria-hidden="true" className="h-4 w-4 text-[hsl(var(--data))]" />
            <h3 className="font-mono text-xs font-semibold">{computation.method_id}</h3>
          </div>
          <dl className="mt-3 grid grid-cols-2 gap-2">
            {Object.entries(computation.metrics).map(([key, value]) => (
              <div className="bg-muted/50 p-2.5" key={key}>
                <dt className="text-[10px] text-muted-foreground">{key.replaceAll("_", " ")}</dt>
                <dd className="mt-1 font-mono text-xs">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </article>
      ))}
    </div>
  );
}

function EvidenceDetails({ findings }: { findings: Finding[] }) {
  if (!findings.length) return <EmptyDetails label="Verified evidence will appear after methods complete." />;
  return (
    <div className="divide-y divide-border border-y border-border">
      {findings.map((finding) => (
        <article className="py-4" key={finding.id}>
          <div className="flex justify-between gap-3 text-[10px] font-semibold uppercase text-muted-foreground">
            <span>{finding.language_class}</span><span>{Math.round(finding.confidence * 100)}% confidence</span>
          </div>
          <p className="mt-2 text-sm leading-6">{finding.statement}</p>
          <p className="mt-2 font-mono text-[10px] text-[hsl(var(--data))]">{finding.evidence_ids.join(" · ")}</p>
        </article>
      ))}
    </div>
  );
}

function LimitDetails({ limitations, profile }: { limitations: string[]; profile: DatasetProfile | null }) {
  const items = [...(profile?.warnings ?? []), ...limitations];
  if (!items.length) return <EmptyDetails label="No limitations have been published for this run." />;
  return (
    <ul className="divide-y divide-border border-y border-border">
      {items.map((item) => (
        <li className="flex gap-3 py-4 text-sm leading-6 text-muted-foreground" key={item}>
          <ShieldCheck aria-hidden="true" className="mt-1 h-4 w-4 shrink-0 text-amber-500" />{item}
        </li>
      ))}
    </ul>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="bg-background p-4"><dt className="text-[10px] font-semibold uppercase text-muted-foreground">{label}</dt><dd className="mt-1 text-2xl font-semibold">{value}</dd></div>;
}

function EmptyDetails({ label }: { label: string }) {
  return <p className="border-y border-dashed border-border py-8 text-center text-sm text-muted-foreground">{label}</p>;
}
