import Link from "next/link";
import { notFound } from "next/navigation";

import { CapabilityBadge } from "@/components/platform/CapabilityBadge";
import { CatalogHttpError, getApp } from "@/lib/apps/client";
import type { AppManifest } from "@/lib/apps/types";

async function loadApp(appId: string): Promise<AppManifest> {
  try {
    return await getApp(appId);
  } catch (error) {
    if (error instanceof CatalogHttpError && error.status === 404) {
      notFound();
    }

    throw error;
  }
}

export default async function AppOverviewPage({
  params,
}: {
  params: { appId: string };
}) {
  const app = await loadApp(params.appId);

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Link
        href="/apps"
        className="inline-flex rounded-sm text-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        ← All applications
      </Link>

      <h1 className="mt-6 text-4xl font-semibold tracking-tight text-foreground">
        {app.name}
      </h1>
      <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
        {app.summary}
      </p>

      {app.required_capabilities.length > 0 ? (
        <ul
          className="mt-6 flex flex-wrap gap-2"
          aria-label={`${app.name} capabilities`}
        >
          {app.required_capabilities.map((capability) => (
            <li key={capability}>
              <CapabilityBadge capability={capability} />
            </li>
          ))}
        </ul>
      ) : null}

      <Link
        href={app.frontend_route}
        className="mt-8 inline-flex rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        Launch {app.name}
      </Link>

      <section className="mt-12" aria-labelledby="demo-scenarios">
        <h2 id="demo-scenarios" className="text-2xl font-semibold text-foreground">
          Guided scenarios
        </h2>

        {app.demo_scenarios.length > 0 ? (
          <ul className="mt-5 grid gap-4 md:grid-cols-2">
            {app.demo_scenarios.map((scenario) => (
              <li key={scenario.id}>
                <article className="h-full rounded-xl border border-border bg-card p-5">
                  <h3 className="font-semibold text-foreground">
                    {scenario.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {scenario.description}
                  </p>
                  <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-words rounded-lg bg-muted p-3 text-xs text-foreground">
                    {scenario.starter_prompt}
                  </pre>
                </article>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-5 rounded-xl border border-dashed border-border bg-card p-5 text-sm text-muted-foreground">
            No guided scenarios are available for this application yet.
          </p>
        )}
      </section>
    </main>
  );
}
