// frontend/app/analysis/[jobId]/page.tsx
'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAnalysisStore } from '@/lib/analysis/store';
import { useAnalysisSocket } from '@/lib/analysis/useAnalysisSocket';
import { AnalysisStepper } from '@/components/analysis/AnalysisStepper';
import { LivePreview } from '@/components/analysis/LivePreview';
import { Button } from '@/components/ui/button';

export default function AnalysisProgressPage() {
  const { jobId } = useParams() as { jobId: string };
  const { progressEvents, jobStatus, reset } = useAnalysisStore();
  const [currentStep, setCurrentStep] = useState(0);

  useAnalysisSocket(jobId);

  useEffect(() => {
    if (progressEvents.length > 0) {
      const last = progressEvents[progressEvents.length - 1];
      const stepMap: Record<string, number> = {
        decompose: 0, build_context: 1, plan_strategy: 2,
        dispatch_execution: 3, prioritize_insights: 4,
        generate_narrative: 5, design: 6, compose: 7,
      };
      setCurrentStep(stepMap[last.step_name] ?? currentStep);
    }
  }, [progressEvents, currentStep]);

  const handleCancel = async () => {
    await fetch(`/api/v1/analysis/${jobId}/cancel`, { method: 'POST' });
    reset();
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
      <div className="md:col-span-1 space-y-6">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${jobStatus === 'running' ? 'bg-blue-100 text-blue-800' : jobStatus === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {jobStatus}
          </span>
        </div>
        <AnalysisStepper currentStep={currentStep} status={jobStatus} />
        <Button variant="outline" className="w-full text-destructive" onClick={handleCancel}>Cancel Analysis</Button>
      </div>
      <div className="md:col-span-2">
        <LivePreview events={progressEvents} />
      </div>
    </div>
  );
}
