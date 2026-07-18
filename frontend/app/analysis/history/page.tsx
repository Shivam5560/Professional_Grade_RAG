"use client";

import { Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { HistoryTable } from "@/components/analysis/HistoryTable";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import type { AnalysisJob } from "@/lib/analysis/types";

export default function AnalysisHistoryPage() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listAnalysisJobs();
      setJobs((data.jobs || []) as unknown as AnalysisJob[]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load analysis history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void fetchJobs(); }, [fetchJobs]);

  async function handleDelete(jobId: string) {
    if (!confirm("Delete this analysis and its reports?")) return;
    try {
      await apiClient.deleteAnalysisJob(jobId);
      setJobs((current) => current.filter((job) => job.job_id !== jobId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to delete analysis");
    }
  }

  return (
    <FocusCanvas ariaLabel="Analysis history">
      <CanvasHeader
        actions={<Button asChild><Link href="/analysis"><Plus aria-hidden="true" className="mr-2 h-4 w-4" />New analysis</Link></Button>}
        description="Return to an analysis without mixing it with activity from other applications."
        eyebrow="Data Analyst Studio"
        title="Analysis history"
      />
      <ContextRibbon label="Run index">
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">{jobs.length} saved {jobs.length === 1 ? "run" : "runs"}</span>
        <span className="border border-border/70 bg-background/65 px-3 py-2 text-xs text-muted-foreground">Analysis only</span>
      </ContextRibbon>

      <section className="mx-auto w-full max-w-6xl py-7 sm:py-10">
        {loading ? <div className="space-y-3" aria-label="Loading analysis history"><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /></div> : null}
        {!loading && error ? (
          <div className="flex min-h-72 flex-col items-center justify-center border-y border-destructive/30 text-center"><p className="text-sm text-destructive" role="alert">{error}</p><Button className="mt-4" onClick={() => void fetchJobs()} variant="outline"><RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />Retry</Button></div>
        ) : null}
        {!loading && !error ? <HistoryTable jobs={jobs} onDelete={handleDelete} /> : null}
      </section>
    </FocusCanvas>
  );
}
