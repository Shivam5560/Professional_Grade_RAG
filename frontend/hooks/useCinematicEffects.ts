"use client";

import { useEffect, useState } from "react";

import { shouldEnableCinematicEffects } from "@/lib/effects";

interface NavigatorHints extends Navigator {
  connection?: { saveData?: boolean };
  deviceMemory?: number;
}

function readState() {
  const hints = navigator as NavigatorHints;

  return {
    enabled: shouldEnableCinematicEffects({
      reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
      coarsePointer: matchMedia("(pointer: coarse)").matches,
      saveData: hints.connection?.saveData === true,
      deviceMemory: hints.deviceMemory,
    }),
    visible: document.visibilityState === "visible",
  };
}

export function useCinematicEffects() {
  const [state, setState] = useState({ enabled: false, visible: true });

  useEffect(() => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const coarse = matchMedia("(pointer: coarse)");
    const update = () => setState(readState());

    update();
    reduced.addEventListener("change", update);
    coarse.addEventListener("change", update);
    document.addEventListener("visibilitychange", update);

    return () => {
      reduced.removeEventListener("change", update);
      coarse.removeEventListener("change", update);
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  return state;
}
