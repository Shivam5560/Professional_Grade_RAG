// frontend/components/analysis/HistoryTable.tsx
'use client';
import { AnalysisJob } from '@/lib/analysis/types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Trash2 } from 'lucide-react';

interface Props {
  jobs: AnalysisJob[];
  onDelete?: (jobId: string) => void;
}

export function HistoryTable({ jobs, onDelete }: Props) {
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
            <TableCell>{(job.progress_events[0]?.payload?.source_type as string) || 'unknown'}</TableCell>
            <TableCell>
              <Badge variant={
                job.status === 'completed' ? 'default' :
                job.status === 'failed' ? 'destructive' :
                job.status === 'running' ? 'secondary' : 'outline'
              } className={
                job.status === 'completed' ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-100 border-transparent dark:bg-emerald-900/30 dark:text-emerald-300' :
                job.status === 'failed' ? 'bg-rose-100 text-rose-800 hover:bg-rose-100 border-transparent dark:bg-rose-900/30 dark:text-rose-300' :
                job.status === 'running' ? 'bg-blue-100 text-blue-800 hover:bg-blue-100 border-transparent dark:bg-blue-900/30 dark:text-blue-300 animate-pulse' :
                ''
              }>
                {job.status}
              </Badge>
            </TableCell>
            <TableCell>{new Date(job.created_at).toLocaleDateString()}</TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-1">
                <Link href={job.status === 'completed' ? `/analysis/${job.job_id}/report` : `/analysis/${job.job_id}`}>
                  <Button variant="ghost" size="sm">
                    {job.status === 'completed' ? 'View' : 'Monitor'}
                  </Button>
                </Link>
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    onClick={() => onDelete(job.job_id)}
                    title="Delete instance"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
