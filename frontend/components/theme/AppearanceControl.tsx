"use client";

import { Moon, Sun } from "lucide-react";

import type { ThemePreference } from "@/lib/appearance";
import { useAppearance } from "./AppearanceProvider";

const choices: Array<{ value: ThemePreference; label: string }> = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

export function AppearanceControl() {
  const { preference, setPreference } = useAppearance();

  return (
    <label className="relative grid h-10 w-10 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-within:ring-2 focus-within:ring-ring">
      <span className="sr-only">Appearance</span>
      <Sun aria-hidden className="h-4 w-4 dark:hidden" />
      <Moon aria-hidden className="hidden h-4 w-4 dark:block" />
      <select
        aria-label="Appearance"
        className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
        onChange={(event) => setPreference(event.target.value as ThemePreference)}
        value={preference}
      >
        {choices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
    </label>
  );
}
