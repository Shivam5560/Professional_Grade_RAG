export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

export const APPEARANCE_STORAGE_KEY = "nexusmind-theme";
const LEGACY_MODE_KEY = "theme-mode";
const LEGACY_PALETTE_KEY = "theme-palette";

export interface AppearanceStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function isPreference(value: string | null): value is ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

export function readThemePreference(storage: AppearanceStorage): ThemePreference {
  const current = storage.getItem(APPEARANCE_STORAGE_KEY);
  if (isPreference(current)) return current;

  const legacy = storage.getItem(LEGACY_MODE_KEY);
  const migrated: ThemePreference = legacy === "light" || legacy === "dark" ? legacy : "system";
  storage.setItem(APPEARANCE_STORAGE_KEY, migrated);
  storage.removeItem(LEGACY_MODE_KEY);
  storage.removeItem(LEGACY_PALETTE_KEY);
  return migrated;
}

export function persistThemePreference(
  storage: AppearanceStorage,
  preference: ThemePreference,
): void {
  storage.setItem(APPEARANCE_STORAGE_KEY, preference);
  storage.removeItem(LEGACY_MODE_KEY);
  storage.removeItem(LEGACY_PALETTE_KEY);
}

export function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean,
): ResolvedTheme {
  return preference === "system" ? (systemPrefersDark ? "dark" : "light") : preference;
}

export function applyResolvedTheme(
  root: HTMLElement,
  preference: ThemePreference,
  resolved: ResolvedTheme,
): void {
  root.classList.toggle("dark", resolved === "dark");
  root.dataset.themeMode = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
}

export const themeBootstrapScript = `(() => {
  try {
    const key = "${APPEARANCE_STORAGE_KEY}";
    const stored = localStorage.getItem(key);
    const legacy = localStorage.getItem("${LEGACY_MODE_KEY}");
    const preference = ["system", "light", "dark"].includes(stored || "")
      ? stored
      : (["light", "dark"].includes(legacy || "") ? legacy : "system");
    localStorage.setItem(key, preference);
    localStorage.removeItem("${LEGACY_MODE_KEY}");
    localStorage.removeItem("${LEGACY_PALETTE_KEY}");
    const dark = preference === "dark" ||
      (preference === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
    const root = document.documentElement;
    root.classList.toggle("dark", dark);
    root.dataset.themeMode = dark ? "dark" : "light";
    root.dataset.themePreference = preference;
    root.style.colorScheme = dark ? "dark" : "light";
  } catch {}
})();`;
