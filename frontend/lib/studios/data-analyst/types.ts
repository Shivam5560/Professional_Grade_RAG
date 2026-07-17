export type StudioRunState = "queued" | "running" | "awaiting_input" | "awaiting_approval" | "succeeded" | "failed" | "cancelled";

export interface StudioRun {
  id: string;
  state: StudioRunState;
  progress: number;
  question?: string;
  warnings?: string[];
  failure_code?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ColumnProfile {
  name: string;
  inferred_type: string;
  missing_count: number;
  unique_count: number;
  sensitive?: boolean;
}

export interface DatasetProfile {
  dataset_snapshot_id: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  warnings: string[];
  fingerprint?: string;
}

export interface DatasetSnapshotResponse {
  snapshot_id: string;
  filename?: string;
  profile: DatasetProfile;
}

export interface PlanStep {
  id: string;
  method_id: string;
  title: string;
  state: "pending" | "running" | "completed" | "failed" | "skipped";
  assumptions: string[];
  depends_on?: string[];
}

export interface AssumptionResult { name: string; passed: boolean; detail?: string }

export interface Computation {
  id: string;
  method_id: string;
  method_version: string;
  metrics: Record<string, string | number | boolean | null>;
  assumptions: AssumptionResult[];
  warnings: string[];
  evidence_id: string;
}

export interface Finding {
  id: string;
  language_class: "observation" | "association" | "prediction" | "hypothesis" | "recommendation";
  statement: string;
  confidence: number;
  evidence_ids: string[];
}

export interface AnalysisRunResponse {
  run: StudioRun;
  run_history?: StudioRun[];
  plan?: { steps?: PlanStep[] } | PlanStep[];
  profile?: DatasetProfile;
  quality?: unknown;
  abstention_reason?: string | null;
}

export interface AnalysisWorkspaceState {
  view: "start" | "run" | "history";
  profile: DatasetProfile | null;
  activeRun: StudioRun | null;
  history: StudioRun[];
  loading: boolean;
  error: string | null;
}
