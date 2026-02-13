export type ThemeMode = 'light' | 'dark';
export type ThemePalette =
  | 'nexus'
  | 'ocean'
  | 'ember'
  | 'graphite'
  | 'forest'
  | 'royal'
  | 'sunset'
  | 'mono';

const MODE_KEY = 'theme-mode';
const PALETTE_KEY = 'theme-palette';
const PALETTE_CLASSES: ThemePalette[] = [
  'nexus',
  'ocean',
  'ember',
  'graphite',
  'forest',
  'royal',
  'sunset',
  'mono',
];

export function readThemeMode(): ThemeMode {
  if (typeof window === 'undefined') return 'dark';
  const stored = window.localStorage.getItem(MODE_KEY);
  return stored === 'dark' || stored === 'light' ? stored : 'dark';
}

export function readThemePalette(): ThemePalette {
  if (typeof window === 'undefined') return 'nexus';
  const stored = window.localStorage.getItem(PALETTE_KEY);
  return stored && PALETTE_CLASSES.includes(stored as ThemePalette)
    ? (stored as ThemePalette)
    : 'nexus';
}

export function applyTheme(mode: ThemeMode, palette: ThemePalette): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.classList.toggle('dark', mode === 'dark');
  PALETTE_CLASSES.forEach((name) => root.classList.remove(`theme-${name}`));
  root.classList.add(`theme-${palette}`);
  root.setAttribute('data-theme-mode', mode);
  root.setAttribute('data-theme-palette', palette);
}

export function persistTheme(mode: ThemeMode, palette: ThemePalette): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(MODE_KEY, mode);
  window.localStorage.setItem(PALETTE_KEY, palette);
}

export function nextPalette(current: ThemePalette): ThemePalette {
  const idx = PALETTE_CLASSES.indexOf(current);
  const nextIndex = idx === -1 ? 0 : (idx + 1) % PALETTE_CLASSES.length;
  return PALETTE_CLASSES[nextIndex];
}
