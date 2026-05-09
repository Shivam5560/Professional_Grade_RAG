// frontend/components/analysis/HistoryTable.tsx
'use client';
import { AnalysisJob } from '@/lib/analysis/types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface Props {
  jobs: AnalysisJob[];
}

export function HistoryTable({ jobs }: Props) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Query</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow key={job.job_id}>
            <TableCell className="max-w-xs truncate" title={job.query}>{job.query}</TableCell>
            <TableCell>{job.progress_events[0]?.payload?.source_type || 'unknown'}</TableCell>
            <TableCell>
              <Badge variant={job.status === 'completed' ? 'default' : 'secondary'}>{job.status}</Badge>
            </TableCell>
            <TableCell>{new Date(job.created_at).toLocaleDateString()}</TableCell>
            <TableCell className="text-right">
              <Link href={`/analysis/${job.job_id}/report`}>
                <Button variant="ghost" size="sm">View</Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
