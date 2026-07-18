"use client";

import { useState } from "react";
import { FileUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { StructuredCareerSource } from "@/lib/studios/career/types";

export function ResumeIntake({ file, onFileChange, onStructuredImport }: { file: File | null; onFileChange(file: File | null): void; onStructuredImport?(payload: StructuredCareerSource): Promise<void> }): JSX.Element {
  const [advanced, setAdvanced] = useState(false);
  const [structuredName, setStructuredName] = useState("");
  const [structuredError, setStructuredError] = useState<string | null>(null);
  const importStructured = async (selected: File | undefined) => {
    if (!selected || !onStructuredImport) return;
    setStructuredError(null);
    try {
      const parsed = JSON.parse(await selected.text()) as { filename?: unknown; claims?: unknown };
      if (!Array.isArray(parsed.claims) || parsed.claims.length === 0) throw new Error("JSON must contain a non-empty claims array.");
      await onStructuredImport({ filename: typeof parsed.filename === "string" && parsed.filename.trim() ? parsed.filename : selected.name, media_type: "application/json", ingestion_mode: "structured", claims: parsed.claims });
      setStructuredName(selected.name);
    } catch (reason) { setStructuredError(reason instanceof Error ? reason.message : "Structured import failed"); }
  };
  return (
    <div className="space-y-4">
      <label className="flex min-h-36 cursor-pointer items-center gap-4 rounded-xl border border-dashed border-border bg-workspace-inset p-5 transition-colors hover:border-foreground/40">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-workspace-raised"><FileUp className="h-5 w-5" /></span>
        <span><span className="block text-sm font-semibold">{file?.name ?? "Choose your resume"}</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">PDF, DOC, DOCX, or TXT · up to 10 MB</span></span>
        <input aria-label="Upload resume" className="sr-only" type="file" accept=".pdf,.doc,.docx,.txt" onChange={(event) => onFileChange(event.target.files?.[0] ?? null)} />
      </label>
      {onStructuredImport ? <Button type="button" variant="ghost" size="sm" onClick={() => setAdvanced((value) => !value)}>Advanced structured import</Button> : null}
      {advanced && onStructuredImport ? <label className="block rounded-lg border border-border bg-workspace-inset p-4 text-sm"><span className="font-medium">Import verified claim JSON</span><span className="mt-1 block text-xs text-muted-foreground">Use a Career claim bundle with a non-empty claims array.</span><input aria-label="Import structured JSON" className="mt-3 block w-full text-xs" type="file" accept=".json,application/json" onChange={(event) => void importStructured(event.target.files?.[0])} />{structuredName ? <span className="mt-2 block text-xs">Imported {structuredName}</span> : null}{structuredError ? <span role="alert" className="mt-2 block text-xs text-destructive">{structuredError}</span> : null}</label> : null}
    </div>
  );
}
