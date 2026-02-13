import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ResumeAnalyzeResponse, ResumeFileInfo } from '@/lib/types';

interface NexusFlowState {
  selectedResume: ResumeFileInfo | null;
  jobDescription: string;
  analysis: ResumeAnalyzeResponse | null;
  setSelectedResume: (resume: ResumeFileInfo | null) => void;
  setJobDescription: (value: string) => void;
  setAnalysis: (analysis: ResumeAnalyzeResponse | null) => void;
  reset: () => void;
}

export const useNexusFlowStore = create<NexusFlowState>()(
  persist(
    (set) => ({
      selectedResume: null,
      jobDescription: '',
      analysis: null,
      setSelectedResume: (resume) => set({ selectedResume: resume }),
      setJobDescription: (value) => set({ jobDescription: value }),
      setAnalysis: (analysis) => set({ analysis }),
      reset: () => set({ selectedResume: null, jobDescription: '', analysis: null }),
    }),
    {
      name: 'nexus-flow',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
