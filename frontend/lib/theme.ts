import { applyResolvedTheme, persistThemePreference, readThemePreference, resolveTheme, type ResolvedTheme } from "./appearance";

export type ThemeMode = ResolvedTheme;

export function readThemeMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  return resolveTheme(readThemePreference(window.localStorage), matchMedia("(prefers-color-scheme: dark)").matches);
}

export function applyTheme(mode: ThemeMode): void {
  if (typeof document !== "undefined") applyResolvedTheme(document.documentElement, mode, mode);
}

export function persistTheme(mode: ThemeMode): void {
  if (typeof window !== "undefined") persistThemePreference(window.localStorage, mode);
}
