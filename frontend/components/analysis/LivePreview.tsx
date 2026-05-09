// frontend/components/analysis/LivePreview.tsx
'use client';
import { WorkflowEvent } from '@/lib/analysis/types';

interface Props {
  events: WorkflowEvent[];
}

export function LivePreview({ events }: Props) {
  return (
    <div className="border rounded-lg p-4 h-full overflow-y-auto">
      <h3 className="text-sm font-medium mb-3">Live Preview</h3>
      {events.length === 0 && <p className="text-sm text-muted-foreground">Waiting for events...</p>}
      <div className="space-y-2">
        {events.map((ev, idx) => (
          <div key={idx} className="text-xs bg-muted rounded p-2">
            <span className="font-semibold">{ev.step_name}</span>
            <pre className="mt-1 text-muted-foreground overflow-x-auto">{JSON.stringify(ev.payload, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
