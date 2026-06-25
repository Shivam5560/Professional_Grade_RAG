'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Activity, CheckCircle2, ChevronRight, Clock, Loader2, X, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useJobs, type Job } from '@/components/providers/JobProvider';
import { cn, formatTimestamp } from '@/lib/utils';

const activeStatuses = new Set<Job['status']>(['pending', 'running']);

const defaultTitleByType: Record<string, string> = {
  start_analysis: 'Starting analysis',
  analysis: 'Analysis workflow',
  document_upload: 'Document upload',
  upload_resume: 'Document upload',
  auto_tailor: 'Auto-Tailor workflow',
  aurasql: 'AuraSQL task',
};

export function JobCenter() {
  const router = useRouter();
  const { activeJobs, removeJob } = useJobs();
  const [open, setOpen] = useState(false);

  const sortedJobs = useMemo(
    () =>
      [...activeJobs].sort((a, b) => {
        const aTime = new Date(a.createdAt || 0).getTime();
        const bTime = new Date(b.createdAt || 0).getTime();
        return bTime - aTime;
      }),
    [activeJobs]
  );

  const activeCount = sortedJobs.filter((job) => activeStatuses.has(job.status)).length;

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen((prev) => !prev)}
        className="relative gap-2 text-muted-foreground hover:text-foreground"
        aria-label="Open job center"
      >
        {activeCount > 0 ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
        <span className="hidden xl:inline">Jobs</span>
        {activeCount > 0 ? (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-foreground px-1 text-[10px] font-semibold text-background">
            {activeCount}
          </span>
        ) : null}
      </Button>

      {open ? (
        <div className="absolute right-0 top-full z-50 mt-2 w-[min(380px,calc(100vw-2rem))] rounded-lg border border-border bg-background p-3 shadow-xl">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-foreground">Job Center</p>
              <p className="text-xs text-muted-foreground">
                {activeCount > 0 ? `${activeCount} active operation${activeCount === 1 ? '' : 's'}` : 'No active operations'}
              </p>
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="max-h-[420px] space-y-2 overflow-y-auto">
            {sortedJobs.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-4 text-center">
                <p className="text-sm font-medium">Nothing running</p>
                <p className="mt-1 text-xs text-muted-foreground">Long-running uploads and workflows will appear here.</p>
              </div>
            ) : (
              sortedJobs.map((job) => (
                <JobCenterRow
                  key={job.id}
                  job={job}
                  onOpen={() => {
                    if (job.href) {
                      router.push(job.href);
                      setOpen(false);
                    }
                  }}
                  onDismiss={() => removeJob(job.id)}
                />
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function JobCenterRow({
  job,
  onOpen,
  onDismiss,
}: {
  job: Job;
  onOpen: () => void;
  onDismiss: () => void;
}) {
  const title = job.title || defaultTitleByType[job.type] || job.type;
  const description = job.message || job.description;
  const canOpen = Boolean(job.href);
  const isActive = activeStatuses.has(job.status);

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          {job.status === 'error' ? (
            <XCircle className="h-4 w-4 text-destructive" />
          ) : job.status === 'success' ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : isActive ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <Clock className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">{title}</p>
              {description ? <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{description}</p> : null}
            </div>
            <span
              className={cn(
                'rounded-md px-1.5 py-0.5 text-[10px] font-medium uppercase',
                job.status === 'error'
                  ? 'bg-destructive/10 text-destructive'
                  : job.status === 'success'
                  ? 'bg-emerald-500/10 text-emerald-500'
                  : 'bg-muted text-muted-foreground'
              )}
            >
              {job.status}
            </span>
          </div>

          {typeof job.progress === 'number' ? (
            <Progress value={Math.max(0, Math.min(100, job.progress))} className="mt-3 h-1.5" />
          ) : null}

          <div className="mt-3 flex items-center justify-between gap-2">
            <p className="text-[11px] text-muted-foreground">{job.createdAt ? formatTimestamp(job.createdAt) : 'Just now'}</p>
            <div className="flex items-center gap-1">
              {!isActive ? (
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={onDismiss}>
                  Dismiss
                </Button>
              ) : null}
              {canOpen ? (
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={onOpen}>
                  Open
                  <ChevronRight className="ml-1 h-3 w-3" />
                </Button>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
