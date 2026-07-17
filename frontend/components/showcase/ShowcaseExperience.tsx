"use client";

import { useShowcase } from "./ShowcaseProvider";

export function ShowcaseExperience() {
  const { state, advance, restart } = useShowcase();
  const active = state.scenario.steps[state.activeStep];
  return (
    <main className="mx-auto grid max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[.75fr_1.25fr]">
      <section>
        <p className="font-mono text-xs uppercase tracking-[.22em] text-primary">{state.scenario.eyebrow}</p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-6xl">{state.scenario.title}</h1>
        <div className="mt-8 rounded-2xl border border-border bg-card p-5">
          <p className="text-xs uppercase tracking-wider text-muted-foreground">Prompt</p>
          <p className="mt-2 font-semibold">{state.scenario.prompt}</p>
        </div>
      </section>
      <section className="rounded-3xl border border-border bg-card p-6 sm:p-8">
        <ol className="grid grid-cols-3 gap-2">
          {state.scenario.steps.map((step, index) => (
            <li
              key={step.id}
              aria-current={index === state.activeStep ? "step" : undefined}
              className={`rounded-xl border p-3 ${
                index <= state.activeStep ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <span className="font-mono text-xs">{step.label}</span>
              <strong className="mt-2 block">{step.title}</strong>
            </li>
          ))}
        </ol>
        <div className="mt-8 min-h-56 rounded-2xl bg-muted p-6">
          <p className="font-mono text-xs uppercase tracking-[.18em] text-[hsl(var(--copper))]">{state.status}</p>
          <h2 className="mt-3 text-2xl font-bold">{active.title}</h2>
          <p className="mt-3 text-muted-foreground">{active.summary}</p>
          <ul className="mt-6 space-y-2">
            {active.evidence.map((item) => (
              <li key={item}>✓ {item}</li>
            ))}
          </ul>
        </div>
        <div className="mt-6 flex gap-3">
          <button
            onClick={advance}
            disabled={state.status === "complete"}
            className="rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50"
          >
            Continue demonstration
          </button>
          <button onClick={restart} className="rounded-full border border-border px-5 py-3 font-semibold">
            Restart
          </button>
        </div>
      </section>
    </main>
  );
}
