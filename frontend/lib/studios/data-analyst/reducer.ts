import type { AnalysisWorkspaceState, DatasetProfile, StudioRun } from "./types";

export const initialAnalysisWorkspace: AnalysisWorkspaceState = { view: "start", profile: null, activeRun: null, history: [], loading: false, error: null };

type Action =
  | { type: "loading" }
  | { type: "failed"; message: string }
  | { type: "profile-loaded"; profile: DatasetProfile }
  | { type: "run-loaded"; run: StudioRun }
  | { type: "cancelled"; runId: string }
  | { type: "history-loaded"; runs: StudioRun[] }
  | { type: "reset" };

export function analysisWorkspaceReducer(state: AnalysisWorkspaceState, action: Action): AnalysisWorkspaceState {
  switch (action.type) {
    case "loading": return { ...state, loading: true, error: null };
    case "failed": return { ...state, loading: false, error: action.message };
    case "profile-loaded": return { ...state, loading: false, profile: action.profile };
    case "run-loaded": return { ...state, view: "run", loading: false, activeRun: action.run, history: [action.run, ...state.history.filter((run) => run.id !== action.run.id)] };
    case "cancelled": return state.activeRun?.id === action.runId ? { ...state, loading: false, view: "run", activeRun: { ...state.activeRun, state: "cancelled" } } : state;
    case "history-loaded": return { ...state, loading: false, view: "history", history: action.runs };
    case "reset": return initialAnalysisWorkspace;
  }
}
