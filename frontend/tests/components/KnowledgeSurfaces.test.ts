import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, it } from "vitest";

it("keeps Knowledge routes inside the cinematic shell without legacy navigation", async () => {
  const [chat, documents, history] = await Promise.all([
    readFile(path.resolve("app/chat/page.tsx"), "utf8"),
    readFile(path.resolve("app/knowledge-base/page.tsx"), "utf8"),
    readFile(path.resolve("components/layout/Sidebar.tsx"), "utf8"),
  ]);

  expect(chat).toContain("<FocusCanvas");
  expect(chat).toContain("<Inspector");
  expect(chat).not.toContain("<Header");
  expect(chat).not.toContain("VerticalMagnificationDock");
  expect(documents).toContain("<ActionDock");
  expect(documents).toContain("<Inspector");
  expect(documents).not.toContain("<Header");
  expect(history).not.toContain("Knowledge Base");
  expect(history).not.toContain("Developer");
  expect(history).not.toContain("Settings");
});
