'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowRight,
  BarChart3,
  FileSpreadsheet,
  History,
  Lightbulb,
  MessageSquare,
  Sparkles,
  Upload,
} from 'lucide-react';
import { FileDropzone } from '@/components/analysis/FileDropzone';
import { AnalysisConfigAccordion } from '@/components/analysis/AnalysisConfigAccordion';
import { PageShell, SectionPanel } from '@/components/layout/PageShell';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ErrorState, LoadingOverlay } from '@/components/ui/loading-state';
import { apiClient } from '@/lib/api';
import { useAnalysisStore } from '@/lib/analysis/store';
import { useJobs } from '@/components/providers/JobProvider';
import type { AnalysisConfig } from '@/lib/analysis/types';

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
  { icon: Sparkles, title: 'Insights', desc: 'AI analyzes and generates a report' },
];

const OUTPUTS = [
  'Interactive report with charts and narrative',
  'Downloadable PPTX slide deck',
  'Key insights ranked by significance',
  'Strategic recommendations',
];

export default function AnalysisHubPage() {
  const router = useRouter();
  const { reset } = useAnalysisStore();
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<AnalysisConfig>({
    max_rows: 50000,
    include_predictive: true,
    output_format: ['interactive', 'pptx'],
  });

  const { addJob, removeJob, isJobActive } = useJobs();
  const isStartingAnalysis = isJobActive('start_analysis');

  useEffect(() => {
    reset();
  }, [reset]);

  const handleSubmit = async () => {
    if (!file || !query.trim() || isStartingAnalysis) return;
    setError(null);

    const tempJobId = `temp_uploading_${Date.now()}`;
    addJob({ id: tempJobId, type: 'start_analysis', status: 'running' });

    try {
      const uploadData = await apiClient.uploadAnalysisFile(file);
      if (!uploadData.source_id) throw new Error('Upload failed - no source ID returned');

      const startData = await apiClient.startAnalysisFromUpload({
        source_id: uploadData.source_id,
        query,
        config: config as unknown as Record<string, unknown>,
      });

      if (startData.job_id) {
        addJob({ id: startData.job_id, type: 'start_analysis', status: 'running' });
        router.push(`/analysis/${startData.job_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
      console.error('Failed to start analysis:', err);
    } finally {
      removeJob(tempJobId);
    }
  };

  const isReady = Boolean(file && query.trim().length > 0);

  return (
    <PageShell
      title="Data Storyteller"
      eyebrow="Analysis workflow"
      description="Upload a spreadsheet, ask a focused question, and let the analysis agents produce insights and a report."
      actions={
        <Button variant="outline" asChild>
          <Link href="/analysis/history" className="gap-2">
            <History className="h-4 w-4" />
            History
          </Link>
        </Button>
      }
      maxWidth="6xl"
    >
      {isStartingAnalysis ? (
        <LoadingOverlay
          title="Starting analysis"
          description="Uploading your file and spawning the analysis agents."
        />
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <SectionPanel>
            <div className="mb-4 flex items-center gap-2">
              <StepNumber value={1} />
              <h2 className="text-sm font-semibold">Upload your data</h2>
            </div>
            <FileDropzone onFileSelect={setFile} selectedFile={file} />
          </SectionPanel>

          <SectionPanel>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <StepNumber value={2} />
                <h2 className="text-sm font-semibold">Ask the business question</h2>
              </div>
              {query.length > 0 ? <span className="text-xs text-muted-foreground">{query.length} chars</span> : null}
            </div>
            <Textarea
              id="analysis-query"
              placeholder="e.g., What are the key trends in revenue and which factors drive customer churn?"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={5}
              className="resize-none"
            />

            <div className="mt-4">
              <p className="mb-2 text-xs font-medium text-muted-foreground">Sample prompts</p>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_QUERIES.map((sample) => (
                  <button
                    key={sample.label}
                    onClick={() => setQuery(sample.query)}
                    className="inline-flex items-center gap-1.5 rounded-md border bg-background px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <sample.icon className="h-3 w-3" />
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>
          </SectionPanel>

          <SectionPanel>
            <div className="mb-4 flex items-center gap-2">
              <StepNumber value={3} />
              <h2 className="text-sm font-semibold">Configure and run</h2>
            </div>

            <AnalysisConfigAccordion config={config} onChange={setConfig} />

            {error ? <ErrorState className="mt-4" title="Analysis could not start" description={error} /> : null}

            <Button
              id="start-analysis-btn"
              onClick={handleSubmit}
              disabled={!isReady || isStartingAnalysis}
              className="mt-4 w-full gap-2"
              size="lg"
            >
              {isStartingAnalysis ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Uploading and starting
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Start Analysis
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>

            {!isReady && !isStartingAnalysis ? (
              <p className="mt-2 text-center text-xs text-muted-foreground">
                {!file ? 'Upload a file to continue' : 'Enter a question to continue'}
              </p>
            ) : null}
          </SectionPanel>
        </div>

        <aside className="space-y-5">
          <SectionPanel>
            <h3 className="mb-4 text-sm font-semibold">How it works</h3>
            <div className="space-y-4">
              {STEPS.map((step) => (
                <div key={step.title} className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                    <step.icon className="h-4 w-4 text-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{step.title}</p>
                    <p className="text-xs text-muted-foreground">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </SectionPanel>

          <SectionPanel>
            <h3 className="mb-3 text-sm font-semibold">Supported formats</h3>
            <div className="space-y-2">
              {['CSV', 'Excel (.xlsx)'].map((format) => (
                <div key={format} className="flex items-center gap-2.5 rounded-md border bg-background p-2.5">
                  <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                  <p className="text-xs font-medium">{format}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">Maximum file size: 100 MB. Up to 100,000 rows.</p>
          </SectionPanel>

          <SectionPanel>
            <h3 className="mb-3 text-sm font-semibold">Outputs</h3>
            <ul className="space-y-2 text-xs text-muted-foreground">
              {OUTPUTS.map((output) => (
                <li key={output} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/60" />
                  {output}
                </li>
              ))}
            </ul>
          </SectionPanel>
        </aside>
      </div>
    </PageShell>
  );
}

function StepNumber({ value }: { value: number }) {
  return (
    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-muted text-xs font-semibold text-foreground">
      {value}
    </span>
  );
}
