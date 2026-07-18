"use client";

import { Download, RotateCcw, Share2 } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";

export function ReportToolbar({ jobId }: { jobId: string }) {
  return (
    <div className="flex items-center gap-2">
      <Button aria-label="Share report" onClick={() => void navigator.clipboard.writeText(window.location.href)} size="icon" title="Share report" variant="ghost"><Share2 aria-hidden="true" className="h-4 w-4" /></Button>
      <Button asChild aria-label="Rerun analysis" size="icon" title="Rerun analysis" variant="ghost"><Link href={`/analysis?rerun=${jobId}`}><RotateCcw aria-hidden="true" className="h-4 w-4" /></Link></Button>
      <Button onClick={() => void apiClient.downloadAnalysisReport(jobId)}><Download aria-hidden="true" className="mr-2 h-4 w-4" />Download deck</Button>
    </div>
  );
}
