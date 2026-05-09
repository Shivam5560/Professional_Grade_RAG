// frontend/app/analysis/history/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { AnalysisJob } from '@/lib/analysis/types';
import { HistoryTable } from '@/components/analysis/HistoryTable';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function AnalysisHistoryPage() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/analysis')
      .then((res) => res.json())
      .then((data) => {
        setJobs(data.jobs || []);
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Analysis History</h1>
        <Link href="/analysis">
          <Button>New Analysis</Button>
        </Link>
      </div>
      {loading ? <p>Loading...</p> : <HistoryTable jobs={jobs} />}
    </div>
  );
}
