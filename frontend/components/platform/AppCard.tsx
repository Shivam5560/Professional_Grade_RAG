"use client";

import {
  BarChart3,
  BookOpen,
  Briefcase,
  Database,
  PanelLeft,
} from "lucide-react";

import type { AppManifest } from "@/lib/apps/types";
import { presentationForApp } from "@/lib/presentation/registry";
import { cn } from "@/lib/utils";

const applicationIcons = {
  "knowledge-studio": BookOpen,
  aurasql: Database,
  analysis: BarChart3,
  "career-studio": Briefcase,
} as const;

export function AppCard({
  app,
  active,
  index,
  onSelect,
}: {
  app: AppManifest;
  active: boolean;
  index: number;
  onSelect(): void;
}): JSX.Element {
  const presentation = presentationForApp(app);
  const Icon = applicationIcons[app.id as keyof typeof applicationIcons] ?? PanelLeft;

  return (
    <button
      aria-label={`Feature ${app.name}`}
      aria-pressed={active}
      className={cn(
        "group flex h-[4.75rem] w-[13.5rem] shrink-0 items-center gap-3 rounded-lg border px-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background sm:w-[15rem]",
        active
          ? "border-foreground/45 bg-foreground text-background"
          : "border-border/70 bg-background/65 text-foreground backdrop-blur-md hover:border-foreground/30 hover:bg-background/85",
      )}
      onClick={onSelect}
      type="button"
    >
      <span
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-md border",
          active
            ? "border-background/20 bg-background/10"
            : "border-border/70 bg-muted/55 text-muted-foreground group-hover:text-foreground",
        )}
      >
        <Icon aria-hidden="true" className="h-[1.125rem] w-[1.125rem]" />
      </span>
      <span className="min-w-0 flex-1">
        <span className={cn("block text-[10px] font-semibold", active ? "text-background/60" : "text-muted-foreground")}>
          {String(index + 1).padStart(2, "0")} / {app.category}
        </span>
        <span className="mt-1 block truncate text-sm font-semibold">
          {presentation.shortName}
        </span>
      </span>
    </button>
  );
}
