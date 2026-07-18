"use client";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export function DeleteAuraSqlResourceDialog({
  deleting,
  error,
  onCancel,
  onConfirm,
  open,
  resourceName,
  resourceType,
}: {
  deleting: boolean;
  error: string | null;
  onCancel(): void;
  onConfirm(): void;
  open: boolean;
  resourceName: string;
  resourceType: "connection" | "context";
}): JSX.Element {
  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next && !deleting) onCancel(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete {resourceType}</DialogTitle>
          <DialogDescription>Delete “{resourceName}”? This removes the saved {resourceType} from AuraSQL.</DialogDescription>
        </DialogHeader>
        {error ? <p role="alert" className="mt-4 text-sm text-destructive">{error}</p> : null}
        <DialogFooter>
          <Button disabled={deleting} onClick={onCancel} variant="ghost">Cancel</Button>
          <Button disabled={deleting} onClick={onConfirm} variant="destructive">{deleting ? "Deleting…" : "Delete"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
