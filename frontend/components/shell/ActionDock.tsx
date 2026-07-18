import type { ReactNode } from "react";

export function ActionDock({
  primary,
  secondary,
}: {
  primary: ReactNode;
  secondary?: ReactNode;
}): JSX.Element {
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-40 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:sticky md:inset-auto md:bottom-4 md:mt-auto md:px-0 md:pb-0 md:pt-8">
      <div
        aria-label="Canvas actions"
        role="toolbar"
        className="pointer-events-auto mx-auto flex min-h-14 w-full max-w-3xl items-center justify-between gap-3 rounded-lg border border-border/70 bg-workspace-raised p-2 shadow-[0_18px_50px_-24px_hsl(var(--foreground)/0.35)] md:mx-0 md:ml-auto md:w-auto md:min-w-[20rem]"
      >
        {secondary ? (
          <div className="flex min-w-0 items-center gap-1.5">{secondary}</div>
        ) : (
          <span aria-hidden="true" />
        )}
        <div className="flex shrink-0 items-center gap-2">{primary}</div>
      </div>
    </div>
  );
}
