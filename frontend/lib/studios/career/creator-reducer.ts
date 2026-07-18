import type { ResumeGenData, ResumeGenEducation, ResumeGenExperience, ResumeGenProject } from "@/lib/types";

export type ResumeCreatorState = Omit<ResumeGenData, "sectionOrder" | "customSections" | "certifications" | "awards" | "languages"> & {
  version: 1;
  sectionOrder: string[];
  customSections: NonNullable<ResumeGenData["customSections"]>;
  certifications: NonNullable<ResumeGenData["certifications"]>;
  awards: NonNullable<ResumeGenData["awards"]>;
  languages: NonNullable<ResumeGenData["languages"]>;
};

export const creatorSections = ["summary", "experience", "education", "projects", "skills", "certifications", "awards", "languages", "custom_sections"];

export const initialResumeCreatorState: ResumeCreatorState = {
  version: 1,
  name: "",
  email: "",
  phone: "",
  location: "",
  linkedin: "",
  github: "",
  portfolio: "",
  summary: "",
  experience: [],
  education: [],
  projects: [],
  skills: { Programming: [] },
  certifications: [],
  awards: [],
  languages: [],
  customSections: [],
  sectionOrder: creatorSections,
};

export type ResumeCreatorAction =
  | { type: "hydrate"; state: ResumeCreatorState }
  | { type: "set-field"; field: keyof ResumeCreatorState; value: unknown }
  | { type: "add-experience" }
  | { type: "update-experience"; index: number; patch: Partial<ResumeGenExperience> }
  | { type: "remove-experience"; index: number }
  | { type: "move-experience"; index: number; direction: "up" | "down" }
  | { type: "add-education" }
  | { type: "update-education"; index: number; patch: Partial<ResumeGenEducation> }
  | { type: "remove-education"; index: number }
  | { type: "move-education"; index: number; direction: "up" | "down" }
  | { type: "add-project" }
  | { type: "update-project"; index: number; patch: Partial<ResumeGenProject> }
  | { type: "remove-project"; index: number }
  | { type: "move-project"; index: number; direction: "up" | "down" }
  | { type: "move-section"; section: string; direction: "up" | "down" };

export function resumeCreatorReducer(state: ResumeCreatorState, action: ResumeCreatorAction): ResumeCreatorState {
  switch (action.type) {
    case "hydrate": return action.state.version === 1 ? action.state : state;
    case "set-field": return { ...state, [action.field]: action.value } as ResumeCreatorState;
    case "add-experience": return { ...state, experience: [...state.experience, { company: "", position: "", duration: "", location: "", responsibilities: [""] }] };
    case "update-experience": return { ...state, experience: state.experience.map((item, index) => index === action.index ? { ...item, ...action.patch } : item) };
    case "remove-experience": return { ...state, experience: state.experience.filter((_, index) => index !== action.index) };
    case "move-experience": return { ...state, experience: moveItem(state.experience, action.index, action.direction) };
    case "add-education": return { ...state, education: [...state.education, { institution: "", degree: "", duration: "", location: "", gpa: "" }] };
    case "update-education": return { ...state, education: state.education.map((item, index) => index === action.index ? { ...item, ...action.patch } : item) };
    case "remove-education": return { ...state, education: state.education.filter((_, index) => index !== action.index) };
    case "move-education": return { ...state, education: moveItem(state.education, action.index, action.direction) };
    case "add-project": return { ...state, projects: [...state.projects, { name: "", technologies: "", descriptions: [""], link: "", dates: "" }] };
    case "update-project": return { ...state, projects: state.projects.map((item, index) => index === action.index ? { ...item, ...action.patch } : item) };
    case "remove-project": return { ...state, projects: state.projects.filter((_, index) => index !== action.index) };
    case "move-project": return { ...state, projects: moveItem(state.projects, action.index, action.direction) };
    case "move-section": {
      const order = [...(state.sectionOrder ?? creatorSections)];
      const index = order.indexOf(action.section);
      const nextIndex = action.direction === "up" ? index - 1 : index + 1;
      if (index < 0 || nextIndex < 0 || nextIndex >= order.length) return state;
      [order[index], order[nextIndex]] = [order[nextIndex], order[index]];
      return { ...state, sectionOrder: order };
    }
  }
}

function moveItem<T>(items: T[], index: number, direction: "up" | "down"): T[] {
  const destination = direction === "up" ? index - 1 : index + 1;
  if (destination < 0 || destination >= items.length) return items;
  const next = [...items];
  [next[index], next[destination]] = [next[destination], next[index]];
  return next;
}
