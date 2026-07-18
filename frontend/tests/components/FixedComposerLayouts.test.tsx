import fs from "node:fs";
import path from "node:path";

const read = (file: string) => fs.readFileSync(path.join(process.cwd(), file), "utf8");

it("gives Knowledge Studio one message scroll owner and a fixed composer", () => {
  const chatInterface = read("components/chat/ChatInterface.tsx");
  const messageList = read("components/chat/MessageList.tsx");

  expect(chatInterface).toContain('data-fixed-composer="knowledge"');
  expect(chatInterface).toMatch(/data-fixed-composer="knowledge"[\s\S]{0,300}bg-workspace-raised/);
  expect(messageList).toContain('data-scroll-owner="messages"');
});

it("keeps the AuraSQL question composer visible while query output scrolls", () => {
  const queryPage = read("app/aurasql/query/page.tsx");

  expect(queryPage).toContain('data-fixed-composer="aurasql"');
  expect(queryPage).toContain('data-scroll-owner="query-results"');
  expect(queryPage).toMatch(/data-fixed-composer="aurasql"[\s\S]{0,400}sticky/);
  expect(queryPage).toContain("max-h-80 resize-none overflow-y-auto");
});
