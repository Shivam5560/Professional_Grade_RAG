import Link from "next/link";

import { CAPABILITIES } from "@/lib/flagship-content";

export function CapabilityStory() {
  return (
    <section
      id="capabilities"
      className="border-y border-border/60 bg-card/40 px-4 py-24 sm:px-6"
    >
      <div className="mx-auto max-w-6xl motion-safe:animate-[reveal-up_.9s_ease_forwards]">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">
          One platform · Four outcomes
        </p>
        <h2 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Move from evidence to a finished decision.
        </h2>
        <div className="mt-14 divide-y divide-border/70">
          {CAPABILITIES.map((item, index) => (
            <article
              key={item.id}
              className="grid gap-6 py-9 md:grid-cols-[5rem_1fr_1fr_auto] md:items-center"
            >
              <span className="font-mono text-sm text-muted-foreground">
                0{index + 1}
              </span>
              <h3 className="text-2xl font-bold">{item.name}</h3>
              <div>
                <p className="text-muted-foreground">{item.statement}</p>
                <p className="mt-2 text-sm">{item.proof.join(" · ")}</p>
              </div>
              <Link
                className="rounded-sm font-semibold text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                href={item.showcaseHref}
              >
                Experience →
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
