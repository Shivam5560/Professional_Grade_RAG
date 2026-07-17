import { shouldEnableCinematicEffects } from "@/lib/effects";

const capable = {
  reducedMotion: false,
  coarsePointer: false,
  saveData: false,
  deviceMemory: 8,
};

describe("shouldEnableCinematicEffects", () => {
  it("enables the scene on a capable device", () =>
    expect(shouldEnableCinematicEffects(capable)).toBe(true));

  it.each([
    { ...capable, reducedMotion: true },
    { ...capable, saveData: true },
    { ...capable, coarsePointer: true },
    { ...capable, deviceMemory: 2 },
  ])(
    "disables expensive effects for constrained environments",
    (environment) => {
      expect(shouldEnableCinematicEffects(environment)).toBe(false);
    },
  );
});
