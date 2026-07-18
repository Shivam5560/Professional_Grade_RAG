"use client";

import { motion } from "framer-motion";
import { getImageProps } from "next/image";

import { useCinematicEffects } from "@/hooks/useCinematicEffects";
import type { ApplicationPresentation } from "@/lib/presentation/types";

interface CinematicBackdropProps {
  media: ApplicationPresentation["media"];
}

export function CinematicBackdrop({ media }: CinematicBackdropProps) {
  const effects = useCinematicEffects();
  const common = {
    alt: media.alt,
    fill: true,
    sizes: "100vw",
    className: "object-cover",
    style: { objectPosition: media.focalPoint },
  } as const;
  const dark = getImageProps({
    ...common,
    src: media.dark,
    loading: "eager",
  }).props;
  const light = getImageProps({
    ...common,
    src: media.light,
    loading: "eager",
  }).props;

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-background"
    >
      <motion.div
        animate={
          effects.enabled && effects.visible
            ? { scale: [1.02, 1.075], x: [0, -12] }
            : undefined
        }
        transition={{
          duration: 18,
          repeat: Infinity,
          repeatType: "mirror",
          ease: "easeInOut",
        }}
        className="absolute inset-0"
      >
        <picture>
          <source
            media="(prefers-color-scheme: light)"
            srcSet={light.srcSet}
          />
          <img {...dark} alt={media.alt} />
        </picture>
      </motion.div>
      <div
        data-testid="cinematic-veil"
        className="absolute inset-0 bg-[linear-gradient(105deg,hsl(var(--background))_0%,hsl(var(--background)/.98)_62%,hsl(var(--background)/.76)_100%)]"
      />
      <div className="absolute inset-0 bg-noise opacity-20 mix-blend-soft-light" />
    </div>
  );
}
