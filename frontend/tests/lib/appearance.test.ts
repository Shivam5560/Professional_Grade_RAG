import {
  APPEARANCE_STORAGE_KEY,
  applyResolvedTheme,
  persistThemePreference,
  readThemePreference,
  resolveTheme,
} from "@/lib/appearance";

function memoryStorage(seed: Record<string, string> = {}) {
  const values = new Map(Object.entries(seed));
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
    value: (key: string) => values.get(key),
  };
}

describe("appearance", () => {
  it("migrates the legacy light mode and removes the palette", () => {
    const storage = memoryStorage({ "theme-mode": "light", "theme-palette": "royal" });
    expect(readThemePreference(storage)).toBe("light");
    expect(storage.value(APPEARANCE_STORAGE_KEY)).toBe("light");
    expect(storage.value("theme-palette")).toBeUndefined();
  });

  it("defaults invalid values to system", () => {
    const storage = memoryStorage({ [APPEARANCE_STORAGE_KEY]: "violet" });
    expect(readThemePreference(storage)).toBe("system");
  });

  it("resolves system preference without changing explicit choices", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
  });

  it("writes the DOM contract used by CSS and hydration", () => {
    const root = document.documentElement;
    applyResolvedTheme(root, "system", "dark");
    expect(root).toHaveClass("dark");
    expect(root).toHaveAttribute("data-theme-mode", "dark");
    expect(root).toHaveAttribute("data-theme-preference", "system");
  });

  it("persists only the new preference key", () => {
    const storage = memoryStorage();
    persistThemePreference(storage, "dark");
    expect(storage.value(APPEARANCE_STORAGE_KEY)).toBe("dark");
  });
});
