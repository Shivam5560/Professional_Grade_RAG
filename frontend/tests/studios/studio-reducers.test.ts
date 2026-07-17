import { analysisWorkspaceReducer, initialAnalysisWorkspace } from "@/lib/studios/data-analyst/reducer";
import { careerWorkspaceReducer, initialCareerWorkspace } from "@/lib/studios/career/reducer";

describe("specialist workspace reducers", () => {
  it("keeps the analysis run inspectable after cancellation", () => {
    const running = analysisWorkspaceReducer(initialAnalysisWorkspace, {
      type: "run-loaded",
      run: { id: "run-1", state: "running", progress: 0.45, question: "Find profit drivers", warnings: [] },
    });
    const cancelled = analysisWorkspaceReducer(running, { type: "cancelled", runId: "run-1" });

    expect(cancelled.activeRun?.state).toBe("cancelled");
    expect(cancelled.activeRun?.progress).toBe(0.45);
    expect(cancelled.view).toBe("run");
  });

  it("moves a career draft from truth issues into approval", () => {
    const withDraft = careerWorkspaceReducer(initialCareerWorkspace, {
      type: "draft-loaded",
      draft: { id: "draft-1", revision: 2, status: "truth_review", bullets: [], truth_issues: [{ id: "issue-1", severity: "critical", message: "Unsupported metric", assertion: "40%", claim_ids: [] }] },
    });
    const cleared = careerWorkspaceReducer(withDraft, { type: "truth-cleared", draftId: "draft-1" });

    expect(cleared.draft?.truth_issues).toEqual([]);
    expect(cleared.draft?.status).toBe("awaiting_approval");
    expect(cleared.stage).toBe("approve");
  });
});
