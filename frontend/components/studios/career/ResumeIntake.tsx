"use client";

import { useState } from "react";
import { FileUp } from "lucide-react";

import { Button } from "@/components/ui/button";

export function ResumeIntake({ file, onFileChange }: { file: File | null; onFileChange(file: File | null): void }): JSX.Element {
  const [advanced, setAdvanced] = useState(false);
  return (
    <div className="space-y-4">
      <label className="flex min-h-36 cursor-pointer items-center gap-4 rounded-xl border border-dashed border-border bg-workspace-inset p-5 transition-colors hover:border-foreground/40">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-workspace-raised"><FileUp className="h-5 w-5" /></span>
        <span><span className="block text-sm font-semibold">{file?.name ?? "Choose your resume"}</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">PDF, DOC, DOCX, or TXT · up to 10 MB</span></span>
        <input aria-label="Upload resume" className="sr-only" type="file" accept=".pdf,.doc,.docx,.txt" onChange={(event) => onFileChange(event.target.files?.[0] ?? null)} />
      </label>
      <Button type="button" variant="ghost" size="sm" onClick={() => setAdvanced((value) => !value)}>Advanced structured import</Button>
      {advanced ? <label className="block rounded-lg border border-border bg-workspace-inset p-4 text-sm"><span className="font-medium">Import verified claim JSON</span><input aria-label="Import structured JSON" className="mt-3 block w-full text-xs" type="file" accept=".json,application/json" /></label> : null}
    </div>
  );
}
