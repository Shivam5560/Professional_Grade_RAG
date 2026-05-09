// frontend/components/analysis/AnalysisStepper.tsx
'use client';

const STEPS = [
  'Decomposing Task',
  'Building Context',
  'Planning Strategy',
  'Running Analysis',
  'Prioritizing Insights',
  'Generating Narrative',
  'Designing Visuals',
  'Composing Report',
];

interface Props {
  currentStep: number;
  status: string;
}

export function AnalysisStepper({ currentStep, status }: Props) {
  return (
    <div className="space-y-4">
      {STEPS.map((step, idx) => (
        <div key={step} className="flex items-center gap-3">
          <div className={`h-3 w-3 rounded-full ${idx === currentStep ? 'bg-primary animate-pulse' : idx < currentStep ? 'bg-primary/60' : 'bg-muted'}`} />
          <span className={`text-sm ${idx === currentStep ? 'font-medium' : 'text-muted-foreground'}`}>{step}</span>
        </div>
      ))}
    </div>
  );
}
