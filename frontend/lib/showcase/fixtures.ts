import type { ShowcaseId, ShowcaseScenario } from "./types";

const steps = (items: Array<[string, string, string, readonly string[]]>) =>
  items.map(([id, title, summary, evidence], index) => ({
    id,
    label: `0${index + 1}`,
    title,
    summary,
    evidence,
  }));

export const SHOWCASE_SCENARIOS: Record<ShowcaseId, ShowcaseScenario> = {
  knowledge: {
    id: "knowledge",
    eyebrow: "Grounded knowledge",
    title: "Trace an answer back to evidence.",
    prompt: "Summarize the revenue risks and cite the strongest evidence.",
    accent: "knowledge",
    steps: steps([
      [
        "retrieve",
        "Retrieve",
        "Hybrid search combines semantic and keyword candidates.",
        ["BM25 keyword signal", "Vector similarity", "User-scoped documents"],
      ],
      [
        "rerank",
        "Rerank",
        "The strongest passages are reordered for the question.",
        ["Cross-encoder relevance", "Duplicate suppression", "Top evidence retained"],
      ],
      [
        "answer",
        "Answer",
        "The response keeps citations and confidence visible.",
        ["Three cited sources", "94% confidence", "Evidence inspector ready"],
      ],
    ]),
  },
  aurasql: {
    id: "aurasql",
    eyebrow: "Schema-aware data",
    title: "Move from intent to a reviewable result.",
    prompt: "Show quarterly revenue growth by region for the last two years.",
    accent: "data",
    steps: steps([
      [
        "ask",
        "Ask",
        "The question is grounded in the active warehouse context.",
        ["Production warehouse selected", "Relevant tables identified", "Business intent retained"],
      ],
      [
        "review",
        "Review",
        "Generated SQL is formatted and validated before execution.",
        ["Schema names verified", "Read-only statement", "Validation passed"],
      ],
      [
        "results",
        "Results",
        "A deterministic result is ready for inspection or export.",
        ["24 rows returned", "Three columns", "Chart and CSV available"],
      ],
    ]),
  },
  analysis: {
    id: "analysis",
    eyebrow: "Multi-agent analysis",
    title: "Turn a dataset into an executive narrative.",
    prompt: "Find the strongest drivers of churn and recommend actions.",
    accent: "analysis",
    steps: steps([
      [
        "plan",
        "Plan",
        "The workflow chooses methods that match the dataset and question.",
        ["Data quality checked", "Correlation selected", "Segment analysis queued"],
      ],
      [
        "execute",
        "Execute",
        "Specialized agents run the approved statistical work.",
        ["Five segments compared", "Outliers inspected", "Visual evidence generated"],
      ],
      [
        "narrate",
        "Narrate",
        "Findings become a prioritized decision brief.",
        ["Four findings ranked", "Methods disclosed", "Report ready"],
      ],
    ]),
  },
  career: {
    id: "career",
    eyebrow: "Career intelligence",
    title: "Make resume improvements explainable.",
    prompt: "Align this resume to the role without inventing experience.",
    accent: "career",
    steps: steps([
      [
        "compare",
        "Compare",
        "Resume evidence is matched to the job description.",
        ["Skills mapped", "Gaps identified", "Existing evidence preserved"],
      ],
      [
        "improve",
        "Improve",
        "Suggested changes remain reviewable and reversible.",
        ["Impact language refined", "Keywords contextualized", "Diff ready"],
      ],
      [
        "export",
        "Export",
        "The approved resume is prepared as a polished artifact.",
        ["ATS score updated", "Human approval retained", "PDF ready"],
      ],
    ]),
  },
};

export function getShowcaseScenario(id: string): ShowcaseScenario | null {
  return Object.prototype.hasOwnProperty.call(SHOWCASE_SCENARIOS, id)
    ? SHOWCASE_SCENARIOS[id as ShowcaseId]
    : null;
}
