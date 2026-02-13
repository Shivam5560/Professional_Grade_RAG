'use client';

import { useEffect, useState } from 'react';
import {
  applyTheme,
  persistTheme,
  readThemeMode,
  readThemePalette,
  type ThemeMode,
  type ThemePalette,
} from '@/lib/theme';

export function useAppTheme() {
  const [mode, setMode] = useState<ThemeMode>('light');
  const [palette, setPalette] = useState<ThemePalette>('nexus');

  useEffect(() => {
    const initialMode = readThemeMode();
    const initialPalette = readThemePalette();
    setMode(initialMode);
    setPalette(initialPalette);
    applyTheme(initialMode, initialPalette);
  }, []);

  const updateTheme = (nextMode: ThemeMode, nextPalette: ThemePalette) => {
    setMode(nextMode);
    setPalette(nextPalette);
    applyTheme(nextMode, nextPalette);
    persistTheme(nextMode, nextPalette);
  };

  return {
    mode,
    palette,
    setMode: (nextMode: ThemeMode) => updateTheme(nextMode, palette),
    setPalette: (nextPalette: ThemePalette) => updateTheme(mode, nextPalette),
    toggleMode: () => updateTheme(mode === 'dark' ? 'light' : 'dark', palette),
  };
}
