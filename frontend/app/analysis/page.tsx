'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { FileDropzone } from '@/components/analysis/FileDropzone';
import { AnalysisConfigAccordion } from '@/components/analysis/AnalysisConfigAccordion';
import { AnalysisConfig } from '@/lib/analysis/types';
import { apiClient } from '@/lib/api';
import { useAnalysisStore } from '@/lib/analysis/store';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  BarChart3,
  Upload,
  MessageSquare,
  Sparkles,
  ArrowRight,
  History,
  FileSpreadsheet,
  Lightbulb,
} from 'lucide-react';
import Link from 'next/link';

const SAMPLE_QUERIES = [
  {
    label: 'Trend Analysis',
    query: 'What are the key trends and patterns in this data? Identify any significant changes over time.',
    icon: BarChart3,
  },
  {
    label: 'Driver Analysis',
    query: 'Which factors most strongly influence the target variable? Rank them by importance and explain the relationships.',
    icon: Lightbulb,
  },
  {
    label: 'Full Exploration',
    query: 'Perform a comprehensive exploratory analysis: distributions, correlations, anomalies, and key segments.',
    icon: Sparkles,
  },
];

const STEPS = [
  { icon: Upload, title: 'Upload', desc: 'Drop your CSV or Excel file' },
  { icon: MessageSquare, title: 'Ask', desc: 'Describe what you want to know' },
  { icon: Sparkles, title: 'Insights', desc: 'AI analyzes & generates a report' },
];

export default function AnalysisHubPage() {
  const router = useRouter();
  const { reset } = useAnalysisStore();
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<AnalysisConfig>({
    max_rows: 50000,
    include_predictive: true,
    output_format: ['interactive', 'pptx'],
  });

  // Reset stale analysis state when user navigates back to this page
  useEffect(() => {
    reset();
  }, [reset]);

  const handleSubmit = async () => {
    if (!file || !query.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const uploadData = await apiClient.uploadAnalysisFile(file);
      if (!uploadData.source_id) throw new Error('Upload failed — no source ID returned');

      const startData = await apiClient.startAnalysisFromUpload({
        source_id: uploadData.source_id,
        query: query,
        config: config as unknown as Record<string, unknown>,
      });

      setLoading(false);
      if (startData.job_id) {
        router.push(`/analysis/${startData.job_id}`);
      }
    } catch (err) {
      setLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
      console.error('Failed to start analysis:', err);
    }
  };

  const isReady = file && query.trim().length > 0;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <div className="mx-auto max-w-6xl px-4 py-8 lg:py-12">
        {/* Hero */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <BarChart3 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Data Storyteller</h1>
              <p className="text-sm text-muted-foreground">Upload data, ask questions, get AI-powered insights & reports</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* ─── Left: Main Form ─── */}
          <div className="lg:col-span-2 space-y-6">
            {/* Step 1: File Upload */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">1</span>
                <h2 className="text-sm font-semibold">Upload your data</h2>
              </div>
              <FileDropzone onFileSelect={setFile} selectedFile={file} />
            </div>

            {/* Step 2: Query */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">2</span>
                  <h2 className="text-sm font-semibold">What do you want to know?</h2>
                </div>
                {query.length > 0 && (
                  <span className="text-xs text-muted-foreground">{query.length} chars</span>
                )}
              </div>
              <Textarea
                id="analysis-query"
                placeholder="e.g., What are the key trends in revenue and which factors drive customer churn?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="resize-none"
              />

              {/* Sample queries */}
              <div className="mt-3">
                <p className="mb-2 text-xs text-muted-foreground">Try a sample query:</p>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_QUERIES.map((sq) => (
                    <button
                      key={sq.label}
                      onClick={() => setQuery(sq.query)}
                      className="inline-flex items-center gap-1.5 rounded-md border bg-background px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-foreground"
                    >
                      <sq.icon className="h-3 w-3" />
                      {sq.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 3: Config + Submit */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">3</span>
                <h2 className="text-sm font-semibold">Configure & run</h2>
              </div>

              <AnalysisConfigAccordion config={config} onChange={setConfig} />

              {error && (
                <div className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <Button
                id="start-analysis-btn"
                onClick={handleSubmit}
                disabled={!isReady || loading}
                className="mt-4 w-full gap-2"
                size="lg"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Uploading & starting...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Start Analysis
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>

              {!isReady && !loading && (
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  {!file ? 'Upload a file to continue' : 'Enter a question to continue'}
                </p>
              )}
            </div>
          </div>

          {/* ─── Right: Guidance Panel ─── */}
          <div className="space-y-6">
            {/* How it works */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <h3 className="mb-4 text-sm font-semibold">How it works</h3>
              <div className="space-y-4">
                {STEPS.map((step, i) => (
                  <div key={step.title} className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                      <step.icon className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{step.title}</p>
                      <p className="text-xs text-muted-foreground">{step.desc}</p>
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className="ml-auto mt-2 text-muted-foreground/30">
                        <ArrowRight className="h-3 w-3" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Supported formats */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold">Supported formats</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2.5 rounded-md border bg-background p-2.5">
                  <FileSpreadsheet className="h-4 w-4 text-emerald-500" />
                  <div>
                    <p className="text-xs font-medium">CSV</p>
                    <p className="text-[10px] text-muted-foreground">Comma-separated values</p>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 rounded-md border bg-background p-2.5">
                  <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="text-xs font-medium">Excel (.xlsx)</p>
                    <p className="text-[10px] text-muted-foreground">Microsoft Excel workbook</p>
                  </div>
                </div>
              </div>
              <p className="mt-3 text-[10px] text-muted-foreground">
                Maximum file size: 100 MB • Up to 100,000 rows
              </p>
            </div>

            {/* What you get */}
            <div className="rounded-xl border bg-card p-6 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold">What you get</h3>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  Interactive report with charts & narrative
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  Downloadable PPTX slide deck
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  Key insights ranked by significance
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  Strategic recommendations
                </li>
              </ul>
            </div>

            {/* Running Instances link */}
            <Link
              href="/analysis/history"
              className="flex items-center gap-2 rounded-xl border bg-card p-4 text-sm font-medium shadow-sm transition-colors hover:border-primary/40 hover:bg-primary/5"
            >
              <History className="h-4 w-4 text-muted-foreground" />
              Running Instances
              <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
