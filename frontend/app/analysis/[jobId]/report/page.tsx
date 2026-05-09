'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Report } from '@/lib/analysis/types';
import { ReportToolbar } from '@/components/analysis/ReportToolbar';
import { InsightCard } from '@/components/analysis/InsightCard';
import { Skeleton } from '@/components/ui/skeleton';

export default function ReportViewerPage() {
  const { jobId } = useParams() as { jobId: string };
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/analysis/${jobId}/report`)
      .then((res) => res.json())
      .then((data) => {
        setReport(data);
        setLoading(false);
      });
  }, [jobId]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  if (!report) return <p>Report not found.</p>;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <ReportToolbar jobId={jobId} />
      <div className="mt-6 space-y-8">
        <div className="bg-card rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-2">{report.title || 'Analysis Report'}</h2>
          <p className="text-muted-foreground whitespace-pre-wrap">{report.narrative}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {report.insights.map((insight) => (
            <InsightCard key={insight.insight_id} insight={insight} />
          ))}
        </div>
      </div>
    </div>
  );
}
