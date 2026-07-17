export type ClaimStatus = "verified" | "inferred" | "disputed" | "rejected";
export interface CareerClaim { id: string; subject: string; predicate: string; value: string; status: ClaimStatus; confidence: number; source_label: string; source_spans?: string[] }
export interface RoleRequirement { id: string; text: string; kind: "mandatory" | "preferred"; confidence: number; source_span?: string }
export interface RequirementMatch { requirement_id: string; claim_id: string; weight: number; rationale: string }
export interface CareerGap { requirement_id: string; text: string; strategy?: string }
export interface DraftBullet { id: string; text: string; source_claim_ids: string[]; transformation: "verbatim" | "compressed" | "combined" | "reordered" | "rephrased"; added_keywords?: string[] }
export interface TruthIssue { id: string; severity: "critical" | "warning"; message: string; assertion: string; claim_ids: string[] }
export interface CareerDraft { id: string; revision: number; status: "drafting" | "truth_review" | "awaiting_approval" | "approved" | "published" | "revision_requested"; bullets: DraftBullet[]; truth_issues: TruthIssue[] }
export interface CareerApproval { id: string; type: "inferred_claim" | "final_publication"; status: "pending" | "approved" | "rejected" | "revision_requested"; claim_id?: string }
export interface CareerProfile { claims: CareerClaim[]; sources?: { id: string; filename: string; status: string }[] }
export interface CareerWorkspaceState { stage: "sources" | "requirements" | "coverage" | "draft" | "approve"; claims: CareerClaim[]; requirements: RoleRequirement[]; matches: RequirementMatch[]; gaps: CareerGap[]; draft: CareerDraft | null; approvals: CareerApproval[]; loading: boolean; error: string | null }

export interface StructuredCareerSource {
  filename: string;
  media_type: "application/json";
  ingestion_mode: "structured";
  claims: unknown[];
}

export interface StructuredRoleInput {
  role_id: string;
  title: string;
  requirements: unknown[];
}

export interface CandidateEdgeInput {
  requirement_id: string;
  claim_id: string;
  components: { semantic_relevance: number; evidence_strength: number; recency: number; duration_seniority: number; transferability: number; specificity: number };
}
