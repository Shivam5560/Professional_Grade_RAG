import { StudioHttpClient, type StudioClientOptions } from "../http";
import type { AnalysisRunResponse, Computation, DatasetProfile, DatasetSnapshotResponse, Finding } from "./types";

export class DataAnalystClient extends StudioHttpClient {
  constructor(options: StudioClientOptions = {}) { super("/api/v2/data-analyst", options); }

  createDataset(file: File): Promise<DatasetSnapshotResponse> {
    return this.request("/datasets", { method: "POST", body: file, headers: { "Content-Type": file.type || "text/csv", "X-Filename": file.name } });
  }
  getProfile(datasetId: string): Promise<DatasetProfile> { return this.request(`/datasets/${encodeURIComponent(datasetId)}/profile`); }
  createRun(payload: { snapshot_id: string; question: string; context?: string }, idempotencyKey: string): Promise<AnalysisRunResponse> {
    return this.request("/runs", { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey }, body: JSON.stringify(payload) });
  }
  getRun(runId: string): Promise<AnalysisRunResponse> { return this.request(`/runs/${encodeURIComponent(runId)}`); }
  cancelRun(runId: string): Promise<AnalysisRunResponse> { return this.request(`/runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" }); }
  updatePlan(runId: string, steps: unknown[]): Promise<AnalysisRunResponse> { return this.request(`/runs/${encodeURIComponent(runId)}/plan`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ steps }) }); }
  async getComputations(runId: string): Promise<Computation[]> {
    const result = await this.request<{ computations: Array<Computation & { output?: Computation["metrics"]; assumption_results?: Array<{ name: string; status: string; detail?: string }>; evidence?: { id: string } }> }>(`/runs/${encodeURIComponent(runId)}/computations`);
    return result.computations.map((item) => ({
      ...item,
      metrics: item.metrics ?? item.output ?? {},
      assumptions: item.assumptions ?? item.assumption_results?.map((value) => ({ name: value.name, passed: value.status === "pass", detail: value.detail })) ?? [],
      evidence_id: item.evidence_id ?? item.evidence?.id ?? item.id,
    }));
  }
  async getClaims(runId: string): Promise<Finding[]> {
    const result = await this.request<{ claims: Array<Finding & { subject?: string; predicate?: string; value?: unknown; evidence_links?: Array<{ evidence_id: string }>; confidence_components?: Record<string, number> }> }>(`/runs/${encodeURIComponent(runId)}/claims`);
    return result.claims.map((item) => ({
      ...item,
      statement: item.statement ?? [item.subject, item.predicate, item.value == null ? "" : String(item.value)].filter(Boolean).join(" "),
      confidence: item.confidence ?? Math.min(...Object.values(item.confidence_components ?? { verified: 1 })),
      evidence_ids: item.evidence_ids ?? item.evidence_links?.map((link) => link.evidence_id) ?? [],
    }));
  }
  getReport(runId: string): Promise<{ limitations: string[]; artifact_id?: string }> { return this.request(`/runs/${encodeURIComponent(runId)}/report`); }
}

export const dataAnalystClient = new DataAnalystClient();
