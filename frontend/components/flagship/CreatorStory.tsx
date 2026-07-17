import Link from "next/link";

import { CREATOR_PROFILE } from "@/lib/creator-profile";

export function CreatorStory() {
  return (
    <section id="creator" className="px-4 py-24 sm:px-6">
      <div className="mx-auto grid max-w-6xl gap-8 rounded-[2rem] bg-foreground p-8 text-background motion-safe:animate-[reveal-up_.9s_ease_forwards] sm:p-12 lg:grid-cols-[.8fr_1.2fr]">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-[hsl(var(--copper))]">
          The creator behind the system
        </p>
        <div>
          <h2 className="text-4xl font-bold tracking-tight">
            Built end to end by {CREATOR_PROFILE.name}
          </h2>
          <p className="mt-5 max-w-2xl leading-7 opacity-70">
            {CREATOR_PROFILE.ownership}
          </p>
          <Link
            className="mt-7 inline-flex rounded-sm font-semibold text-[hsl(var(--signal))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--signal))] focus-visible:ring-offset-2 focus-visible:ring-offset-foreground"
            href="/developer"
          >
            Read the engineering story →
          </Link>
        </div>
      </div>
    </section>
  );
}
