export interface CapabilityStoryItem {
  id: "knowledge" | "aurasql" | "analysis" | "career";
  name: string;
  statement: string;
  proof: readonly string[];
  showcaseHref: string;
}

export const CAPABILITIES: readonly CapabilityStoryItem[] = [
  {
    id: "knowledge",
    name: "Knowledge",
    statement: "Grounded answers with evidence kept in view.",
    proof: ["Hybrid retrieval", "Source citations", "Confidence scoring"],
    showcaseHref: "/showcase/knowledge",
  },
  {
    id: "aurasql",
    name: "AuraSQL",
    statement: "Natural-language questions become reviewable, executable SQL.",
    proof: ["Schema context", "SQL validation", "Exportable results"],
    showcaseHref: "/showcase/aurasql",
  },
  {
    id: "analysis",
    name: "Analysis",
    statement: "Multi-agent analysis becomes an executive narrative, not a log wall.",
    proof: ["Statistical methods", "Visual reports", "Persistent jobs"],
    showcaseHref: "/showcase/analysis",
  },
  {
    id: "career",
    name: "Career Studio",
    statement: "Resume evidence turns into targeted, explainable improvements.",
    proof: ["JD alignment", "ATS scoring", "PDF generation"],
    showcaseHref: "/showcase/career",
  },
] as const;

export const PROOF_POINTS = [
  ["Retrieval", "BM25 + vector fusion with reranking"],
  ["Reasoning", "Fast and deep document navigation modes"],
  ["Data", "Schema-aware SQL generation and execution"],
  ["Operations", "Observable long-running analysis workflows"],
] as const;

export const CREATOR_SUMMARY = {
  name: "Shivam Sourav",
  heading: "Built end to end by Shivam Sourav",
  body: "A solo-engineered AI platform spanning product design, retrieval, data systems, workflow orchestration, observability, and deployment.",
  href: "/developer",
} as const;
