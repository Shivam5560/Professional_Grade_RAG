import Link from "next/link";

import { NexusAperture } from "@/components/brand/NexusAperture";
import { PublicFooter } from "@/components/flagship/PublicFooter";
import { PublicHeader } from "@/components/flagship/PublicHeader";
import { CREATOR_PROFILE } from "@/lib/creator-profile";

const architecture = [
  ["Knowledge", "Hybrid retrieval, reranking, citations, and confidence."],
  ["AuraSQL", "Schema context, query generation, validation, and results."],
  ["Analysis", "Specialized agents, persistent jobs, charts, and reports."],
  ["Career Studio", "Resume evidence, JD alignment, review, and export."],
] as const;

export default function DeveloperPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <PublicHeader />
      <main className="pt-16">
        <section className="px-4 py-24 sm:px-6">
          <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1fr_.7fr] lg:items-center">
            <div>
              <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">
                Creator and engineer
              </p>
              <h1 className="mt-5 text-5xl font-black tracking-[-.055em] sm:text-7xl">
                {CREATOR_PROFILE.name}
              </h1>
              <p className="mt-4 text-lg text-[hsl(var(--copper))]">
                {CREATOR_PROFILE.role}
              </p>
              <p className="mt-7 max-w-3xl text-lg leading-8 text-muted-foreground">
                {CREATOR_PROFILE.ownership}
              </p>
              <div className="mt-9 flex gap-3">
                <Link
                  className="rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground"
                  href="/"
                >
                  View product
                </Link>
                <Link
                  className="rounded-full border border-border px-5 py-3 font-semibold"
                  href="/showcase"
                >
                  Explore showcase
                </Link>
              </div>
              <nav
                aria-label="Creator links"
                className="mt-6 flex gap-5 text-sm font-semibold text-muted-foreground"
              >
                {CREATOR_PROFILE.links.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {link.label}
                  </a>
                ))}
              </nav>
            </div>
            <NexusAperture className="mx-auto w-64" />
          </div>
        </section>

        <section className="border-y border-border bg-card/50 px-4 py-20 sm:px-6">
          <div className="mx-auto grid max-w-7xl gap-px overflow-hidden rounded-3xl border border-border bg-border md:grid-cols-2">
            {CREATOR_PROFILE.areas.map((area) => (
              <article key={area.title} className="bg-card p-8">
                <h2 className="text-2xl font-bold">{area.title}</h2>
                <p className="mt-3 leading-7 text-muted-foreground">
                  {area.detail}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="px-4 py-24 sm:px-6">
          <div className="mx-auto max-w-7xl">
            <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">
              System architecture
            </p>
            <h2 className="mt-4 text-4xl font-bold">
              One platform, four specialist experiences.
            </h2>
            <div className="mt-12 divide-y divide-border">
              {architecture.map(([name, detail]) => (
                <article
                  key={name}
                  className="grid gap-3 py-6 md:grid-cols-[12rem_1fr]"
                >
                  <h3 className="text-xl font-bold">{name}</h3>
                  <p className="text-muted-foreground">{detail}</p>
                </article>
              ))}
            </div>
            <div className="mt-16 rounded-3xl bg-foreground p-8 text-background">
              <h2 className="text-3xl font-bold">Engineering principles</h2>
              <ul className="mt-6 grid gap-4 sm:grid-cols-2">
                {CREATOR_PROFILE.principles.map((principle) => (
                  <li
                    key={principle}
                    className="border-l-2 border-[hsl(var(--copper))] pl-4"
                  >
                    {principle}
                  </li>
                ))}
              </ul>
              <p className="mt-8 max-w-3xl text-sm leading-7 opacity-70">
                Built with Next.js, React, TypeScript, FastAPI, PostgreSQL,
                pgvector, LlamaIndex, containerized services, and production
                observability.
              </p>
            </div>
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
