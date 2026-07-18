"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { AppCard } from "@/components/platform/AppCard";
import { DashboardSignal } from "@/components/platform/DashboardSignal";
import { useCinematicEffects } from "@/hooks/useCinematicEffects";
import type { AppManifest } from "@/lib/apps/types";
import { motionTokens } from "@/lib/motion";
import {
  directApplicationRoute,
  presentationForApp,
} from "@/lib/presentation/registry";

export function CinematicAppGallery({ apps }: { apps: AppManifest[] }): JSX.Element {
  const [activeIndex, setActiveIndex] = useState(0);
  const reduceMotion = useReducedMotion();
  const effects = useCinematicEffects();
  const animated = effects.enabled && effects.visible && !reduceMotion;
  const safeIndex = Math.min(activeIndex, apps.length - 1);
  const activeApp = apps[safeIndex];
  const presentation = presentationForApp(activeApp);
  const transition = animated
    ? { duration: 0.58, ease: motionTokens.ease }
    : { duration: 0 };

  return (
    <main
      aria-label="Application dashboard"
      className="relative min-h-[calc(100svh-2rem)] w-full overflow-hidden bg-background"
    >
      <AnimatePresence initial={false} mode="sync">
        <motion.div
          key={`media-${activeApp.id}`}
          initial={animated ? { opacity: 0, scale: 1.025 } : false}
          animate={{ opacity: 1, scale: 1 }}
          exit={animated ? { opacity: 0 } : undefined}
          transition={transition}
          className="absolute inset-0"
        >
          <Image
            alt=""
            className="object-cover dark:hidden"
            fill
            priority
            sizes="100vw"
            src={presentation.media.light}
            style={{ objectPosition: presentation.media.focalPoint }}
          />
          <Image
            alt=""
            className="hidden object-cover dark:block"
            fill
            priority
            sizes="100vw"
            src={presentation.media.dark}
            style={{ objectPosition: presentation.media.focalPoint }}
          />
        </motion.div>
      </AnimatePresence>

      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(100deg,hsl(var(--background)/.98)_0%,hsl(var(--background)/.90)_42%,hsl(var(--background)/.48)_72%,hsl(var(--background)/.62)_100%)]" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-15 mix-blend-soft-light" />

      <section
        aria-label="Featured application"
        className="relative z-10 flex min-h-[calc(100svh-2rem)] flex-col px-5 pb-24 pt-14 sm:px-8 sm:pt-16 md:px-10 md:pb-8 lg:px-14 lg:pt-20"
      >
        <AnimatePresence initial={false} mode="wait">
          <motion.div
            key={`content-${activeApp.id}`}
            initial={animated ? { opacity: 0, y: 20, filter: "blur(8px)" } : false}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={animated ? { opacity: 0, y: -12, filter: "blur(6px)" } : undefined}
            transition={transition}
            className="flex flex-1 flex-col justify-center py-10"
          >
            <div className="max-w-2xl">
              <div className="flex items-center gap-3 text-[11px] font-semibold uppercase text-muted-foreground">
                <span>NexusMind</span>
                <span aria-hidden="true" className="h-px w-8 bg-current/50" />
                <span>{String(safeIndex + 1).padStart(2, "0")} / {String(apps.length).padStart(2, "0")}</span>
              </div>
              <h1 className="mt-6 max-w-2xl text-balance text-4xl font-semibold leading-[1.04] text-foreground sm:text-5xl lg:text-6xl">
                {presentation.headline}
              </h1>
              <p className="mt-5 max-w-xl text-base font-medium text-foreground/85 sm:text-lg">
                {activeApp.name}
              </p>
              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground sm:text-[15px] sm:leading-7">
                {activeApp.summary}
              </p>
              <Link
                aria-label={`Open ${activeApp.name}`}
                className="mt-8 inline-flex h-11 items-center gap-3 rounded-md bg-foreground px-5 text-sm font-semibold text-background transition-transform hover:translate-x-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                href={directApplicationRoute(activeApp)}
              >
                Open workspace
                <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </Link>
            </div>
            <div className="mt-10 self-end lg:mr-[8vw]">
              <DashboardSignal accent={presentation.accent} animated={animated} />
            </div>
          </motion.div>
        </AnimatePresence>

        <nav aria-label="Choose an application" className="shrink-0 border-t border-border/60 pt-4">
          <ol className="flex snap-x snap-mandatory gap-2.5 overflow-x-auto overscroll-x-contain pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {apps.map((app, index) => (
              <li className="snap-start" key={app.id}>
                <AppCard
                  active={safeIndex === index}
                  app={app}
                  index={index}
                  onSelect={() => setActiveIndex(index)}
                />
              </li>
            ))}
          </ol>
        </nav>
      </section>
    </main>
  );
}
