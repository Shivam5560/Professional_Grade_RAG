"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  Trash2,
} from "lucide-react";

import { ActionDock } from "@/components/shell/ActionDock";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Inspector } from "@/components/shell/Inspector";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import type { DocumentInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return "Unknown size";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (date: string): string => {
  const parsed = new Date(date);
  return Number.isNaN(parsed.getTime()) ? date : parsed.toLocaleString();
};

export default function KnowledgeBasePage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { confirm, toast } = useToast();
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeDocument, setActiveDocument] = useState<DocumentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const loadDocuments = useCallback(async (userId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getUserDocuments(userId);
      setDocuments(response.documents);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => setHydrated(true), []);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.push("/auth");
      return;
    }
    loadDocuments(user.id);
  }, [hydrated, loadDocuments, router, user]);

  const totalVectors = useMemo(
    () => documents.reduce((total, document) => total + (document.vector_count || 0), 0),
    [documents],
  );

  const selectAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(documents.map((document) => document.id)) : new Set());
  };

  const selectOne = (id: string, checked: boolean) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const deleteSelected = async () => {
    if (!user || selectedIds.size === 0) return;
    const approved = await confirm({
      title: "Delete documents?",
      description: `Delete ${selectedIds.size} document${selectedIds.size === 1 ? "" : "s"}? This cannot be undone.`,
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      variant: "destructive",
    });
    if (!approved) return;

    setDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await apiClient.bulkDeleteDocuments({
        document_ids: Array.from(selectedIds),
        user_id: user.id,
      });
      setSuccess(response.message);
      setSelectedIds(new Set());
      setActiveDocument(null);
      toast({ title: "Documents deleted", description: response.message });
      await loadDocuments(user.id);
    } catch (deleteError) {
      const message = deleteError instanceof Error ? deleteError.message : "Failed to delete documents";
      setError(message);
      toast({ title: "Delete failed", description: message, variant: "destructive" });
    } finally {
      setDeleting(false);
    }
  };

  if (!hydrated || loading) {
    return (
      <FocusCanvas ariaLabel="Knowledge documents loading">
        <div className="grid min-h-[70svh] place-items-center">
          <div className="text-center" role="status">
            <Loader2 className="mx-auto h-6 w-6 animate-spin text-foreground" />
            <p className="mt-3 text-sm text-muted-foreground">Loading Knowledge documents...</p>
          </div>
        </div>
      </FocusCanvas>
    );
  }

  return (
    <FocusCanvas ariaLabel="Knowledge documents">
      <CanvasHeader
        actions={
          <Button onClick={() => router.push("/chat")} size="sm">
            Open conversation
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        }
        description="Review the source material available to Knowledge Studio. Select a record for details."
        eyebrow="Knowledge Studio"
        title="Documents"
      />

      <ContextRibbon label="Library">
        <span className="inline-flex h-7 items-center rounded-md border border-border/70 bg-background/70 px-2.5 text-xs text-muted-foreground">
          {documents.length} document{documents.length === 1 ? "" : "s"}
        </span>
        <span className="inline-flex h-7 items-center rounded-md border border-border/70 bg-background/70 px-2.5 text-xs text-muted-foreground">
          {totalVectors.toLocaleString()} indexed vectors
        </span>
        {selectedIds.size > 0 ? (
          <span className="inline-flex h-7 items-center rounded-md bg-foreground px-2.5 text-xs text-background">
            {selectedIds.size} selected
          </span>
        ) : null}
      </ContextRibbon>

      <div className="pt-4">
        {error ? (
          <Alert className="mb-4" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        {success ? (
          <Alert className="mb-4 border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        ) : null}

        {documents.length === 0 ? (
          <section className="grid min-h-[56svh] place-items-center border-y border-border/60" aria-label="Empty document library">
            <div className="max-w-sm px-6 text-center">
              <FileText className="mx-auto h-7 w-7 text-muted-foreground" />
              <h2 className="mt-4 text-lg font-semibold text-foreground">No documents yet</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Add source material from a Knowledge conversation to build this library.
              </p>
              <Button className="mt-5" onClick={() => router.push("/chat")}>
                Start a conversation
              </Button>
            </div>
          </section>
        ) : (
          <section className="overflow-hidden rounded-lg border border-border/70 bg-background/72 backdrop-blur-xl" aria-label="Document library">
            <div className="flex min-h-12 items-center justify-between gap-4 border-b border-border/70 px-4">
              <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
                <input
                  aria-label="Select all documents"
                  checked={selectedIds.size === documents.length}
                  className="h-4 w-4 rounded border-border"
                  onChange={(event) => selectAll(event.target.checked)}
                  type="checkbox"
                />
                Select all
              </label>
              <span className="text-xs text-muted-foreground">Newest source material first</span>
            </div>

            <div className="divide-y divide-border/60">
              {documents.map((document) => (
                <article
                  className={cn(
                    "group grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3.5 transition-colors hover:bg-muted/45 sm:gap-4",
                    selectedIds.has(document.id) && "bg-foreground/[0.055]",
                  )}
                  key={document.id}
                >
                  <input
                    aria-label={`Select ${document.filename}`}
                    checked={selectedIds.has(document.id)}
                    className="h-4 w-4 rounded border-border"
                    onChange={(event) => selectOne(document.id, event.target.checked)}
                    type="checkbox"
                  />
                  <button className="min-w-0 text-left" onClick={() => setActiveDocument(document)} type="button">
                    <span className="block truncate text-sm font-medium text-foreground">{document.title || document.filename}</span>
                    <span className="mt-1 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                      {document.title ? <span className="max-w-64 truncate">{document.filename}</span> : null}
                      <span>{formatFileSize(document.file_size)}</span>
                      <span className="hidden sm:inline">{document.vector_count.toLocaleString()} vectors</span>
                      <span className="hidden lg:inline">{formatDate(document.upload_date)}</span>
                    </span>
                  </button>
                  <Button aria-label={`View details for ${document.filename}`} onClick={() => setActiveDocument(document)} size="icon" variant="ghost">
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>

      {documents.length > 0 ? (
        <ActionDock
          primary={
            <Button onClick={() => router.push("/chat")} size="sm">
              Use in chat
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          }
          secondary={
            <Button
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              disabled={selectedIds.size === 0 || deleting}
              onClick={deleteSelected}
              size="sm"
              variant="ghost"
            >
              {deleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
              Delete{selectedIds.size > 0 ? ` ${selectedIds.size}` : ""}
            </Button>
          }
        />
      ) : null}

      <Inspector onOpenChange={(open) => !open && setActiveDocument(null)} open={Boolean(activeDocument)} title="Document details">
        {activeDocument ? (
          <div className="space-y-6">
            <div>
              <Badge variant="outline">{activeDocument.file_type || "Document"}</Badge>
              <h2 className="mt-3 break-words text-xl font-semibold text-foreground">
                {activeDocument.title || activeDocument.filename}
              </h2>
              {activeDocument.title ? <p className="mt-1 break-all text-sm text-muted-foreground">{activeDocument.filename}</p> : null}
            </div>
            <dl className="divide-y divide-border/60 border-y border-border/60 text-sm">
              <div className="flex items-center justify-between gap-6 py-3">
                <dt className="text-muted-foreground">Size</dt>
                <dd className="font-medium text-foreground">{formatFileSize(activeDocument.file_size)}</dd>
              </div>
              <div className="flex items-center justify-between gap-6 py-3">
                <dt className="text-muted-foreground">Indexed vectors</dt>
                <dd className="font-medium text-foreground">{activeDocument.vector_count.toLocaleString()}</dd>
              </div>
              <div className="flex items-center justify-between gap-6 py-3">
                <dt className="text-muted-foreground">Uploaded</dt>
                <dd className="text-right font-medium text-foreground">{formatDate(activeDocument.upload_date)}</dd>
              </div>
            </dl>
            <Button className="w-full" onClick={() => router.push("/chat")}>
              Open Knowledge conversation
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        ) : null}
      </Inspector>
    </FocusCanvas>
  );
}
