import fs from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const read = (relativePath: string) => fs.readFileSync(path.join(process.cwd(), relativePath), "utf8");

describe("opaque authenticated workspaces", () => {
  it.each([
    "app/aurasql/connections/new/page.tsx",
    "app/aurasql/connections/[id]/page.tsx",
    "app/aurasql/contexts/new/page.tsx",
  ])("uses the shared AuraSQL canvas without legacy glass on %s", (file) => {
    const source = read(file);
    expect(source).toContain("<AuraSqlPage");
    expect(source).toContain("bg-workspace-raised");
    expect(source).not.toMatch(/glass-panel|backdrop-blur|ShaderAnimation|bg-accent-soft/);
  });

  it.each([
    "app/aurasql/connections/page.tsx",
    "app/aurasql/contexts/page.tsx",
    "app/aurasql/settings/page.tsx",
    "components/aurasql/AuraSqlResultViewport.tsx",
    "components/shell/ContextRibbon.tsx",
  ])("does not blur functional content on %s", (file) => {
    expect(read(file)).not.toMatch(/backdrop-blur|bg-background\/(55|70|75|85|88|90|95)/);
  });
});
