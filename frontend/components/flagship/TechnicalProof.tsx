import { ReasoningThreads } from "@/components/brand/ReasoningThreads";
import { PROOF_POINTS } from "@/lib/flagship-content";

export function TechnicalProof() {
  return (
    <section id="proof" className="px-4 py-24 sm:px-6">
      <div className="mx-auto max-w-6xl motion-safe:animate-[reveal-up_.9s_ease_forwards]">
        <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">
          Technical proof
        </p>
        <h2 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
          Substance behind the surface.
        </h2>
        <div className="relative mt-12 overflow-hidden rounded-3xl border border-border bg-card">
          <ReasoningThreads className="h-48 border-b border-border opacity-70" />
          <dl className="grid gap-px bg-border md:grid-cols-2">
            {PROOF_POINTS.map(([term, detail]) => (
              <div key={term} className="bg-card p-7">
                <dt className="font-mono text-xs uppercase tracking-[.2em] text-[hsl(var(--copper))]">
                  {term}
                </dt>
                <dd className="mt-3 text-lg font-semibold">{detail}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}
