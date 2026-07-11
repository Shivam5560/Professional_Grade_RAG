"use client";

import { Button } from "@/components/ui/button";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";
import { AppCard } from "./AppCard";

export function AppCatalog() {
  const catalog = useAppCatalog();

  if (catalog.status === "loading") {
    return (
      <div
        role="status"
        aria-label="Loading applications"
        aria-live="polite"
        className="rounded-2xl border border-border bg-card px-6 py-16 text-center text-sm text-muted-foreground"
      >
        Loading applications…
      </div>
    );
  }

  if (catalog.status === "error") {
    return (
      <section
        role="alert"
        className="rounded-2xl border border-destructive/40 bg-destructive/5 p-6"
      >
        <h2 className="font-semibold text-foreground">
          Application catalog unavailable
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {catalog.error.message}
        </p>
        <Button className="mt-4" onClick={() => void catalog.retry()}>
          Retry
        </Button>
      </section>
    );
  }

  if (catalog.status === "empty" || catalog.apps.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-border bg-card p-8 text-center sm:p-10">
        <h2 className="font-semibold text-foreground">
          No applications are enabled
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enable an application manifest to add it to this deployment.
        </p>
      </section>
    );
  }

  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {catalog.apps.map((app) => (
        <AppCard key={app.id} app={app} />
      ))}
    </div>
  );
}
