import { StudioHttpClient, type StudioClientOptions } from "../http";
import type { ResumeAnalyzeResponse } from "@/lib/types";
import type { CandidateEdgeInput, StructuredCareerSource, StructuredRoleInput } from "./types";

export type CareerJsonScalar = string | number | boolean;

export interface CareerSourceSpanWire {
  source_id: string;
  locator: string;
  exact_text: string;
}

export interface CareerClaimWire {
  id: string;
  subject: {
    kind: "person" | "role" | "employer" | "project" | "education" | "certification" | "skill";
    id: string;
    label: string;
  };
  predicate:
    | "worked-at"
    | "held-title"
    | "has-skill"
    | "earned-degree"
    | "occurred-on"
    | "performed"
    | "achieved"
    | "measured"
    | "worked-on"
    | "earned-certification"
    | "located-in";
  object: {
    kind:
      | "employer"
      | "title"
      | "date"
      | "skill"
      | "degree"
      | "metric"
      | "responsibility"
      | "outcome"
      | "project"
      | "certification"
      | "location"
      | "work-mode";
    value: CareerJsonScalar;
    unit: string | null;
    measure: string | null;
  };
  source_spans: CareerSourceSpanWire[];
  temporal_scope: {
    start: string | null;
    end: string | null;
    label: string | null;
  };
  verification_status: "verified" | "inferred" | "disputed" | "rejected";
  confidence: number;
  verifier_id: string;
  context: {
    employer_id: string | null;
    project_id: string | null;
  };
  related_claim_ids: string[];
}

export interface CareerClaimRevisionWire {
  revision_id: string;
  logical_claim_id: string;
  revision: number;
  source_id: string;
  claim: CareerClaimWire;
  supersedes_revision_id: string | null;
  reviewer_id: number | null;
  created_at: string;
}

export interface CareerSourceWire {
  id: string;
  owner_id: number;
  filename: string;
  media_type: string;
  content_digest: string;
  created_at: string;
}

export interface CareerSourceIngestionResponseWire {
  source: CareerSourceWire;
  claims: CareerClaimRevisionWire[];
  resume?: {
    resume_id: string;
    filename: string;
    status: string;
  };
}

export interface ParsedRoleWire {
  title: string;
  requirements: RoleRequirementWire[];
}

export interface RoleRequirementWire {
  id: string;
  priority: "required" | "preferred";
  category:
    | "skill"
    | "responsibility"
    | "outcome"
    | "experience"
    | "seniority"
    | "education"
    | "certification"
    | "location"
    | "work-mode"
    | "domain";
  description: string;
  source_span: CareerSourceSpanWire;
  confidence: number;
  weight: number;
}

export interface CareerRoleWire {
  id: string;
  title: string;
  requirements: RoleRequirementWire[];
  created_at: string;
}

export interface ScoreComponentsWire {
  semantic_relevance: number;
  evidence_strength: number;
  recency: number;
  duration_seniority: number;
  transferability: number;
  specificity: number;
}

export interface SelectedMatchWire {
  requirement_id: string;
  claim_id: string;
  components: ScoreComponentsWire;
  score: number;
  strength: "weak" | "moderate" | "strong";
  objective_weight: number;
  uncertain: boolean;
}

export interface CoverageSummaryWire {
  total_weight: number;
  confident_matched_weight: number;
  possible_matched_weight: number;
  lower_bound: number;
  upper_bound: number;
  band: "none" | "limited" | "partial" | "substantial" | "complete";
}

export interface CareerMatchResultWire {
  selected_matches: SelectedMatchWire[];
  mandatory_coverage: CoverageSummaryWire;
  preferred_coverage: CoverageSummaryWire;
  unmatched_requirements: RoleRequirementWire[];
  uncertain_matches: SelectedMatchWire[];
  uncertain_requirement_ids: string[];
  transferable_matches: SelectedMatchWire[];
  selected_evidence: CareerClaimWire[];
}

export interface CareerMatchWire {
  id: string;
  role_id: string;
  result: CareerMatchResultWire;
  created_at: string;
}

export interface ResumeDraftBulletWire {
  source_claim_ids: string[];
  transformation: "verbatim" | "compressed" | "combined" | "reordered" | "rephrased";
  asserted_facts: Array<{
    kind: CareerClaimWire["object"]["kind"];
    value: CareerJsonScalar;
    unit: string | null;
    measure: string | null;
    source_claim_ids: string[];
  }>;
  added_keywords: Array<{
    keyword: string;
    source_claim_ids: string[];
  }>;
  before_text: string[];
  after_text: string;
}

export interface ResumeDraftWire {
  id: string;
  bullets: ResumeDraftBulletWire[];
  publication_ready: boolean;
}

