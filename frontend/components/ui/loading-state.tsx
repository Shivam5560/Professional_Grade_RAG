import { Loader2 } from 'lucide-react';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type LoadingStateProps = {
  title?: string;
  description?: string;
  className?: string;
};

export function LoadingState({
  title = 'Loading',
  description = 'Please wait while this finishes.',
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex min-h-[220px] items-center justify-center rounded-lg border border-border bg-card p-6 text-center',
        className
      )}
      role="status"
      aria-live="polite"
    >
      <div className="space-y-3">
        <Loader2 className="mx-auto h-6 w-6 animate-spin text-muted-foreground" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="max-w-sm text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}

export function LoadingOverlay({
  title = 'Working',
  description = 'This may take a moment.',
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn('fixed inset-0 z-50 flex items-center justify-center bg-background/75 p-4 backdrop-blur-sm', className)}
      role="status"
      aria-live="polite"
    >
      <LoadingState title={title} description={description} className="min-h-0 w-full max-w-sm shadow-lg" />
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('rounded-lg border border-dashed border-border bg-card p-6 text-center', className)}>
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description ? <p className="mx-auto mt-1 max-w-md text-xs text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title = 'Something went wrong',
  description,
  className,
}: {
  title?: string;
  description: string;
  className?: string;
}) {
  return (
    <div className={cn('rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm', className)}>
      <p className="font-medium text-destructive">{title}</p>
      <p className="mt-1 text-xs text-destructive/90">{description}</p>
    </div>
  );
}
