'use client';
import { WorkflowEvent } from '@/lib/analysis/types';
import { CheckCircle2, Loader2, XCircle, Download, FileText, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import { useAnalysisStore } from '@/lib/analysis/store';

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

  return (
    <div className="border rounded-lg p-4 h-full flex flex-col">
      <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-primary" />
        Live Progress
      </h3>

      <div className="flex-1 overflow-y-auto space-y-1.5 min-h-0">
        {events.length === 0 && !isComplete && (
          <p className="text-sm text-muted-foreground">Waiting for analysis to begin...</p>
        )}

        {events.map((ev, idx) => {
          const status = ev.payload.status as string;
          const label = STEP_LABELS[ev.step_name] || ev.step_name;
          const summary = eventSummary(ev);

          return (
            <div key={idx} className="flex items-start gap-2 py-1">
              {status === 'completed' ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-green-500 mt-0.5 shrink-0" />
              ) : status === 'error' || status === 'timeout' ? (
                <XCircle className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" />
              ) : status === 'started' ? (
                <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin mt-0.5 shrink-0" />
              ) : (
                <div className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-xs font-medium truncate">{label}</p>
                {summary && (
                  <p className={`text-xs truncate ${
                    status === 'error' || status === 'timeout' ? 'text-red-500' : 'text-muted-foreground'
                  }`}>
                    {summary}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {isComplete && events.length > 0 && (
        <div className="mt-4 pt-4 border-t space-y-2">
          <div className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
            <CheckCircle2 className="h-4 w-4" />
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

      {events.length === 0 && (
        <div className="text-xs text-muted-foreground space-y-1 mt-1">
          {Object.entries(STEP_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-muted" />
              <span>{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
