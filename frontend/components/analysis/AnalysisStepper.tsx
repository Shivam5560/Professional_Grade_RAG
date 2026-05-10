// frontend/components/analysis/AnalysisStepper.tsx
'use client';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';

export const ANALYSIS_STEPS = [
  { key: 'build_context', label: 'Dataset Context', detail: 'Profiling rows, columns, and quality' },
  { key: 'decompose', label: 'Task Decomposition', detail: 'Breaking the request into analysis work' },
  { key: 'plan_strategy', label: 'Agent Strategy', detail: 'Choosing statistical and narrative agents' },
  { key: 'dispatch_execution', label: 'Analysis Execution', detail: 'Running the analytical passes' },
  { key: 'prioritize_insights', label: 'Insight Ranking', detail: 'Selecting the strongest findings' },
  { key: 'generate_narrative', label: 'Narrative', detail: 'Writing the analytical storyline' },
  { key: 'design', label: 'Visual Direction', detail: 'Choosing theme, charts, and deck style' },
  { key: 'compose', label: 'Report Assembly', detail: 'Building report, charts, and slides' },
];

interface Props {
  currentStep: number;
  status: string;
  failedSteps?: Set<string>;
  completedSteps?: Set<string>;
}

export function AnalysisStepper({ currentStep, status, failedSteps = new Set(), completedSteps = new Set() }: Props) {
  return (
    <div className="space-y-2">
      {ANALYSIS_STEPS.map((step, idx) => {
        const failed = failedSteps.has(step.key);
        const completed = completedSteps.has(step.key) || idx < currentStep || status === 'completed';
        const active = idx === currentStep && status !== 'completed' && !failed;

        return (
        <div
          key={step.key}
          className={`rounded-md border px-3 py-2 transition-colors ${
            active ? 'border-primary/40 bg-primary/5' : completed ? 'border-emerald-500/20 bg-emerald-500/5' : failed ? 'border-destructive/30 bg-destructive/5' : 'border-border bg-background'
          }`}
        >
          <div className="flex items-start gap-2.5">
            {failed ? (
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            ) : completed ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
            ) : active ? (
              <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-primary" />
            ) : (
              <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground/60" />
            )}
            <div className="min-w-0">
              <p className={`text-sm font-medium ${active ? 'text-foreground' : 'text-muted-foreground'}`}>{step.label}</p>
              <p className="text-xs text-muted-foreground">{step.detail}</p>
            </div>
          </div>
        </div>
        );
      })}
    </div>
  );
}
