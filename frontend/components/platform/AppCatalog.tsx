"use client";

import { RefreshCw } from "lucide-react";

import { CinematicAppGallery } from "@/components/platform/CinematicAppGallery";
import { Button } from "@/components/ui/button";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";

const stateFrame =
  "relative flex min-h-[calc(100svh-2rem)] w-full items-center overflow-hidden px-5 pb-24 pt-16 md:px-12 md:py-16";

export function AppCatalog(): JSX.Element {
  const catalog = useAppCatalog();

  if (catalog.status === "loading") {
    return (
      <main aria-label="Application dashboard" className={stateFrame}>
        <div
          aria-label="Loading applications"
          aria-live="polite"
          className="w-full max-w-2xl"
          role="status"
        >
          <div className="h-3 w-28 rounded-sm bg-muted-foreground/20 motion-safe:animate-pulse" />
          <div className="mt-7 h-12 w-full max-w-xl rounded-md bg-muted-foreground/15 motion-safe:animate-pulse" />
          <div className="mt-3 h-12 w-4/5 max-w-md rounded-md bg-muted-foreground/15 motion-safe:animate-pulse" />
          <div className="mt-7 h-4 w-full max-w-lg rounded-sm bg-muted-foreground/10 motion-safe:animate-pulse" />
          <div className="mt-3 h-4 w-3/4 max-w-sm rounded-sm bg-muted-foreground/10 motion-safe:animate-pulse" />
          <span className="sr-only">Loading applications</span>
        </div>
      </main>
    );
  }

  if (catalog.status === "error") {
    return (
      <main aria-label="Application dashboard" className={stateFrame}>
        <section aria-labelledby="catalog-error" className="max-w-lg" role="alert">
          <p className="text-xs font-semibold uppercase text-destructive">Catalog offline</p>
          <h1 id="catalog-error" className="mt-3 text-3xl font-semibold leading-tight text-foreground sm:text-4xl">
            Application catalog unavailable
          </h1>
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            The workspace directory could not be reached. Retry the connection to continue.
          </p>
          <Button className="mt-7 gap-2" onClick={() => void catalog.retry()} type="button">
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
            Retry
          </Button>
        </section>
      </main>
    );
  }

  if (catalog.status === "empty" || catalog.apps.length === 0) {
    return (
      <main aria-label="Application dashboard" className={stateFrame}>
        <section aria-labelledby="catalog-empty" className="max-w-lg">
          <p className="text-xs font-semibold uppercase text-muted-foreground">No workspaces</p>
          <h1 id="catalog-empty" className="mt-3 text-3xl font-semibold leading-tight text-foreground sm:text-4xl">
            No applications are enabled
          </h1>
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            Ask an administrator to enable an application manifest for this deployment.
          </p>
        </section>
      </main>
    );
  }

  return <CinematicAppGallery apps={catalog.apps} />;
}
