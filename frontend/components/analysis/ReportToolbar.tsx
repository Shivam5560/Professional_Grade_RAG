'use client';
import { Button } from '@/components/ui/button';
import { Download, Share2, RotateCcw } from 'lucide-react';
import Link from 'next/link';

interface Props {
  jobId: string;
}

export function ReportToolbar({ jobId }: Props) {
  const handleDownload = () => {
    window.open(`/api/v1/analysis/${jobId}/slides`, '_blank');
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
  };

  return (
    <div className="flex items-center gap-2 sticky top-0 bg-background z-10 py-4 border-b">
      <Link href="/analysis/history">
        <Button variant="ghost">← All Analyses</Button>
      </Link>
      <div className="flex-1" />
      <Button variant="outline" onClick={handleDownload}>
        <Download className="h-4 w-4 mr-2" />PPTX
      </Button>
      <Button variant="outline" onClick={handleShare}>
        <Share2 className="h-4 w-4 mr-2" />Share
      </Button>
      <Link href={`/analysis?rerun=${jobId}`}>
        <Button variant="outline">
          <RotateCcw className="h-4 w-4 mr-2" />Re-run
        </Button>
      </Link>
    </div>
  );
}