export interface ApprovalRequestWire {
  id: string;
  run_id: string;
  owner_id: number;
  decision_type: string;
  proposed_changes: string[];
  evidence_ids: string[];
  status: "pending" | "approved" | "rejected" | "revision_requested";
  reviewer_id: number | null;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudioRunWire {
  id: string;
  owner_id: number;
  studio_id: string;
  operation: string;
  idempotency_key: string;
  input_fingerprint: string;
  state: "queued" | "running" | "awaiting_input" | "succeeded" | "failed" | "cancelled" | "expired";
  current_step: string | null;
  progress: number;
  failure_code: string | null;
  cancellation_requested: boolean;
  created_at: string;
  updated_at: string;
}

export interface QualityMetadataWire {
  algorithm_versions: Record<string, string>;
  model_versions: Record<string, string>;
  prompt_versions: Record<string, string>;
  confidence_components: Record<string, number>;
  validations: Array<{
    code: string;
    message: string;
    status: "pass" | "warning" | "error";
    critical: boolean;
  }>;
  warnings: string[];
  abstention_reason: string | null;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  trace_id: string;
  evaluation_run_id: string | null;
}

export interface CareerDraftWorkflowResponseWire {
  run: StudioRunWire;
  match: CareerMatchResultWire;
  draft: ResumeDraftWire;
  approval: ApprovalRequestWire;
  quality: QualityMetadataWire;
}

export interface CareerDraftWire {
  id: string;
  run_id: string;
  match_id: string;
  draft: ResumeDraftWire;
  truth_valid: boolean;
  approval_id: string | null;
  published_at: string | null;
  created_at: string;
}

export interface ArtifactRevisionWire {
  revision_id: string;
  artifact_id: string;
  revision: number;
  owner_id: number;
  studio_id: string;
  run_id: string;
  media_type: string;
  content_digest: string;
  evidence_ids: string[];
  supersedes_revision_id: string | null;
  created_at: string;
}

export interface CareerPublicationResponseWire {
  run: StudioRunWire;
  draft: ResumeDraftWire;
  approval: ApprovalRequestWire;
  artifact: ArtifactRevisionWire;
}

export class CareerStudioClient extends StudioHttpClient {
  constructor(options: StudioClientOptions = {}) { super("/api/v2/career", options); }
  createSource(payload: StructuredCareerSource): Promise<CareerSourceIngestionResponseWire> { return this.request("/sources", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  uploadResume(file: File): Promise<CareerSourceIngestionResponseWire> { const body = new FormData(); body.append("file", file); return this.request("/sources/upload", { method: "POST", body }); }
  getSource(sourceId: string): Promise<CareerSourceWire> { return this.request(`/sources/${encodeURIComponent(sourceId)}`); }
  decideClaim(claimId: string, action: "verify" | "reject" | "revise", replacement?: unknown): Promise<CareerClaimRevisionWire> { return this.request(`/claims/${encodeURIComponent(claimId)}/decisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, ...(replacement ? { replacement } : {}) }) }); }
  verifyClaim(claimId: string): Promise<CareerClaimRevisionWire> { return this.decideClaim(claimId, "verify"); }
  createRole(payload: StructuredRoleInput): Promise<CareerRoleWire> { return this.request("/roles", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  parseRole(jobDescription: string): Promise<ParsedRoleWire> { return this.request("/roles/parse", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_description: jobDescription }) }); }
  scoreResume(resumeId: string, jobDescription: string): Promise<ResumeAnalyzeResponse> { return this.request("/scores", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resume_id: resumeId, job_description: jobDescription }) }); }
  getRole(roleId: string): Promise<CareerRoleWire> { return this.request(`/roles/${encodeURIComponent(roleId)}`); }
  createMatch(payload: { match_id: string; role_id: string; candidate_edges: CandidateEdgeInput[] }): Promise<CareerMatchWire> { return this.request("/matches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  getMatch(matchId: string): Promise<CareerMatchWire> { return this.request(`/matches/${encodeURIComponent(matchId)}`); }
  createDraft(matchId: string, idempotencyKey = crypto.randomUUID()): Promise<CareerDraftWorkflowResponseWire> { return this.request("/drafts", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey }, body: JSON.stringify({ match_id: matchId }) }); }
  getDraft(draftId: string): Promise<CareerDraftWire> { return this.request(`/drafts/${encodeURIComponent(draftId)}`); }
  decideApproval(approvalId: string, decision: "approve" | "reject" | "revise", note?: string): Promise<ApprovalRequestWire> { return this.request(`/approvals/${encodeURIComponent(approvalId)}/decisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, comment: note }) }); }
  publishDraft(draftId: string): Promise<CareerPublicationResponseWire> { return this.request(`/drafts/${encodeURIComponent(draftId)}/publish`, { method: "POST" }); }
}

export const careerStudioClient = new CareerStudioClient();
