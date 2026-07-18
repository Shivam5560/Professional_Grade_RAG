import { readFileSync } from "node:fs";
import path from "node:path";

it("declares the complete additive ResumeGen field contract", () => {
  const types = readFileSync(path.join(process.cwd(), "lib/types.ts"), "utf8");

  for (const field of [
    "phone",
    "portfolio",
    "summary",
    "certifications",
    "awards",
    "languages",
    "customSections",
    "sectionOrder",
  ]) {
    expect(types).toMatch(new RegExp(`\\b${field}\\??:`));
  }
});
