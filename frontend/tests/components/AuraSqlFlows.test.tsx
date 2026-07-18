import * as React from "react";
import fs from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ContextNameDialog } from "@/components/aurasql/ContextNameDialog";

const affectedRoutes = [
  "app/aurasql/connections/new/page.tsx",
  "app/aurasql/connections/[id]/page.tsx",
  "app/aurasql/connections/page.tsx",
  "app/aurasql/contexts/new/page.tsx",
  "app/aurasql/contexts/page.tsx",
  "app/aurasql/query/page.tsx",
];

it("does not use browser-native workflow navigation or dialogs", () => {
  for (const route of affectedRoutes) {
    const source = fs.readFileSync(path.join(process.cwd(), route), "utf8");
    expect(source, route).not.toMatch(/router\.back\(\)|window\.(prompt|confirm|location\.assign)/);
  }
});

it("names a selected table context inside an accessible product dialog", async () => {
  const user = userEvent.setup();
  const onSave = vi.fn();

  render(
    <ContextNameDialog
      connectionLabel="Analytics warehouse"
      error={null}
      initialName=""
      onCancel={() => undefined}
      onSave={onSave}
      open
      saving={false}
      selectedTables={["orders", "customers"]}
    />,
  );

  expect(screen.getByRole("dialog", { name: "Name schema context" })).toBeVisible();
  expect(screen.getByText("2 tables selected")).toBeVisible();

  await user.click(screen.getByRole("button", { name: "Save context" }));
  expect(screen.getByText("Enter a context name.")).toBeVisible();
  expect(onSave).not.toHaveBeenCalled();

  await user.type(screen.getByRole("textbox", { name: "Context name" }), "Revenue view");
  await user.click(screen.getByRole("button", { name: "Save context" }));
  expect(onSave).toHaveBeenCalledWith("Revenue view");
});
