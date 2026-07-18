import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function FocusCanvas({
  ariaLabel,
  children,
  className,
}: {
  ariaLabel: string;
  children: ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <main
      aria-label={ariaLabel}
      className={cn(
        "relative min-h-[calc(100svh-2rem)] w-full overflow-x-clip pl-0 md:pl-[4.5rem]",
        className,
      )}
    >
      <div className="mx-auto flex w-full max-w-[100rem] flex-col px-4 pb-28 pt-5 sm:px-6 md:min-h-[calc(100svh-2rem)] md:px-8 md:pb-8 md:pt-7 lg:px-10">
        {children}
      </div>
    </main>
  );
}
