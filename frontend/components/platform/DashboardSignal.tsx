"use client";

import { motion, useReducedMotion } from "framer-motion";

import type { ApplicationAccent } from "@/lib/presentation/types";
import { cn } from "@/lib/utils";

const accentClasses: Record<ApplicationAccent, string> = {
  signal: "text-[hsl(var(--signal))]",
  data: "text-[hsl(var(--data))]",
  copper: "text-[hsl(var(--copper))]",
  career: "text-[hsl(var(--chart-4))]",
  neutral: "text-foreground",
};

const columns = [32, 48, 38, 72, 58, 88, 64, 78, 52, 68, 42, 56, 35];

export function DashboardSignal({
  accent,
  animated = true,
}: {
  accent: ApplicationAccent;
  animated?: boolean;
}): JSX.Element {
  const reduceMotion = useReducedMotion();
  const shouldAnimate = animated && !reduceMotion;

  return (
    <div
      aria-hidden="true"
      className={cn(
        "relative h-24 w-52 overflow-hidden border-y border-current/20 opacity-65 sm:h-28 sm:w-64",
        accentClasses[accent],
      )}
    >
      <motion.span
        className="absolute inset-x-0 top-1/2 h-px bg-current/40"
        animate={shouldAnimate ? { x: ["-35%", "35%"], opacity: [0.2, 0.65, 0.2] } : undefined}
        transition={{ duration: 5.8, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }}
      />
      <div className="absolute inset-0 flex items-end justify-between gap-1 px-2 py-4">
        {columns.map((height, index) => (
          <motion.span
            className="w-px origin-bottom bg-current"
            key={`${height}-${index}`}
            style={{ height: `${height}%` }}
            animate={shouldAnimate ? { scaleY: [0.72, 1, 0.82] } : undefined}
            transition={{
              duration: 2.4 + (index % 4) * 0.45,
              delay: index * 0.08,
              repeat: Infinity,
              repeatType: "mirror",
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </div>
  );
}
