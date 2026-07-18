"use client";

import { useEffect, useReducer, useState, type Dispatch, type ReactNode } from "react";
import { ArrowDown, ArrowUp, Download, Plus, Trash2 } from "lucide-react";

import { ResumePreview } from "./ResumePreview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { creatorSections, initialResumeCreatorState, resumeCreatorReducer, type ResumeCreatorAction } from "@/lib/studios/career/creator-reducer";
import type { ResumeGenNamedRecord } from "@/lib/types";

const steps = ["Details", "Experience", "Education", "Projects", "Extras", "Preview"];
const storageKey = "career-resume-creator-v1";

export function ResumeCreator(): JSX.Element {
  const [state, dispatch] = useReducer(resumeCreatorReducer, initialResumeCreatorState);
  const [step, setStep] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) dispatch({ type: "hydrate", state: JSON.parse(saved) });
    } catch { localStorage.removeItem(storageKey); }
  }, []);
  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(state)); }, [state]);

  const setField = (field: keyof typeof state, value: unknown) => dispatch({ type: "set-field", field, value });
  const download = async (format: "pdf" | "tex") => {
    if (!state.name.trim() || !state.email.trim()) { setError("Name and email are required before export."); return; }
    setGenerating(true); setError(null);
    try {
      const blob = format === "pdf" ? await apiClient.generateResumePdf(state) : new Blob([await apiClient.generateResumeLatex(state)], { type: "text/plain" });
      const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `${state.name.trim().replace(/\s+/g, "-").toLowerCase() || "resume"}.${format}`; link.click(); URL.revokeObjectURL(url);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Resume generation failed"); }
    finally { setGenerating(false); }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(28rem,.9fr)]">
      <section className="rounded-xl border border-border bg-workspace-raised">
        <nav aria-label="Resume creator steps" className="flex overflow-x-auto border-b border-border p-2">{steps.map((label, index) => <button className={`whitespace-nowrap rounded-md px-3 py-2 text-xs font-medium ${step === index ? "bg-foreground text-background" : "text-muted-foreground hover:bg-workspace-inset"}`} key={label} onClick={() => setStep(index)} type="button">{index + 1}. {label}</button>)}</nav>
        <div className="p-5 sm:p-6">
          {step === 0 ? <Details state={state} setField={setField} /> : null}
          {step === 1 ? <Experience state={state} dispatch={dispatch} /> : null}
          {step === 2 ? <Education state={state} dispatch={dispatch} /> : null}
          {step === 3 ? <Projects state={state} dispatch={dispatch} /> : null}
          {step === 4 ? <Extras state={state} setField={setField} dispatch={dispatch} /> : null}
          {step === 5 ? <div><h2 className="text-xl font-semibold">Ready to export</h2><p className="mt-2 text-sm text-muted-foreground">Review the formatted resume, reorder sections, then download PDF or editable LaTeX source.</p><SectionOrder order={state.sectionOrder ?? creatorSections} dispatch={dispatch} /></div> : null}
          {error ? <p role="alert" className="mt-5 text-sm text-destructive">{error}</p> : null}
          <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5"><Button disabled={step === 0} onClick={() => setStep((value) => value - 1)} variant="ghost">Previous</Button><div className="flex gap-2">{step < steps.length - 1 ? <Button onClick={() => setStep((value) => value + 1)}>Continue</Button> : <><Button disabled={generating} onClick={() => download("tex")} variant="outline">Download .tex</Button><Button disabled={generating} onClick={() => download("pdf")}><Download className="mr-2 h-4 w-4" />Download PDF</Button></>}</div></footer>
        </div>
      </section>
      <div className="max-h-[calc(100svh-9rem)] overflow-y-auto rounded-xl bg-workspace-inset p-3"><ResumePreview data={state} /></div>
    </div>
  );
}

function Details({ state, setField }: { state: typeof initialResumeCreatorState; setField(field: keyof typeof state, value: unknown): void }) {
  const fields = [["name", "Full name", "Jane Doe"], ["email", "Email", "jane@example.com"], ["phone", "Phone", "+1 555 0100"], ["location", "Location", "Bengaluru, India"], ["linkedin", "LinkedIn", "linkedin.com/in/jane"], ["github", "GitHub", "github.com/jane"], ["portfolio", "Portfolio", "jane.dev"]] as const;
  return <div><h2 className="text-xl font-semibold">Start with your professional identity</h2><p className="mt-2 text-sm text-muted-foreground">These details form the resume header and contact links.</p><div className="mt-6 grid gap-4 sm:grid-cols-2">{fields.map(([field, label, placeholder]) => <Field key={field} label={label}><Input value={String(state[field] ?? "")} onChange={(event) => setField(field, event.target.value)} placeholder={placeholder} /></Field>)}</div><Field label="Professional summary" className="mt-4"><Textarea className="min-h-32" value={state.summary} onChange={(event) => setField("summary", event.target.value)} placeholder="Describe your scope, strengths, and the outcomes you create." /></Field></div>;
}

