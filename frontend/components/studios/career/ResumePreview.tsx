import type { ReactNode } from "react";
import type { ResumeGenData, ResumeGenNamedRecord } from "@/lib/types";

const defaultOrder = ["summary", "experience", "education", "projects", "skills", "certifications", "awards", "languages", "custom_sections"];

export function ResumePreview({ data }: { data: ResumeGenData }): JSX.Element {
  const sections: Record<string, ReactNode> = {
    summary: data.summary ? <PreviewSection title="Professional Summary"><p className="text-sm leading-6">{data.summary}</p></PreviewSection> : null,
    experience: data.experience.length ? <PreviewSection title="Experience">{data.experience.map((item, index) => <div className="mb-4" key={index}><div className="flex justify-between gap-3 text-sm font-semibold"><span>{item.position} · {item.company}</span><span>{item.duration}</span></div><p className="text-xs text-slate-600">{item.location}</p><ul className="mt-2 list-disc space-y-1 pl-5 text-xs">{item.responsibilities.filter(Boolean).map((line, lineIndex) => <li key={lineIndex}>{line}</li>)}</ul></div>)}</PreviewSection> : null,
    education: data.education.length ? <PreviewSection title="Education">{data.education.map((item, index) => <div className="mb-3" key={index}><p className="text-sm"><strong>{item.degree}</strong> · {item.institution} <span className="float-right">{item.duration}</span></p><p className="text-xs text-slate-600">{[item.location, item.gpa ? `GPA ${item.gpa}` : ""].filter(Boolean).join(" · ")}</p></div>)}</PreviewSection> : null,
    projects: data.projects.length ? <PreviewSection title="Projects">{data.projects.map((item, index) => <div className="mb-3" key={index}><div className="flex justify-between gap-3"><p className="text-sm font-semibold">{item.name} <span className="font-normal text-slate-600">{item.technologies}</span></p><span className="text-xs">{item.dates}</span></div>{item.link ? <p className="text-xs text-slate-600">{item.link}</p> : null}<ul className="mt-1 list-disc pl-5 text-xs">{item.descriptions.filter(Boolean).map((line, lineIndex) => <li key={lineIndex}>{line}</li>)}</ul></div>)}</PreviewSection> : null,
    skills: Object.values(data.skills).some((values) => values.length) ? <PreviewSection title="Skills"><div className="space-y-1 text-xs">{Object.entries(data.skills).map(([category, values]) => values.filter(Boolean).length ? <p key={category}><strong>{category}:</strong> {values.filter(Boolean).join(", ")}</p> : null)}</div></PreviewSection> : null,
    certifications: namedSection("Certifications", data.certifications),
    awards: namedSection("Awards", data.awards),
    languages: namedSection("Languages", data.languages),
    custom_sections: data.customSections?.map((section, index) => section.title.trim() && section.items.some(Boolean) ? <PreviewSection key={index} title={section.title}><ul className="list-disc space-y-1 pl-5 text-xs">{section.items.filter(Boolean).map((item, itemIndex) => <li key={itemIndex}>{item}</li>)}</ul></PreviewSection> : null),
  };
  return <article aria-label="Resume preview" className="mx-auto min-h-[52rem] w-full max-w-[46rem] bg-white p-8 text-slate-950 shadow-xl sm:p-12"><header className="border-b border-slate-300 pb-4 text-center"><h2 className="text-3xl font-bold tracking-tight">{data.name || "Your Name"}</h2><p className="mt-2 text-xs">{[data.email, data.phone, data.location].filter(Boolean).join(" · ")}</p><p className="mt-1 text-xs">{[data.linkedin, data.github, data.portfolio].filter(Boolean).join(" · ")}</p></header>{(data.sectionOrder ?? defaultOrder).map((section) => <div key={section}>{sections[section]}</div>)}</article>;
}

function namedSection(title: string, records?: ResumeGenNamedRecord[]): ReactNode { return records?.length ? <PreviewSection title={title}><div className="space-y-2">{records.map((record, index) => <div className="flex justify-between gap-3 text-xs" key={index}><span><strong>{record.name}</strong>{record.issuer ? ` · ${record.issuer}` : ""}{record.proficiency ? ` · ${record.proficiency}` : ""}</span><span>{record.date}</span></div>)}</div></PreviewSection> : null; }
function PreviewSection({ children, title }: { children: ReactNode; title: string }) { return <section className="mt-6"><h3 className="mb-3 border-b border-slate-300 pb-1 text-sm font-bold uppercase tracking-wider">{title}</h3>{children}</section>; }
