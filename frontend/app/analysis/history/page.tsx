// frontend/app/analysis/history/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { AnalysisJob } from '@/lib/analysis/types';
import { HistoryTable } from '@/components/analysis/HistoryTable';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function AnalysisHistoryPage() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = () => {
    apiClient.listAnalysisJobs()
      .then((data) => {
        setJobs((data.jobs || []) as unknown as AnalysisJob[]);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this analysis instance and all associated charts/reports?')) return;
    try {
      await apiClient.deleteAnalysisJob(jobId);
      setJobs((prev) => prev.filter((job) => job.job_id !== jobId));
    } catch (e) {
      console.error('Failed to delete analysis instance:', e);
      alert('Failed to delete analysis instance.');
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Running Instances</h1>
        <Link href="/analysis">
          <Button>New Analysis</Button>
        </Link>
      </div>
      {loading ? <p>Loading...</p> : <HistoryTable jobs={jobs} onDelete={handleDelete} />}
      </div>
    </div>
  );
}
