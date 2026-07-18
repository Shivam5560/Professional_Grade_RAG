import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuraSqlResultViewport } from "@/components/aurasql/AuraSqlResultViewport";

const result = {
  columns: ["month", "revenue", "orders"],
  rows: [
    { month: "Jan", revenue: 120, orders: 18 },
    { month: "Feb", revenue: 180, orders: 24 },
  ],
};

it("treats table and graph as equal result modes", async () => {
  const user = userEvent.setup();
  render(<AuraSqlResultViewport execution={result} onExport={vi.fn()} />);

  expect(screen.getByRole("table", { name: "Query results" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Graph view" }));

  expect(screen.getByRole("img", { name: "revenue by month" })).toBeInTheDocument();
  expect(screen.getByLabelText("Metric")).toHaveValue("revenue");
  expect(screen.getAllByText("180")).not.toHaveLength(0);
});

it("keeps export available and reports empty numeric data clearly", async () => {
  const user = userEvent.setup();
  const onExport = vi.fn();
  render(
    <AuraSqlResultViewport
      execution={{ columns: ["team"], rows: [{ team: "Platform" }] }}
      onExport={onExport}
    />,
  );

  await user.click(screen.getByRole("button", { name: "Export results" }));
  expect(onExport).toHaveBeenCalledOnce();

  await user.click(screen.getByRole("button", { name: "Graph view" }));
  expect(screen.getByText("No numeric series to visualize")).toBeInTheDocument();
});
