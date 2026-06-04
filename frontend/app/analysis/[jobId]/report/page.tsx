'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Report } from '@/lib/analysis/types';
import { ReportToolbar } from '@/components/analysis/ReportToolbar';
import { InsightCard } from '@/components/analysis/InsightCard';
import { apiClient } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { BarChart3, FileText, Sparkles } from 'lucide-react';

export default function ReportViewerPage() {
  const { jobId } = useParams() as { jobId: string };
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.getAnalysisReport(jobId)
      .then((data) => {
        setReport(data as unknown as Report);
        setLoading(false);
      });
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="max-w-5xl mx-auto py-8 px-4 space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        </div>
      </div>
    );
  }

  if (!report) return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <p className="max-w-5xl mx-auto py-8 px-4">Report not found.</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <div className="mx-auto max-w-6xl px-4 py-8">
        <ReportToolbar jobId={jobId} />
        <div className="mt-8 space-y-8">
          <section className="rounded-lg border bg-card p-6 shadow-sm">
            <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <Badge variant="outline" className="mb-3 gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" />
                  Analysis report
                </Badge>
                <h1 className="max-w-3xl text-3xl font-semibold tracking-tight">{report.title || 'Analysis Report'}</h1>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-md border bg-background px-3 py-2">
                  <p className="text-xs text-muted-foreground">Insights</p>
                  <p className="text-lg font-semibold">{report.insights.length}</p>
                </div>
                <div className="rounded-md border bg-background px-3 py-2">
                  <p className="text-xs text-muted-foreground">Charts</p>
                  <p className="text-lg font-semibold">{report.chart_urls.length}</p>
                </div>
              </div>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{report.narrative}</p>
          </section>

          {report.sections?.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <h2 className="text-lg font-semibold">Report Sections</h2>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {report.sections.map((section, index) => (
                  <article key={`${section.title}-${index}`} className="rounded-lg border bg-card p-5 shadow-sm">
                    <h3 className="text-sm font-semibold">{section.title || `Section ${index + 1}`}</h3>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{section.content}</p>
                  </article>
                ))}
              </div>
            </section>
          )}

          {report.chart_urls?.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                <h2 className="text-lg font-semibold">Visual Evidence</h2>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {report.chart_urls.map((url, index) => (
                  <figure key={url} className="overflow-hidden rounded-lg border bg-card shadow-sm">
                    <div className="border-b px-4 py-3 text-sm font-medium">Chart {index + 1}</div>
                    <div className="bg-background p-3">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${url}`} alt={`Analysis chart ${index + 1}`} className="h-auto w-full rounded-md border bg-white object-contain" />
                    </div>
                  </figure>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h2 className="text-lg font-semibold">Prioritized Insights</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {report.insights.map((insight) => (
                <InsightCard key={insight.insight_id} insight={insight} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
