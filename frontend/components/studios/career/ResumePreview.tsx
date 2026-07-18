import type { ResumeGenData } from "@/lib/types";

export function ResumePreview({ data }: { data: ResumeGenData }): JSX.Element {
  return (
    <article aria-label="Resume preview" className="mx-auto min-h-[52rem] w-full max-w-[46rem] bg-white p-8 text-slate-950 shadow-xl sm:p-12">
      <header className="border-b border-slate-300 pb-4 text-center"><h2 className="text-3xl font-bold tracking-tight">{data.name || "Your Name"}</h2><p className="mt-2 text-xs">{[data.email, data.phone, data.location].filter(Boolean).join(" · ")}</p><p className="mt-1 text-xs">{[data.linkedin, data.github, data.portfolio].filter(Boolean).join(" · ")}</p></header>
      {data.summary ? <PreviewSection title="Professional Summary"><p className="text-sm leading-6">{data.summary}</p></PreviewSection> : null}
      {data.experience.length ? <PreviewSection title="Experience">{data.experience.map((item, index) => <div className="mb-4" key={index}><div className="flex justify-between gap-3 text-sm font-semibold"><span>{item.position} · {item.company}</span><span>{item.duration}</span></div><p className="text-xs text-slate-600">{item.location}</p><ul className="mt-2 list-disc space-y-1 pl-5 text-xs">{item.responsibilities.filter(Boolean).map((line, lineIndex) => <li key={lineIndex}>{line}</li>)}</ul></div>)}</PreviewSection> : null}
      {data.education.length ? <PreviewSection title="Education">{data.education.map((item, index) => <p className="mb-2 text-sm" key={index}><strong>{item.degree}</strong> · {item.institution} <span className="float-right">{item.duration}</span></p>)}</PreviewSection> : null}
      {data.projects.length ? <PreviewSection title="Projects">{data.projects.map((item, index) => <div className="mb-3" key={index}><p className="text-sm font-semibold">{item.name} <span className="font-normal text-slate-600">{item.technologies}</span></p><ul className="list-disc pl-5 text-xs">{item.descriptions.filter(Boolean).map((line, lineIndex) => <li key={lineIndex}>{line}</li>)}</ul></div>)}</PreviewSection> : null}
      {Object.values(data.skills).some((values) => values.length) ? <PreviewSection title="Skills"><div className="space-y-1 text-xs">{Object.entries(data.skills).map(([category, values]) => values.filter(Boolean).length ? <p key={category}><strong>{category}:</strong> {values.filter(Boolean).join(", ")}</p> : null)}</div></PreviewSection> : null}
    </article>
  );
}

function PreviewSection({ children, title }: { children: React.ReactNode; title: string }) { return <section className="mt-6"><h3 className="mb-3 border-b border-slate-300 pb-1 text-sm font-bold uppercase tracking-wider">{title}</h3>{children}</section>; }