function Experience({ state, dispatch }: { state: typeof initialResumeCreatorState; dispatch: Dispatch<ResumeCreatorAction> }) {
  return <RepeatSection title="Experience" description="Add roles and evidence-rich achievement bullets." onAdd={() => dispatch({ type: "add-experience" })} addLabel="Add experience">{state.experience.map((item, index) => <Entry key={index} title={item.position || item.company || `Experience ${index + 1}`} onRemove={() => dispatch({ type: "remove-experience", index })}><div className="grid gap-3 sm:grid-cols-2"><Field label="Company"><Input value={item.company} onChange={(e) => dispatch({ type: "update-experience", index, patch: { company: e.target.value } })} /></Field><Field label="Position"><Input value={item.position} onChange={(e) => dispatch({ type: "update-experience", index, patch: { position: e.target.value } })} /></Field><Field label="Location"><Input value={item.location ?? ""} onChange={(e) => dispatch({ type: "update-experience", index, patch: { location: e.target.value } })} /></Field><Field label="Dates"><Input value={item.duration} onChange={(e) => dispatch({ type: "update-experience", index, patch: { duration: e.target.value } })} /></Field></div><Field className="mt-3" label="Achievement bullets (one per line)"><Textarea value={item.responsibilities.join("\n")} onChange={(e) => dispatch({ type: "update-experience", index, patch: { responsibilities: e.target.value.split("\n") } })} /></Field></Entry>)}</RepeatSection>;
}

function Education({ state, dispatch }: { state: typeof initialResumeCreatorState; dispatch: Dispatch<ResumeCreatorAction> }) {
  return <RepeatSection title="Education" description="Include formal education and relevant credentials." onAdd={() => dispatch({ type: "add-education" })} addLabel="Add education">{state.education.map((item, index) => <Entry key={index} title={item.degree || item.institution || `Education ${index + 1}`} onRemove={() => dispatch({ type: "remove-education", index })}><div className="grid gap-3 sm:grid-cols-2">{([["institution", "Institution"], ["degree", "Degree"], ["location", "Location"], ["duration", "Dates"], ["gpa", "GPA"]] as const).map(([field, label]) => <Field key={field} label={label}><Input value={String(item[field] ?? "")} onChange={(e) => dispatch({ type: "update-education", index, patch: { [field]: e.target.value } })} /></Field>)}</div></Entry>)}</RepeatSection>;
}

function Projects({ state, dispatch }: { state: typeof initialResumeCreatorState; dispatch: Dispatch<ResumeCreatorAction> }) {
  return <RepeatSection title="Projects" description="Show what you built, the tools you used, and why it mattered." onAdd={() => dispatch({ type: "add-project" })} addLabel="Add project">{state.projects.map((item, index) => <Entry key={index} title={item.name || `Project ${index + 1}`} onRemove={() => dispatch({ type: "remove-project", index })}><div className="grid gap-3 sm:grid-cols-2">{([["name", "Project name"], ["technologies", "Technologies"], ["link", "Project link"], ["dates", "Dates"]] as const).map(([field, label]) => <Field key={field} label={label}><Input value={String(item[field] ?? "")} onChange={(e) => dispatch({ type: "update-project", index, patch: { [field]: e.target.value } })} /></Field>)}</div><Field className="mt-3" label="Project highlights (one per line)"><Textarea value={item.descriptions.join("\n")} onChange={(e) => dispatch({ type: "update-project", index, patch: { descriptions: e.target.value.split("\n") } })} /></Field></Entry>)}</RepeatSection>;
}

