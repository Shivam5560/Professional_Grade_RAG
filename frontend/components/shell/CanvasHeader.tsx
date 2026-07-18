import type { ReactNode } from "react";

export function CanvasHeader({
  eyebrow,
  title,
  description,
  status,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  status?: ReactNode;
  actions?: ReactNode;
}): JSX.Element {
  return (
    <header className="grid gap-5 border-b border-border/70 pb-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-end md:gap-8 md:pb-6">
      <div className="min-w-0">
        {(eyebrow || status) && (
          <div className="mb-2.5 flex min-h-5 flex-wrap items-center gap-x-3 gap-y-2">
            {eyebrow ? (
              <p className="text-[11px] font-semibold uppercase text-muted-foreground">
                {eyebrow}
              </p>
            ) : null}
            {status ? <div className="shrink-0">{status}</div> : null}
          </div>
        )}
        <h1 className="max-w-4xl text-balance text-2xl font-semibold leading-tight text-foreground sm:text-3xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground sm:text-[15px]">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex min-h-10 shrink-0 flex-wrap items-center gap-2 md:justify-end">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
