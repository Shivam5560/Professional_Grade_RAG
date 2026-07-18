import * as React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ActionDock } from "@/components/shell/ActionDock";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Inspector } from "@/components/shell/Inspector";

it("keeps one named primary work region", () => {
  render(<FocusCanvas ariaLabel="AuraSQL result">Result</FocusCanvas>);

  expect(screen.getByRole("main", { name: "AuraSQL result" })).toHaveTextContent("Result");
});

it("opens advanced detail only when requested and restores the trigger focus", async () => {
  const user = userEvent.setup();

  function Harness() {
    const [open, setOpen] = React.useState(false);
    return (
      <>
        <button onClick={() => setOpen(true)}>Evidence</button>
        <Inspector open={open} onOpenChange={setOpen} title="Evidence">
          Sources
        </Inspector>
      </>
    );
  }

  render(<Harness />);
  const trigger = screen.getByRole("button", { name: "Evidence" });
  expect(screen.getByText("Sources")).not.toBeVisible();

  await user.click(trigger);
  await waitFor(() => expect(screen.getByRole("dialog", { name: "Evidence" })).toBeVisible());
  expect(screen.getByText("Sources")).toBeVisible();

  await user.keyboard("{Escape}");
  expect(screen.getByText("Sources")).not.toBeVisible();
  expect(trigger).toHaveFocus();
});

it("composes header, context, and actions without additional main regions", () => {
  render(
    <FocusCanvas ariaLabel="Analysis workspace">
      <CanvasHeader
        eyebrow="Analysis"
        title="See the signal"
        description="Inspect a verified result."
        status={<span>Ready</span>}
        actions={<button>Export</button>}
      />
      <ContextRibbon>
        <button>Quarterly data</button>
      </ContextRibbon>
      <ActionDock primary={<button>Run analysis</button>} secondary={<button>Reset</button>} />
    </FocusCanvas>,
  );

  expect(screen.getAllByRole("main")).toHaveLength(1);
  expect(screen.getByRole("heading", { name: "See the signal", level: 1 })).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Active context" })).toBeInTheDocument();
  expect(screen.getByRole("toolbar", { name: "Canvas actions" })).toBeInTheDocument();
});
