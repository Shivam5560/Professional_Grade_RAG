import {
  initialResumeCreatorState,
  resumeCreatorReducer,
} from "@/lib/studios/career/creator-reducer";

it("adds repeatable resume details and reorders sections without losing data", () => {
  const withExperience = resumeCreatorReducer(initialResumeCreatorState, { type: "add-experience" });
  const updated = resumeCreatorReducer(withExperience, {
    type: "update-experience",
    index: 0,
    patch: { company: "Acme", position: "Engineer", duration: "2022-present" },
  });
  const reordered = resumeCreatorReducer(updated, {
    type: "move-section",
    section: "skills",
    direction: "up",
  });

  expect(updated.experience[0].company).toBe("Acme");
  expect(reordered.sectionOrder.indexOf("skills")).toBeLessThan(updated.sectionOrder.indexOf("skills"));
  expect(reordered.experience[0].company).toBe("Acme");
});

it("hydrates only versioned creator drafts", () => {
  const hydrated = resumeCreatorReducer(initialResumeCreatorState, {
    type: "hydrate",
    state: { ...initialResumeCreatorState, name: "Jane Doe", version: 1 },
  });
  const ignored = resumeCreatorReducer(initialResumeCreatorState, {
    type: "hydrate",
    state: { ...initialResumeCreatorState, name: "Old draft", version: 0 } as never,
  });

  expect(hydrated.name).toBe("Jane Doe");
  expect(ignored.name).toBe("");
});

it("reorders repeatable entries independently", () => {
  const one = resumeCreatorReducer(initialResumeCreatorState, { type: "add-project" });
  const two = resumeCreatorReducer(one, { type: "add-project" });
  const named = resumeCreatorReducer(two, { type: "update-project", index: 1, patch: { name: "Second project" } });
  const moved = resumeCreatorReducer(named, { type: "move-project", index: 1, direction: "up" });

  expect(moved.projects[0].name).toBe("Second project");
});
