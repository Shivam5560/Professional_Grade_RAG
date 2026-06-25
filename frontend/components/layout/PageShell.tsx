import type { ReactNode } from 'react';
import { Header } from '@/components/layout/Header';
import { cn } from '@/lib/utils';

type PageShellProps = {
  title?: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  maxWidth?: '5xl' | '6xl' | '7xl' | 'full';
  className?: string;
  contentClassName?: string;
};

const maxWidthClass = {
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  '7xl': 'max-w-7xl',
  full: 'max-w-none',
};

export function PageShell({
  title,
  description,
  eyebrow,
  actions,
  children,
  maxWidth = '6xl',
  className,
  contentClassName,
}: PageShellProps) {
  return (
    <div className={cn('min-h-screen bg-background text-foreground', className)}>
      <Header />
      <main className={cn('mx-auto w-full px-4 py-6 md:px-8 md:py-8', maxWidthClass[maxWidth], contentClassName)}>
        {(title || description || eyebrow || actions) && (
          <div className="mb-6 flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-end md:justify-between">
            <div className="space-y-1">
              {eyebrow ? (
                <p className="text-xs font-semibold uppercase text-muted-foreground">{eyebrow}</p>
              ) : null}
              {title ? <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1> : null}
              {description ? <p className="max-w-3xl text-sm text-muted-foreground">{description}</p> : null}
            </div>
            {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}

export function SectionPanel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn('rounded-lg border border-border bg-card p-5 shadow-sm md:p-6', className)}>
      {children}
    </section>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  className,
}: {
  label: string;
  value: string | number;
  detail?: string;
  className?: string;
}) {
  return (
    <div className={cn('rounded-lg border border-border bg-card p-4', className)}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
      {detail ? <p className="mt-1 text-xs text-muted-foreground">{detail}</p> : null}
    </div>
  );
}