function Extras({ state, setField }: { state: typeof initialResumeCreatorState; setField(field: keyof typeof state, value: unknown): void; dispatch: Dispatch<ResumeCreatorAction> }) {
  const named = (field: "certifications" | "awards" | "languages", label: string) => <NamedRecords label={label} records={state[field] ?? []} onChange={(records) => setField(field, records)} />;
  return <div className="space-y-6"><div><h2 className="text-xl font-semibold">Skills and additional proof</h2><p className="mt-2 text-sm text-muted-foreground">Use commas between skills. Add as many categories as you need.</p></div><div className="space-y-3">{Object.entries(state.skills).map(([category, skills]) => <div className="grid gap-2 sm:grid-cols-[12rem_1fr_auto]" key={category}><Input aria-label="Skill category" value={category} onChange={(e) => { const next = { ...state.skills }; delete next[category]; next[e.target.value] = skills; setField("skills", next); }} /><Input aria-label={`${category} skills`} value={skills.join(", ")} onChange={(e) => setField("skills", { ...state.skills, [category]: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} /><Button aria-label={`Remove ${category} skills`} size="icon" variant="ghost" onClick={() => { const next = { ...state.skills }; delete next[category]; setField("skills", next); }}><Trash2 className="h-4 w-4" /></Button></div>)}<Button variant="outline" onClick={() => setField("skills", { ...state.skills, [`Category ${Object.keys(state.skills).length + 1}`]: [] })}><Plus className="mr-2 h-4 w-4" />Add skill category</Button></div>{named("certifications", "Certifications")}{named("awards", "Awards")}{named("languages", "Languages")}<CustomSections sections={state.customSections} onChange={(sections) => setField("customSections", sections)} /></div>;
}

function CustomSections({ sections, onChange }: { sections: typeof initialResumeCreatorState.customSections; onChange(sections: typeof initialResumeCreatorState.customSections): void }) {
  return <section><div className="flex items-center justify-between"><div><h3 className="font-semibold">Custom sections</h3><p className="mt-1 text-xs text-muted-foreground">Add publications, volunteering, interests, or any section your story needs.</p></div><Button size="sm" variant="outline" onClick={() => onChange([...sections, { title: "", items: [""] }])}><Plus className="mr-2 h-3.5 w-3.5" />Add section</Button></div><div className="mt-3 space-y-3">{sections.map((section, index) => <div className="rounded-lg border border-border bg-workspace-inset p-3" key={index}><div className="flex gap-2"><Input aria-label={`Custom section ${index + 1} title`} placeholder="Section title" value={section.title} onChange={(event) => onChange(sections.map((item, itemIndex) => itemIndex === index ? { ...item, title: event.target.value } : item))} /><Button aria-label={`Remove custom section ${index + 1}`} size="icon" variant="ghost" onClick={() => onChange(sections.filter((_, itemIndex) => itemIndex !== index))}><Trash2 className="h-4 w-4" /></Button></div><Textarea aria-label={`Custom section ${index + 1} items`} className="mt-2" placeholder="One item per line" value={section.items.join("\n")} onChange={(event) => onChange(sections.map((item, itemIndex) => itemIndex === index ? { ...item, items: event.target.value.split("\n") } : item))} /></div>)}</div></section>;
}

function NamedRecords({ label, records, onChange }: { label: string; records: ResumeGenNamedRecord[]; onChange(records: ResumeGenNamedRecord[]): void }) { return <section><div className="flex items-center justify-between"><h3 className="font-semibold">{label}</h3><Button size="sm" variant="outline" onClick={() => onChange([...records, { name: "" }])}><Plus className="mr-2 h-3.5 w-3.5" />Add</Button></div><div className="mt-3 space-y-3">{records.map((record, index) => <div className="grid gap-2 rounded-lg border border-border bg-workspace-inset p-3 sm:grid-cols-4" key={index}><Input placeholder="Name" value={record.name} onChange={(e) => onChange(records.map((item, i) => i === index ? { ...item, name: e.target.value } : item))} /><Input placeholder={label === "Languages" ? "Proficiency" : "Issuer"} value={label === "Languages" ? record.proficiency ?? "" : record.issuer ?? ""} onChange={(e) => onChange(records.map((item, i) => i === index ? { ...item, [label === "Languages" ? "proficiency" : "issuer"]: e.target.value } : item))} /><Input placeholder="Date" value={record.date ?? ""} onChange={(e) => onChange(records.map((item, i) => i === index ? { ...item, date: e.target.value } : item))} /><Button size="icon" variant="ghost" onClick={() => onChange(records.filter((_, i) => i !== index))}><Trash2 className="h-4 w-4" /></Button></div>)}</div></section>; }

function SectionOrder({ order, dispatch }: { order: string[]; dispatch: Dispatch<ResumeCreatorAction> }) { return <div className="mt-6 space-y-2">{order.map((section, index) => <div className="flex items-center justify-between rounded-lg border border-border bg-workspace-inset px-3 py-2" key={section}><span className="text-sm capitalize">{section.replace("_", " ")}</span><span><Button disabled={index === 0} size="icon" variant="ghost" onClick={() => dispatch({ type: "move-section", section, direction: "up" })}><ArrowUp className="h-4 w-4" /></Button><Button disabled={index === order.length - 1} size="icon" variant="ghost" onClick={() => dispatch({ type: "move-section", section, direction: "down" })}><ArrowDown className="h-4 w-4" /></Button></span></div>)}</div>; }
function RepeatSection({ addLabel, children, description, onAdd, title }: { addLabel: string; children: ReactNode; description: string; onAdd(): void; title: string }) { return <div><h2 className="text-xl font-semibold">{title}</h2><p className="mt-2 text-sm text-muted-foreground">{description}</p><div className="mt-6 space-y-4">{children}</div><Button className="mt-4" variant="outline" onClick={onAdd}><Plus className="mr-2 h-4 w-4" />{addLabel}</Button></div>; }
function Entry({ children, onRemove, title }: { children: ReactNode; onRemove(): void; title: string }) { return <article className="rounded-xl border border-border bg-workspace-inset p-4"><header className="mb-4 flex items-center justify-between"><h3 className="font-medium">{title}</h3><Button aria-label={`Remove ${title}`} size="icon" variant="ghost" onClick={onRemove}><Trash2 className="h-4 w-4" /></Button></header>{children}</article>; }
function Field({ children, className = "", label }: { children: ReactNode; className?: string; label: string }) { return <div className={`space-y-2 ${className}`}><Label>{label}</Label>{children}</div>; }
