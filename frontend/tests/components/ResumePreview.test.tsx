import { render, screen } from "@testing-library/react";
import { ResumePreview } from "@/components/studios/career/ResumePreview";
import { initialResumeCreatorState } from "@/lib/studios/career/creator-reducer";

it("previews every supported resume story section", () => {
  render(<ResumePreview data={{
    ...initialResumeCreatorState,
    name: "Jane Doe",
    education: [{ institution: "State University", degree: "BS", duration: "2020", location: "Pune", gpa: "3.8" }],
    projects: [{ name: "Atlas", technologies: "TypeScript", descriptions: ["Built it"], link: "atlas.dev", dates: "2024" }],
    certifications: [{ name: "Cloud Pro", issuer: "Cloud Co", date: "2025" }],
    awards: [{ name: "Builder Award", issuer: "Acme" }],
    languages: [{ name: "English", proficiency: "Fluent" }],
    customSections: [{ title: "Volunteering", items: ["Mentored students"] }],
  }} />);

  for (const text of ["State University", "GPA 3.8", "atlas.dev", "Cloud Pro", "Builder Award", "Fluent", "Mentored students"]) expect(screen.getByText(text, { exact: false })).toBeVisible();
});
