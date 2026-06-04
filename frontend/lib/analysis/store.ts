// frontend/lib/analysis/store.ts
import { create } from 'zustand';
import { AnalysisJob, WorkflowEvent, Report } from './types';

interface AnalysisState {
  activeJobId: string | null;
  jobStatus: AnalysisJob['status'] | 'idle';
  progressEvents: WorkflowEvent[];
  reportData: Report | null;
  socketConnected: boolean;
  setSocketConnected: (connected: boolean) => void;
  startAnalysis: (jobId: string) => void;
  appendEvent: (event: WorkflowEvent) => void;
  setReportData: (report: Report | null) => void;
  setJobState: (status: AnalysisJob['status'] | 'idle', events: WorkflowEvent[], report: Report | null) => void;
  reset: () => void;
}

// Track seen event keys to prevent duplicates
const seenEventKeys = new Set<string>();

export const useAnalysisStore = create<AnalysisState>((set) => ({
  activeJobId: null,
  jobStatus: 'idle',
  progressEvents: [],
  reportData: null,
  socketConnected: false,
  setSocketConnected: (connected) => set({ socketConnected: connected }),
  startAnalysis: (jobId) => {
    seenEventKeys.clear();
    set({ activeJobId: jobId, jobStatus: 'queued', progressEvents: [], reportData: null });
  },
  appendEvent: (event) => {
    // Deduplicate by step_name + timestamp (unique per emission)
    const key = `${event.step_name}::${event.timestamp}`;
    if (seenEventKeys.has(key)) return;
    seenEventKeys.add(key);
    set((state) => ({ progressEvents: [...state.progressEvents, event] }));
  },
  setReportData: (report) => set({ reportData: report, jobStatus: report ? 'completed' : 'failed' }),
  setJobState: (status, events, report) => {
    seenEventKeys.clear();
    events.forEach((event) => {
      const key = `${event.step_name}::${event.timestamp}`;
      seenEventKeys.add(key);
    });
    set({ jobStatus: status, progressEvents: events, reportData: report });
  },
  reset: () => {
    seenEventKeys.clear();
    set({ activeJobId: null, jobStatus: 'idle', progressEvents: [], reportData: null });
  },
}));
