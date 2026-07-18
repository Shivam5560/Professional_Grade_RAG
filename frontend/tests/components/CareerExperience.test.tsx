import fs from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

describe("Career Studio experience", () => {
  it("uses the focused shell and keeps detailed review in an inspector", () => {
    const source = fs.readFileSync(
      path.join(process.cwd(), "app/career/page.tsx"),
      "utf8",
    );

    expect(source).toContain("<ContextRibbon");
    expect(source).toContain("<ActionDock");
    expect(source).toContain("<Inspector");
    expect(source).not.toContain("<StudioPanel");
    expect(source).not.toContain("<Header");
  });
});
