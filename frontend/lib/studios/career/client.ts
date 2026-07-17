import { StudioHttpClient, type StudioClientOptions } from "../http";
import type { CandidateEdgeInput, StructuredCareerSource, StructuredRoleInput } from "./types";

export class CareerStudioClient extends StudioHttpClient {
  constructor(options: StudioClientOptions = {}) { super("/api/v2/career", options); }
  createSource(payload: StructuredCareerSource): Promise<any> { return this.request("/sources", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  getSource(sourceId: string): Promise<any> { return this.request(`/sources/${encodeURIComponent(sourceId)}`); }
  decideClaim(claimId: string, action: "verify" | "reject" | "revise", replacement?: unknown): Promise<any> { return this.request(`/claims/${encodeURIComponent(claimId)}/decisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, ...(replacement ? { replacement } : {}) }) }); }
  verifyClaim(claimId: string): Promise<any> { return this.decideClaim(claimId, "verify"); }
  createRole(payload: StructuredRoleInput): Promise<any> { return this.request("/roles", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  getRole(roleId: string): Promise<any> { return this.request(`/roles/${encodeURIComponent(roleId)}`); }
  createMatch(payload: { match_id: string; role_id: string; candidate_edges: CandidateEdgeInput[] }): Promise<any> { return this.request("/matches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); }
  getMatch(matchId: string): Promise<any> { return this.request(`/matches/${encodeURIComponent(matchId)}`); }
  createDraft(matchId: string, idempotencyKey = crypto.randomUUID()): Promise<any> { return this.request("/drafts", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey }, body: JSON.stringify({ match_id: matchId }) }); }
  getDraft(draftId: string): Promise<any> { return this.request(`/drafts/${encodeURIComponent(draftId)}`); }
  decideApproval(approvalId: string, decision: "approve" | "reject" | "revise", note?: string): Promise<any> { return this.request(`/approvals/${encodeURIComponent(approvalId)}/decisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, comment: note }) }); }
  publishDraft(draftId: string): Promise<{ artifact_id: string }> { return this.request(`/drafts/${encodeURIComponent(draftId)}/publish`, { method: "POST" }); }
}

export const careerStudioClient = new CareerStudioClient();
