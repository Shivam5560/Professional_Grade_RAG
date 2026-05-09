// frontend/lib/analysis/store.ts
import { create } from 'zustand';
import { AnalysisJob, WorkflowEvent, Report } from './types';

interface AnalysisState {
  activeJobId: string | null;
  jobStatus: AnalysisJob['status'] | 'idle';
  progressEvents: WorkflowEvent[];
  reportData: Report | null;
  startAnalysis: (jobId: string) => void;
  appendEvent: (event: WorkflowEvent) => void;
  setReportData: (report: Report) => void;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  activeJobId: null,
  jobStatus: 'idle',
  progressEvents: [],
  reportData: null,
  startAnalysis: (jobId) => set({ activeJobId: jobId, jobStatus: 'queued', progressEvents: [], reportData: null }),
  appendEvent: (event) => set((state) => ({ progressEvents: [...state.progressEvents, event] })),
  setReportData: (report) => set({ reportData: report, jobStatus: 'completed' }),
  reset: () => set({ activeJobId: null, jobStatus: 'idle', progressEvents: [], reportData: null }),
}));
