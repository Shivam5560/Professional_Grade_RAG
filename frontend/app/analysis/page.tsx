'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropzone } from '@/components/analysis/FileDropzone';
import { AnalysisConfigAccordion } from '@/components/analysis/AnalysisConfigAccordion';
import { AnalysisConfig } from '@/lib/analysis/types';
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
      // Step 1: Upload file
      const uploadForm = new FormData();
      uploadForm.append('file', file);

      const uploadRes = await fetch('/api/v1/analysis/upload', {
        method: 'POST',
        body: uploadForm,
      });
      const uploadData = await uploadRes.json();

      if (!uploadData.source_id) {
        throw new Error(uploadData.detail || 'Upload failed');
      }

      // Step 2: Start analysis from uploaded file
      const startRes = await fetch(`/api/v1/analysis/from-upload?source_id=${encodeURIComponent(uploadData.source_id)}&query=${encodeURIComponent(query)}&config=${encodeURIComponent(JSON.stringify(config))}`, {
        method: 'POST',
      });
      const startData = await startRes.json();

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
  );
}
