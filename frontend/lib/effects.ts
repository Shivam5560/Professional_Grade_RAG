export interface EffectsEnvironment {
  reducedMotion: boolean;
  coarsePointer: boolean;
  saveData: boolean;
  deviceMemory?: number;
}

export function shouldEnableCinematicEffects(
  environment: EffectsEnvironment,
): boolean {
  return (
    !environment.reducedMotion &&
    !environment.coarsePointer &&
    !environment.saveData &&
    (environment.deviceMemory === undefined || environment.deviceMemory >= 4)
  );
}
