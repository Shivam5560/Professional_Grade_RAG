'use client';
import { WorkflowEvent } from '@/lib/analysis/types';
import { AlertTriangle, CheckCircle2, Download, FileText, Sparkles, Activity, Timer, Workflow } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { useAnalysisStore } from '@/lib/analysis/store';
import { ANALYSIS_STEPS } from './AnalysisStepper';

const STEP_LABELS: Record<string, string> = {
  build_context: 'Building dataset context',
  decompose: 'Decomposing query into tasks',
  plan_strategy: 'Planning analysis strategy',
  dispatch_execution: 'Running analysis agents',
  prioritize_insights: 'Prioritizing insights',
  generate_narrative: 'Generating narrative',
  design: 'Designing report layout',
  compose: 'Composing final report',
};

interface Props {
  events: WorkflowEvent[];
  jobId: string;
}

function eventSummary(ev: WorkflowEvent): string {
  const p = ev.payload;
  const status = p.status as string;
  if (status === 'started') return 'Started';
  if (status === 'completed') {
    if (p.tasks !== undefined) return `${(p.tasks as unknown[]).length} tasks created`;
    if (p.invocations !== undefined) return `${(p.invocations as unknown[]).length} agents planned`;
    if (p.results !== undefined) return `${(p.results as unknown[]).length} agents completed`;
    if (p.insights !== undefined) return `${(p.insights as unknown[]).length} insights`;
    if (p.summary !== undefined) return 'Summary ready';
    if (p.theme !== undefined) return `Theme: ${p.theme}, ${p.charts} charts`;
    return 'Completed';
  }
  if (status === 'timeout') return `Timed out: ${(p.error as string)?.slice(0, 60)}`;
  if (status === 'error') return `Error: ${(p.error as string)?.slice(0, 80)}`;
  return '';
}

export function LivePreview({ events, jobId }: Props) {
  const { jobStatus } = useAnalysisStore();
  const isComplete = jobStatus === 'completed';
  const latestByStep = new Map<string, WorkflowEvent>();
  events.forEach((event) => latestByStep.set(event.step_name, event));
  const completedCount = isComplete
    ? ANALYSIS_STEPS.length
    : ANALYSIS_STEPS.filter((step) => latestByStep.get(step.key)?.payload.status === 'completed').length;
  const failedCount = ANALYSIS_STEPS.filter((step) => {
    const status = latestByStep.get(step.key)?.payload.status;
    return status === 'error' || status === 'timeout';
  }).length;
  const activeEvent = [...events].reverse().find((event) => {
    const status = event.payload.status;
    return status === 'started' && latestByStep.get(event.step_name)?.payload.status !== 'completed';
  }) || events[events.length - 1];
  const progress = isComplete ? 100 : Math.round((completedCount / ANALYSIS_STEPS.length) * 100);
  const activeLabel = activeEvent ? STEP_LABELS[activeEvent.step_name] || activeEvent.step_name : 'Waiting for analysis';
  const activeStep = ANALYSIS_STEPS.find((step) => step.key === activeEvent?.step_name);
  const activeSummary = activeEvent ? eventSummary(activeEvent) : 'Preparing the analysis workspace';

  return (
    <div className="flex h-full flex-col rounded-lg border bg-card p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Activity className="h-4 w-4 text-primary" />
            Live Workspace
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">{activeLabel}</p>
        </div>
        <div className="rounded-md border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">
          {progress}%
        </div>
      </div>

      <div className="mb-4 h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>

      <div className="mb-5 grid grid-cols-3 gap-2">
        <div className="rounded-md border bg-background p-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            Done
          </div>
          <p className="mt-1 text-lg font-semibold">{completedCount}</p>
        </div>
        <div className="rounded-md border bg-background p-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Workflow className="h-3.5 w-3.5 text-primary" />
            Stages
          </div>
          <p className="mt-1 text-lg font-semibold">{ANALYSIS_STEPS.length}</p>
        </div>
        <div className="rounded-md border bg-background p-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
            Issues
          </div>
          <p className="mt-1 text-lg font-semibold">{failedCount}</p>
        </div>
      </div>

      <div className="mb-5 rounded-lg border bg-background p-4">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-primary/10 p-2 text-primary">
            <Timer className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium">{activeStep?.label || 'Queued'}</p>
            <p className="mt-1 text-sm text-muted-foreground">{activeStep?.detail || activeSummary}</p>
            {activeSummary && activeSummary !== 'Started' && (
              <p className="mt-2 text-xs text-muted-foreground">{activeSummary}</p>
            )}
          </div>
        </div>
      </div>

      {!isComplete && events.length > 0 && (
        <div className="min-h-0 flex-1 flex items-center justify-center">
          <div className="text-center space-y-2 py-4">
            <div className="mx-auto h-8 w-8 animate-pulse rounded-full bg-primary/10 flex items-center justify-center">
              <Activity className="h-4 w-4 text-primary" />
            </div>
            <p className="text-sm font-medium">{completedCount} of {ANALYSIS_STEPS.length} stages complete</p>
            <p className="text-xs text-muted-foreground">Analysis is running — results will appear when ready</p>
          </div>
        </div>
      )}

      {events.length === 0 && !isComplete && (
        <div className="min-h-0 flex-1 flex items-center justify-center">
          <div className="rounded-md border border-dashed bg-background p-6 text-center">
            <Timer className="mx-auto h-6 w-6 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Waiting for analysis to begin...</p>
          </div>
        </div>
      )}

      {isComplete && events.length > 0 && (
        <div className="mt-4 pt-4 border-t space-y-2">
          <div className="flex items-center gap-1.5 text-emerald-600 text-sm font-medium">
            <Sparkles className="h-4 w-4" />
            Analysis Complete
          </div>
          <div className="flex gap-2">
            <Link href={`/analysis/${jobId}/report`} className="flex-1">
              <button className="w-full inline-flex items-center justify-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                <FileText className="h-4 w-4" />
                View Report
              </button>
            </Link>
            <button
              onClick={() => apiClient.downloadAnalysisReport(jobId)}
              className="w-full inline-flex items-center justify-center gap-1.5 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium hover:bg-accent"
            >
              <Download className="h-4 w-4" />
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
