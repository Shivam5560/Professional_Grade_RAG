'use client';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Share2, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';

interface Props {
  jobId: string;
}

export function ReportToolbar({ jobId }: Props) {
  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
  };

  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 border-b bg-background/95 py-4 backdrop-blur">
      <Link href="/analysis/history">
        <Button variant="ghost" className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          All Analyses
        </Button>
      </Link>
      <div className="flex-1" />
      <Button variant="outline" className="gap-2" onClick={() => apiClient.downloadAnalysisReport(jobId)}>
        <Download className="h-4 w-4" />
        Download PPTX
      </Button>
      <Button variant="outline" className="gap-2" onClick={handleShare}>
        <Share2 className="h-4 w-4" />
        Share
      </Button>
      <Link href={`/analysis?rerun=${jobId}`}>
        <Button variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Re-run
        </Button>
      </Link>
    </div>
  );
}
