import { access, readFile } from "node:fs/promises";
import path from "node:path";
import { expect, it } from "vitest";

interface CinematicAsset {
  file: string;
  application: string;
  mode: "dark" | "light";
  width: number;
  height: number;
  focalPoint: string;
  prompt: string;
}

it("ships every cinematic asset locally with prompt metadata", async () => {
  const root = path.resolve("public/images/cinematic");
  const manifest = JSON.parse(
    await readFile(path.join(root, "manifest.json"), "utf8"),
  ) as { assets: CinematicAsset[] };

  expect(manifest.assets).toHaveLength(10);
  expect(new Set(manifest.assets.map(({ file }) => file)).size).toBe(10);

  for (const asset of manifest.assets) {
    expect(asset.prompt.length).toBeGreaterThan(80);
    expect(asset.width / asset.height).toBeCloseTo(16 / 9, 4);
    expect(asset.focalPoint).toMatch(/^\d+% \d+%$/);
    await expect(access(path.join(root, asset.file))).resolves.toBeUndefined();
  }
});
