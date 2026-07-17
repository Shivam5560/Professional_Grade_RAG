import Link from "next/link";
import { ShowcaseShell } from "@/components/showcase/ShowcaseShell";
import { SHOWCASE_SCENARIOS } from "@/lib/showcase/fixtures";

export default function ShowcasePage() {
  return (
    <ShowcaseShell>
      <main className="mx-auto max-w-7xl px-4 py-20">
        <p className="font-mono text-xs uppercase tracking-[.22em] text-primary">Choose a guided outcome</p>
        <h1 className="mt-4 max-w-4xl text-5xl font-bold tracking-tight">
          Explore the system without infrastructure or credentials.
        </h1>
        <div className="mt-12 grid gap-5 md:grid-cols-2">
          {Object.values(SHOWCASE_SCENARIOS).map((scenario) => (
            <Link
              key={scenario.id}
              href={`/showcase/${scenario.id}`}
              className="rounded-3xl border border-border bg-card p-7"
            >
              <span className="font-mono text-xs uppercase tracking-wider text-[hsl(var(--copper))]">
                {scenario.eyebrow}
              </span>
              <h2 className="mt-3 text-2xl font-bold">{scenario.title}</h2>
              <p className="mt-4 text-muted-foreground">{scenario.prompt}</p>
            </Link>
          ))}
        </div>
      </main>
    </ShowcaseShell>
  );
}
