import Link from "next/link";

import type { AppManifest } from "@/lib/apps/types";
import { CapabilityBadge } from "./CapabilityBadge";

export function AppCard({ app }: { app: AppManifest }) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {app.category}
          </p>
          <h2 className="mt-2 text-xl font-semibold text-foreground">
            {app.name}
          </h2>
        </div>
        <span className="shrink-0 text-xs text-muted-foreground">
          v{app.version}
        </span>
      </div>

      <p className="mt-3 flex-1 text-sm leading-6 text-muted-foreground">
        {app.summary}
      </p>

      {app.required_capabilities.length > 0 ? (
        <ul
          className="mt-5 flex flex-wrap gap-2"
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
        className="mt-6 inline-flex w-fit rounded-sm font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        href={`/apps/${encodeURIComponent(app.id)}`}
      >
        Open {app.name}
      </Link>
    </article>
  );
}
