import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CareerHome } from "@/components/studios/career/CareerHome";
import { ResumeIntake } from "@/components/studios/career/ResumeIntake";
import { TailorWorkspace } from "@/components/studios/career/TailorWorkspace";

const { startAutoTailor } = vi.hoisted(() => ({ startAutoTailor: vi.fn().mockResolvedValue({ analysis_id: "analysis-1", status: "paused_for_human" }) }));

vi.mock("@/lib/api", () => ({
  apiClient: { startAutoTailor },
}));

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

it("does not start tailoring until the reviewed plan is explicitly confirmed", async () => {
  const user = userEvent.setup();
  render(<TailorWorkspace resumes={[{ id: "row-1", resume_id: "resume-1", filename: "resume.pdf", status: "uploaded", created_at: "" }]} />);

  expect(screen.getByLabelText("Upload resume")).toHaveAttribute("accept", ".pdf,.doc,.docx,.txt");
  await user.type(screen.getByLabelText("Target job description"), "A complete senior data engineering job description");
  await user.click(screen.getByRole("button", { name: "Review tailoring plan" }));
  expect(startAutoTailor).not.toHaveBeenCalled();

  await user.click(screen.getByRole("button", { name: "Start tailoring" }));
  expect(startAutoTailor).toHaveBeenCalledTimes(1);
});
