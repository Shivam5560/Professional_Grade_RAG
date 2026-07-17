"use client";

import { useAppearance } from "@/components/theme/AppearanceProvider";

export function useAppTheme() {
  const { resolvedTheme, setPreference } = useAppearance();
  return {
    mode: resolvedTheme,
    toggleMode: () => setPreference(resolvedTheme === "dark" ? "light" : "dark"),
  };
}
