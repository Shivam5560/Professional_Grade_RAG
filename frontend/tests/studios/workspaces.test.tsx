import { render, screen } from "@testing-library/react";
import { DataAnalystWorkspace } from "@/components/studios/data-analyst/DataAnalystWorkspace";
import { CareerWorkspace } from "@/components/studios/career/CareerWorkspace";

describe("specialist workspaces", () => {
  it("renders evidence and limitations beside verified findings", () => {
    render(<DataAnalystWorkspace
      profile={{ dataset_snapshot_id: "snapshot-1", row_count: 1200, column_count: 8, columns: [{ name: "revenue", inferred_type: "numeric", missing_count: 0, unique_count: 1190 }], warnings: ["Region is missing in 2.1% of rows"] }}
      run={{ id: "run-1", state: "succeeded", progress: 1, question: "What drives revenue?", warnings: [] }}
      plan={[{ id: "step-1", method_id: "pearson-correlation", title: "Measure relationships", state: "completed", assumptions: ["Numeric variables"] }]}
      computations={[{ id: "comp-1", method_id: "pearson-correlation", method_version: "1.0.0", metrics: { coefficient: 0.72, sample_size: 1200 }, assumptions: [{ name: "finite-values", passed: true }], warnings: [], evidence_id: "evidence-1" }]}
      findings={[{ id: "finding-1", language_class: "association", statement: "Revenue and retention move together.", confidence: 0.91, evidence_ids: ["evidence-1"] }]}
      limitations={["Association does not establish causation."]}
    />);

    expect(screen.getByRole("heading", { name: "Verified findings" })).toBeInTheDocument();
    expect(screen.getAllByText("evidence-1").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Association does not establish causation.")).toBeInTheDocument();
  });

  it("renders one-to-one career coverage and approval state", () => {
    render(<CareerWorkspace
      claims={[{ id: "claim-1", subject: "Payments migration", predicate: "delivered", value: "Cut checkout latency", status: "verified", confidence: 0.98, source_label: "Resume · page 1" }]}
      requirements={[{ id: "req-1", text: "Lead platform migrations", kind: "mandatory", confidence: 0.94 }]}
      matches={[{ requirement_id: "req-1", claim_id: "claim-1", weight: 0.88, rationale: "Direct delivery evidence" }]}
      gaps={[]}
      draft={{ id: "draft-1", revision: 3, status: "awaiting_approval", bullets: [{ id: "bullet-1", text: "Led a payments migration that reduced checkout latency.", source_claim_ids: ["claim-1"], transformation: "rephrased" }], truth_issues: [] }}
      approvals={[{ id: "approval-1", type: "final_publication", status: "pending" }]}
    />);

    expect(screen.getByRole("heading", { name: "Requirement coverage" })).toBeInTheDocument();
    expect(screen.getAllByText("claim-1").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Awaiting final approval")).toBeInTheDocument();
  });
});
