export type ShowcaseId = "knowledge" | "aurasql" | "analysis" | "career";
export type ShowcaseStatus = "ready" | "running" | "complete";

export interface ShowcaseStep {
  id: string;
  label: string;
  title: string;
  summary: string;
  evidence: readonly string[];
}

export interface ShowcaseScenario {
  id: ShowcaseId;
  eyebrow: string;
  title: string;
  prompt: string;
  accent: "knowledge" | "data" | "analysis" | "career";
  steps: readonly ShowcaseStep[];
}

export interface ShowcaseState {
  scenario: ShowcaseScenario;
  activeStep: number;
  status: ShowcaseStatus;
}

export type ShowcaseAction = { type: "advance" } | { type: "restart" };
