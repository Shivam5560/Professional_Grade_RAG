// frontend/app/analysis/[jobId]/page.tsx
'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { useAnalysisStore } from '@/lib/analysis/store';
import { useAnalysisSocket } from '@/lib/analysis/useAnalysisSocket';
import { AnalysisStepper } from '@/components/analysis/AnalysisStepper';
import { LivePreview } from '@/components/analysis/LivePreview';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { BarChart3, Clock3, ShieldCheck } from 'lucide-react';

export default function AnalysisProgressPage() {
  const { jobId } = useParams() as { jobId: string };
  const { progressEvents, jobStatus, reset } = useAnalysisStore();
  const [currentStep, setCurrentStep] = useState(0);

  useAnalysisSocket(jobId);

  useEffect(() => {
    if (progressEvents.length > 0) {
      const last = progressEvents[progressEvents.length - 1];
      const stepMap: Record<string, number> = {
        build_context: 0, decompose: 1, plan_strategy: 2,
        dispatch_execution: 3, prioritize_insights: 4,
        generate_narrative: 5, design: 6, compose: 7,
      };
      setCurrentStep(stepMap[last.step_name] ?? currentStep);
    }
  }, [progressEvents, currentStep]);

  const completedSteps = new Set(
    progressEvents
      .filter((event) => event.payload.status === 'completed')
      .map((event) => event.step_name)
  );
  const failedSteps = new Set(
    progressEvents
      .filter((event) => event.payload.status === 'error' || event.payload.status === 'timeout')
      .map((event) => event.step_name)
  );
  const completedCount = completedSteps.size;
  const totalSteps = 8;

  const handleCancel = async () => {
    await apiClient.cancelAnalysisJob(jobId);
    reset();
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${jobStatus === 'running' ? 'bg-blue-100 text-blue-800' : jobStatus === 'completed' ? 'bg-green-100 text-green-800' : jobStatus === 'failed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                {jobStatus}
              </span>
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight">Analysis Run</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
              Job {jobId}
            </p>
          </div>
          <Button variant="outline" className="text-destructive" onClick={handleCancel}>Cancel Analysis</Button>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              Completed
            </div>
            <p className="mt-2 text-2xl font-semibold">{completedCount}/{totalSteps}</p>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock3 className="h-4 w-4 text-primary" />
              Current Stage
            </div>
            <p className="mt-2 truncate text-lg font-semibold">{progressEvents[progressEvents.length - 1]?.step_name?.replaceAll('_', ' ') || 'queued'}</p>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <BarChart3 className="h-4 w-4 text-primary" />
              Stages
            </div>
            <p className="mt-2 text-2xl font-semibold">{totalSteps}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-5">
          <div className="md:col-span-2">
            <AnalysisStepper
              currentStep={currentStep}
              status={jobStatus}
              completedSteps={completedSteps}
              failedSteps={failedSteps}
            />
          </div>
          <div className="md:col-span-3">
            <LivePreview events={progressEvents} jobId={jobId} />
          </div>
        </div>
      </div>
    </div>
  );
}
