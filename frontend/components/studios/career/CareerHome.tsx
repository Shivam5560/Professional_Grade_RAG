import { FileSearch, PenLine, Sparkles } from "lucide-react";

export type CareerWorkflow = "score" | "tailor" | "create";

const workflows = [
  { id: "score" as const, title: "Score Resume", description: "Evaluate an existing resume against a target role without changing it.", icon: FileSearch, action: "Score Resume" },
  { id: "tailor" as const, title: "Tailor Resume", description: "Explicitly create an evidence-grounded revision for one job description.", icon: Sparkles, action: "Tailor Resume" },
  { id: "create" as const, title: "Create Resume", description: "Enter your complete career details and export a polished LaTeX PDF.", icon: PenLine, action: "Create Resume" },
];

export function CareerHome({ onSelect }: { onSelect(workflow: CareerWorkflow): void }): JSX.Element {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {workflows.map(({ action, description, icon: Icon, id, title }) => (
        <article className="flex min-h-64 flex-col rounded-xl border border-border bg-workspace-raised p-6 shadow-sm" key={id}>
          <span className="grid h-11 w-11 place-items-center rounded-lg bg-workspace-inset"><Icon className="h-5 w-5" /></span>
          <h2 className="mt-6 text-xl font-semibold">{title}</h2>
          <p className="mt-2 flex-1 text-sm leading-6 text-muted-foreground">{description}</p>
          <button className="mt-6 inline-flex h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground" onClick={() => onSelect(id)} type="button">{action}</button>
        </article>
      ))}
    </div>
  );
}
