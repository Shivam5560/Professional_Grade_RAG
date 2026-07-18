import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";

import { AnalysisRunCanvas } from "@/components/analysis/AnalysisRunCanvas";
import { ReportExperience } from "@/components/analysis/ReportExperience";

describe("Analysis experience", () => {
  it("keeps the current phase primary and moves technical detail into an inspector", () => {
    render(
      <AnalysisRunCanvas
        computations={[]}
        findings={[]}
        limitations={[]}
        plan={[
          {
            id: "profile",
            method_id: "profile",
            title: "Profile the dataset",
            state: "completed",
            assumptions: [],
          },
          {
            id: "compare",
            method_id: "compare-groups",
            title: "Compare retention cohorts",
            state: "running",
            assumptions: ["Independent groups"],
          },
        ]}
        profile={{
          dataset_snapshot_id: "snapshot-1",
          row_count: 1200,
          column_count: 8,
          columns: [],
          warnings: [],
        }}
        run={{
          id: "run-1",
          state: "running",
          progress: 0.42,
          question: "What drives retention?",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Compare retention cohorts" })).toBeInTheDocument();
    expect(screen.getByText("42%")) .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect run details" })).toBeInTheDocument();
    expect(screen.queryByText("Dataset columns")).not.toBeVisible();
  });

  it("presents the report as narrative, charts, and insight views", () => {
    render(
      <ReportExperience
        jobId="job-1"
        report={{
          report_id: "report-1",
          title: "Retention signal review",
          narrative: "Retention is strongest in the assisted onboarding cohort.",
          sections: [],
          insights: [],
          chart_urls: [],
        }}
      />,
    );

    expect(screen.getByRole("tab", { name: "Narrative" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Charts" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Insights" })).toBeInTheDocument();
    expect(screen.getByText("Retention is strongest in the assisted onboarding cohort.")).toBeInTheDocument();
  });

  it("does not mount the legacy global header from any Analysis route", () => {
    const routes = [
      "app/analysis/page.tsx",
      "app/analysis/[jobId]/page.tsx",
      "app/analysis/[jobId]/report/page.tsx",
      "app/analysis/history/page.tsx",
    ];

    for (const route of routes) {
      const source = readFileSync(join(process.cwd(), route), "utf8");
      expect(source).not.toContain("@/components/layout/Header");
      expect(source).not.toContain("@/components/layout/PageShell");
      expect(source).toContain("FocusCanvas");
    }
  });
});
