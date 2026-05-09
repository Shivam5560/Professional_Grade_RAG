'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { FileDropzone } from '@/components/analysis/FileDropzone';
import { AnalysisConfigAccordion } from '@/components/analysis/AnalysisConfigAccordion';
import { AnalysisConfig } from '@/lib/analysis/types';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

export default function AnalysisHubPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<AnalysisConfig>({
    max_rows: 50000,
    include_predictive: true,
    output_format: ['interactive', 'pptx'],
  });

  const handleSubmit = async () => {
    if (!file || !query.trim()) return;
    setLoading(true);

    try {
      // Step 1: Upload file via ApiClient (backend at port 8000)
      const uploadData = await apiClient.uploadAnalysisFile(file);

      if (!uploadData.source_id) {
        throw new Error('Upload failed');
      }

      // Step 2: Start analysis from uploaded file
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
      console.error('Failed to start analysis:', err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <div className="max-w-3xl mx-auto py-12 px-4">
      <h1 className="text-3xl font-bold mb-2">Data Analysis</h1>
      <p className="text-muted-foreground mb-8">Upload data, ask questions, get insights.</p>

      <div className="space-y-6">
        <FileDropzone onFileSelect={setFile} />
        {file && <p className="text-sm">Selected: {file.name}</p>}

        <Textarea
          placeholder="e.g., What are the key trends in revenue and which factors drive customer churn?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={4}
        />

        <AnalysisConfigAccordion config={config} onChange={setConfig} />

        <Button onClick={handleSubmit} disabled={!file || !query.trim() || loading} className="w-full">
          {loading ? 'Starting...' : 'Start Analysis'}
        </Button>
      </div>
      </div>
    </div>
  );
}
