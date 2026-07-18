import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CareerHome } from "@/components/studios/career/CareerHome";
import { ResumeIntake } from "@/components/studios/career/ResumeIntake";
import { TailorWorkspace } from "@/components/studios/career/TailorWorkspace";
import { ResumeCreator } from "@/components/studios/career/ResumeCreator";

const { ingestStoredResume, decideClaim, prepareTailoring } = vi.hoisted(() => ({
  ingestStoredResume: vi.fn().mockResolvedValue({ source: { id: "source-1" }, claims: [{ logical_claim_id: "claim-1", claim: { object: { value: "Python" }, predicate: "has-skill", verification_status: "inferred" } }] }),
  decideClaim: vi.fn().mockResolvedValue({ logical_claim_id: "claim-1", claim: { object: { value: "Python" }, predicate: "has-skill", verification_status: "verified" } }),
  prepareTailoring: vi.fn().mockResolvedValue({ approval: { id: "approval-1", status: "pending" }, draft: { id: "draft-1", bullets: [] }, match: { unmatched_requirements: [] } }),
}));

vi.mock("@/lib/api", () => ({
  apiClient: {},
}));
vi.mock("@/lib/studios/career/client", () => ({ careerStudioClient: { ingestStoredResume, decideClaim, prepareTailoring } }));

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
  expect(prepareTailoring).not.toHaveBeenCalled();

  await user.click(await screen.findByRole("button", { name: "Verify" }));
  await user.click(screen.getByRole("button", { name: "Start tailoring" }));
  expect(prepareTailoring).toHaveBeenCalledWith("source-1", "A complete senior data engineering job description");
});

it("scopes resume creator autosave to the signed-in owner", async () => {
  localStorage.clear();
  render(<ResumeCreator ownerId={42} />);

  await userEvent.setup().type(screen.getByPlaceholderText("Jane Doe"), "Jane");

  expect(localStorage.getItem("career-resume-creator-v1-42")).toContain('"name":"Jane"');
  expect(localStorage.getItem("career-resume-creator-v1")).toBeNull();
});
