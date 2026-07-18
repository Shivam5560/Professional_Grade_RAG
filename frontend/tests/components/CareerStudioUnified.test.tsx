import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CareerHome } from "@/components/studios/career/CareerHome";
import { ResumeIntake } from "@/components/studios/career/ResumeIntake";

it("presents score, explicit tailor, and create as separate Career workflows", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  render(<CareerHome onSelect={onSelect} />);

  expect(screen.getByRole("button", { name: "Score Resume" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Tailor Resume" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Create Resume" })).toBeVisible();

  await user.click(screen.getByRole("button", { name: "Score Resume" }));
  expect(onSelect).toHaveBeenCalledWith("score");
  expect(onSelect).not.toHaveBeenCalledWith("tailor");
});

it("accepts normal resume files and keeps JSON under advanced import", async () => {
  const user = userEvent.setup();
  render(<ResumeIntake file={null} onFileChange={() => undefined} />);

  expect(screen.getByLabelText("Upload resume")).toHaveAttribute("accept", ".pdf,.doc,.docx,.txt");
  expect(screen.queryByLabelText("Import structured JSON")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Advanced structured import" }));
  expect(screen.getByLabelText("Import structured JSON")).toHaveAttribute("accept", ".json,application/json");
});
