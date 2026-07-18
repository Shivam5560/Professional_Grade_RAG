"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ReportExperience } from "@/components/analysis/ReportExperience";
import { ReportToolbar } from "@/components/analysis/ReportToolbar";
import { ActionDock } from "@/components/shell/ActionDock";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import type { Report } from "@/lib/analysis/types";

export default function ReportViewerPage() {
  const { jobId } = useParams() as { jobId: string };
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiClient.getAnalysisReport(jobId)
      .then((data) => { if (active) setReport(data as unknown as Report); })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Unable to load report"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [jobId]);

  return (
    <FocusCanvas ariaLabel="Analysis report">
      <CanvasHeader
        description="A decision-first narrative with supporting visual evidence and prioritized findings available on demand."
        eyebrow="Data Analyst Studio"
        status={<span className="text-[11px] font-medium text-emerald-600">Verified report</span>}
        title={report?.title || "Analysis report"}
      />
      <ContextRibbon label="Report context">
        <span className="border border-border/70 bg-background/65 px-3 py-2 font-mono text-[10px] text-muted-foreground">{jobId}</span>
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">{report?.insights.length ?? 0} insights</span>
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">{report?.chart_urls.length ?? 0} charts</span>
      </ContextRibbon>

      {loading ? (
        <div className="mx-auto w-full max-w-6xl space-y-5 py-10" aria-label="Loading analysis report">
          <Skeleton className="h-10 w-72" /><Skeleton className="h-64 w-full" />
        </div>
      ) : error || !report ? (
        <div className="flex min-h-[50svh] items-center justify-center text-sm text-destructive" role="alert">{error ?? "Report not found."}</div>
      ) : <ReportExperience jobId={jobId} report={report} />}

      {report ? <ActionDock primary={<ReportToolbar jobId={jobId} />} /> : null}
    </FocusCanvas>
  );
}
