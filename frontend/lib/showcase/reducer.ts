import type { ShowcaseAction, ShowcaseScenario, ShowcaseState } from "./types";

export const initialShowcaseState = (scenario: ShowcaseScenario): ShowcaseState => ({
  scenario,
  activeStep: 0,
  status: "ready",
});

export function showcaseReducer(state: ShowcaseState, action: ShowcaseAction): ShowcaseState {
  if (action.type === "restart") return initialShowcaseState(state.scenario);
  const last = state.scenario.steps.length - 1;
  const activeStep = Math.min(state.activeStep + 1, last);
  return { ...state, activeStep, status: activeStep === last ? "complete" : "running" };
}
