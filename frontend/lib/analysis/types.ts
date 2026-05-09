// frontend/lib/analysis/types.ts
export interface AnalysisJob {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  query: string;
  created_at: string;
  progress_events: WorkflowEvent[];
}

export interface WorkflowEvent {
  step_name: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface Insight {
  insight_id: string;
  content: string;
  significance_score: number;
  source_agents: string[];
}

export interface Report {
  report_id: string;
  title: string;
  narrative: string;
  sections: ReportSection[];
  insights: Insight[];
  chart_urls: string[];
  slide_deck_url?: string;
}

export interface ReportSection {
  title: string;
  content: string;
  chart_id?: string;
}

export interface AnalysisConfig {
  max_rows: number;
  include_predictive: boolean;
  output_format: ('interactive' | 'pptx')[];
}
