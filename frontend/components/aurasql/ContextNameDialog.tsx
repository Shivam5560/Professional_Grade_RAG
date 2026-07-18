"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ContextNameDialogProps {
  connectionLabel: string;
  error: string | null;
  initialName?: string;
  onCancel(): void;
  onSave(name: string): void | Promise<void>;
  open: boolean;
  saving: boolean;
  selectedTables: string[];
}

export function ContextNameDialog({
  connectionLabel,
  error,
  initialName = "",
  onCancel,
  onSave,
  open,
  saving,
  selectedTables,
}: ContextNameDialogProps): JSX.Element {
  const [name, setName] = useState(initialName);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(initialName);
    setValidationError(null);
  }, [initialName, open]);

  const submit = () => {
    const trimmed = name.trim();
    if (!trimmed) {
      setValidationError("Enter a context name.");
      return;
    }
    setValidationError(null);
    void onSave(trimmed);
  };

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next && !saving) onCancel(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Name schema context</DialogTitle>
          <DialogDescription>Save this table selection so future questions begin with the right schema.</DialogDescription>
        </DialogHeader>
        <div className="mt-5 space-y-4">
          <div className="rounded-lg border border-border bg-workspace-inset p-3 text-xs">
            <p className="font-medium">{connectionLabel || "Selected connection"}</p>
            <p className="mt-1 text-muted-foreground">{selectedTables.length} tables selected</p>
            <p className="mt-2 line-clamp-2 font-mono text-[11px] text-muted-foreground">{selectedTables.join(" · ")}</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="context-name">Context name</Label>
            <Input id="context-name" aria-label="Context name" autoComplete="off" value={name} onChange={(event) => setName(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); submit(); } }} />
          </div>
          {validationError || error ? <p role="alert" className="text-sm text-destructive">{validationError ?? error}</p> : null}
        </div>
        <DialogFooter>
          <Button disabled={saving} onClick={onCancel} type="button" variant="ghost">Cancel</Button>
          <Button disabled={saving} onClick={submit} type="button">{saving ? "Saving…" : "Save context"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
