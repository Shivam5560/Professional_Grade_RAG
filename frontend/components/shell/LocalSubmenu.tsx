"use client";

import Link from "next/link";

import type { ApplicationPresentation } from "@/lib/presentation/types";
import { cn } from "@/lib/utils";

interface LocalSubmenuProps {
  pathname: string;
  presentation: ApplicationPresentation;
}

export function LocalSubmenu({
  pathname,
  presentation,
}: LocalSubmenuProps) {
  if (presentation.localDestinations.length === 0) {
    return null;
  }

  return (
    <div className="sticky top-0 z-40 border-b border-border/60 bg-workspace-raised px-3 md:ml-20 md:border-b-0 md:bg-transparent md:px-0 md:pt-3">
      <nav
        aria-label={`${presentation.name} sections`}
        className="flex min-h-12 items-center gap-1 overflow-x-auto overscroll-x-contain [scrollbar-width:none] md:mr-3 md:w-fit md:rounded-md md:border md:border-border/70 md:bg-workspace-raised md:px-1.5 md:shadow-sm [&::-webkit-scrollbar]:hidden"
      >
        {presentation.localDestinations.map((item) => {
          const active = item.matches(pathname);
          const Icon = item.icon;

          return (
            <Link
              aria-current={active ? "page" : undefined}
              aria-label={`${presentation.shortName} ${item.label.toLowerCase()}`}
              className={cn(
                "inline-flex h-9 shrink-0 items-center gap-2 rounded-md px-3 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
              href={item.href}
              key={item.href}
            >
              <Icon aria-hidden="true" className="h-3.5 w-3.5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
