"use client";

import Link from "next/link";
import { Blocks, LayoutGrid } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CatalogState } from "@/lib/apps/useAppCatalog";
import {
  directApplicationRoute,
  presentationForApp,
} from "@/lib/presentation/registry";
import type { ApplicationPresentation } from "@/lib/presentation/types";

interface ApplicationSwitcherProps {
  catalog: CatalogState;
  activePresentation: ApplicationPresentation;
}

const safeRoute = /^\/(?!\/)/;

export function ApplicationSwitcher({
  catalog,
  activePresentation,
}: ApplicationSwitcherProps) {
  const applications =
    catalog.status === "success"
      ? catalog.apps.filter(
          (app) =>
            presentationForApp(app).id !== activePresentation.id &&
            safeRoute.test(directApplicationRoute(app)),
        )
      : [];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label="Switch application"
          className="inline-flex h-11 w-11 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          title="Switch application"
          type="button"
        >
          <LayoutGrid aria-hidden="true" className="h-5 w-5" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="center"
        className="mb-2 w-64 bg-background/95 backdrop-blur-xl"
        side="top"
      >
        <DropdownMenuLabel>Applications</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {applications.map((app) => (
          <DropdownMenuItem asChild key={app.id}>
            <Link
              className="flex min-w-0 items-center gap-2"
              href={directApplicationRoute(app)}
            >
              <Blocks
                aria-hidden="true"
                className="h-4 w-4 shrink-0 text-muted-foreground"
              />
              <span className="truncate">{app.name}</span>
            </Link>
          </DropdownMenuItem>
        ))}
        {catalog.status === "loading" ? (
          <DropdownMenuItem disabled>Loading applications</DropdownMenuItem>
        ) : null}
        {catalog.status === "error" ? (
          <DropdownMenuItem onSelect={() => void catalog.retry()}>
            Retry application catalog
          </DropdownMenuItem>
        ) : null}
        {(catalog.status === "empty" ||
          (catalog.status === "success" && applications.length === 0)) && (
          <DropdownMenuItem disabled>
            No additional applications
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
