import type { CareerApproval, CareerClaim, CareerDraft, CareerGap, CareerWorkspaceState, RequirementMatch, RoleRequirement } from "./types";

export const initialCareerWorkspace: CareerWorkspaceState = { stage: "sources", claims: [], requirements: [], matches: [], gaps: [], draft: null, approvals: [], loading: false, error: null };
type Action =
  | { type: "loading" }
  | { type: "failed"; message: string }
  | { type: "claims-loaded"; claims: CareerClaim[] }
  | { type: "role-loaded"; requirements: RoleRequirement[] }
  | { type: "match-loaded"; matches: RequirementMatch[]; gaps: CareerGap[] }
  | { type: "draft-loaded"; draft: CareerDraft }
  | { type: "approvals-loaded"; approvals: CareerApproval[] }
  | { type: "truth-cleared"; draftId: string };

export function careerWorkspaceReducer(state: CareerWorkspaceState, action: Action): CareerWorkspaceState {
  switch (action.type) {
    case "loading": return { ...state, loading: true, error: null };
    case "failed": return { ...state, loading: false, error: action.message };
    case "claims-loaded": return { ...state, loading: false, claims: action.claims, stage: "requirements" };
    case "role-loaded": return { ...state, loading: false, requirements: action.requirements, stage: "coverage" };
    case "match-loaded": return { ...state, loading: false, matches: action.matches, gaps: action.gaps, stage: "draft" };
    case "draft-loaded": return { ...state, loading: false, draft: action.draft, stage: action.draft.status === "awaiting_approval" ? "approve" : "draft" };
    case "approvals-loaded": return { ...state, loading: false, approvals: action.approvals };
    case "truth-cleared": return state.draft?.id === action.draftId ? { ...state, stage: "approve", draft: { ...state.draft, truth_issues: [], status: "awaiting_approval" } } : state;
  }
}
