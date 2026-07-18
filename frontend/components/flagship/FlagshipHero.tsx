"use client";

import dynamic from "next/dynamic";
import { ArrowRight } from "lucide-react";

import { NexusAperture } from "@/components/brand/NexusAperture";
import { useCinematicEffects } from "@/hooks/useCinematicEffects";

const CinematicScene = dynamic(
  () => import("@/components/brand/CinematicScene"),
  { ssr: false },
);

const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";

export function FlagshipHero() {
  const { enabled, visible } = useCinematicEffects();

  return (
    <section className="relative isolate flex min-h-[92svh] items-center overflow-hidden px-4 pb-20 pt-28 sm:px-6">
      {enabled ? <CinematicScene active={visible} /> : null}
      <div className="mx-auto grid w-full max-w-6xl items-center gap-14 lg:grid-cols-[1.1fr_.9fr]">
        <div className="relative z-10 motion-safe:animate-[reveal-up_.9s_ease_forwards]">
          <p className="font-mono text-xs font-semibold uppercase tracking-[.28em] text-[hsl(var(--signal))]">
            A system for serious thinking
          </p>
          <h1
            aria-label="Intelligence, made tangible."
            className="mt-6 max-w-4xl text-5xl font-black leading-[.92] tracking-[-.06em] sm:text-7xl lg:text-8xl"
          >
            Intelligence,
            <br />
            <em className="font-editorial font-normal text-[hsl(var(--copper))]">
              made tangible.
            </em>
          </h1>
          <p className="mt-7 max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
            Grounded research, data intelligence, and high-stakes output in one authored system.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => window.dispatchEvent(new CustomEvent("nexusmind:auth", { detail: "login" }))}
              className={`inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground transition-opacity hover:opacity-90 ${focusRing}`}
            >
              Enter the workspace <ArrowRight aria-hidden className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => document.querySelector("#capabilities")?.scrollIntoView({ behavior: "smooth" })}
              className={`rounded-full border border-border px-5 py-3 font-semibold transition-colors hover:bg-muted ${focusRing}`}
            >
              Explore capabilities
            </button>
          </div>
        </div>
        <div className="relative mx-auto grid min-h-80 w-full place-items-center motion-safe:animate-[reveal-up_1.1s_ease_forwards]">
          <NexusAperture className="w-72 sm:w-96" />
        </div>
      </div>
    </section>
  );
}
