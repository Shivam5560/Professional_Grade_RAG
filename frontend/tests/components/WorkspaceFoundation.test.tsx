import * as React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkspaceSurface } from "@/components/shell/WorkspaceSurface";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

it("renders a fully opaque workspace surface", () => {
  render(<WorkspaceSurface data-testid="surface">Work</WorkspaceSurface>);

  expect(screen.getByTestId("surface")).toHaveClass("bg-workspace");
  expect(screen.getByTestId("surface").className).not.toMatch(/backdrop-blur|\/\d/);
});

it("renders an accessible product dialog and returns focus after close", async () => {
  const user = userEvent.setup();

  function Harness() {
    const [open, setOpen] = React.useState(false);
    return (
      <>
        <button onClick={() => setOpen(true)}>Open naming</button>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Name context</DialogTitle>
              <DialogDescription>Give this table selection a reusable name.</DialogDescription>
            </DialogHeader>
            <input aria-label="Context name" />
            <DialogFooter>
              <button onClick={() => setOpen(false)}>Cancel</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    );
  }

  render(<Harness />);
  const trigger = screen.getByRole("button", { name: "Open naming" });
  await user.click(trigger);

  expect(screen.getByRole("dialog", { name: "Name context" })).toBeVisible();
  expect(screen.getByText("Give this table selection a reusable name.")).toBeVisible();

  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog", { name: "Name context" })).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
