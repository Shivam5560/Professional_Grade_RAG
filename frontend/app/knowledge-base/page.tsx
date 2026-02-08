'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { DocumentInfo } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Trash2, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '@/lib/store';
import { Header } from '@/components/layout/Header';
import { useToast } from '@/hooks/useToast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AuraSqlContext } from '@/lib/types';

export default function KnowledgeBasePage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [loadingContexts, setLoadingContexts] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const { confirm, toast } = useToast();

  const loadDocuments = useCallback(async (userId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getUserDocuments(userId);
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadContexts = useCallback(async () => {
    setLoadingContexts(true);
    try {
      const response = await apiClient.listAuraSqlContexts();
      setContexts(response);
    } catch (err) {
      console.error('Failed to load contexts:', err);
    } finally {
      setLoadingContexts(false);
    }
  }, []);

  // Wait for Zustand to hydrate from localStorage
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    // Only check auth after hydration
    if (!isHydrated) return;
    
    // Check if user is logged in
    if (!user) {
      router.push('/auth');
      return;
    }
    
    // Fetch user's documents
    loadDocuments(user.id);
    loadContexts();
  }, [router, user, isHydrated, loadDocuments, loadContexts]);

  // Show loading state while hydrating
  if (!isHydrated || (loading && documents.length === 0 && loadingContexts)) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 app-aurora" />
        <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
        <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
        <Header />
        <div className="relative z-10 flex min-h-[calc(100vh-4rem)] items-center justify-center">
          <div className="text-center glass-panel rounded-3xl px-8 py-10">
            <Loader2 className="h-8 w-8 animate-spin text-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Loading Knowledge Base...</p>
          </div>
        </div>
      </div>
    );
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(documents.map(doc => doc.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  const handleBulkDelete = async () => {
    if (!user || selectedIds.size === 0) return;

    const approved = await confirm({
      title: "Delete documents?",
      description: `Delete ${selectedIds.size} document(s)? This action cannot be undone.`,
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
      toast({
        title: "Documents deleted",
        description: response.message,
      });
      
      // Reload documents
      await loadDocuments(user.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete documents');
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : 'Failed to delete documents',
        variant: "destructive",
      });
    } finally {
      setDeleting(false);
    }
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 app-aurora" />
        <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
        <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
        <Header />
        <div className="relative z-10 flex min-h-[calc(100vh-4rem)] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-8">
        <div className="glass-panel rounded-3xl p-6 md:p-8 max-w-6xl mx-auto">
          <div className="flex flex-col gap-2 mb-6">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center shadow-lg ring-2 ring-foreground/10">
                <FileText className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-foreground">Knowledge Base</h1>
                <p className="text-sm text-muted-foreground">
                  Manage your uploaded documents and keep your chat context clean.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4 border-red-500/30 bg-red-500/10 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="mb-4 border-emerald-500/30 bg-emerald-500/10 text-emerald-600">
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="documents" className="space-y-4">
            <TabsList className="bg-muted/40">
              <TabsTrigger value="documents">Documents</TabsTrigger>
              <TabsTrigger value="contexts">SQL Contexts</TabsTrigger>
            </TabsList>

            <TabsContent value="documents" className="space-y-4">
              {documents.length === 0 ? (
                <div className="text-center py-14">
                  <div className="mx-auto mb-6 h-16 w-16 rounded-2xl bg-muted/70 flex items-center justify-center">
                    <FileText className="h-8 w-8 text-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">No documents yet</h3>
                  <p className="text-muted-foreground mb-6">Upload your first document to get started.</p>
                  <Button onClick={() => router.push('/chat')} className="bg-foreground text-background shadow-lg">
                    Go to Chat
                  </Button>
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedIds.size === documents.length && documents.length > 0}
                          onChange={(e) => handleSelectAll(e.target.checked)}
                          className="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/40"
                        />
                        <span className="text-sm font-medium text-foreground">Select All</span>
                      </label>
                      {selectedIds.size > 0 && (
                        <Badge variant="secondary" className="bg-primary/10 text-primary border border-primary/20">
                          {selectedIds.size} selected
                        </Badge>
                      )}
                    </div>

                    <Button
                      onClick={handleBulkDelete}
                      disabled={selectedIds.size === 0 || deleting}
                      variant="destructive"
                      size="sm"
                    >
                      {deleting ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        <>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Selected
                        </>
                      )}
                    </Button>
                  </div>

                  <div className="border border-border/70 rounded-2xl overflow-hidden bg-card/70">
                    <table className="min-w-full divide-y divide-border">
                      <thead className="bg-muted/60">
                        <tr>
                          <th className="w-12 px-4 py-3"></th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Filename
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Size
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Vectors
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            Uploaded
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-card/60 divide-y divide-border">
                        {documents.map((doc) => (
                          <tr
                            key={doc.id}
                            className={`hover:bg-muted/40 transition-colors ${
                              selectedIds.has(doc.id) ? 'bg-primary/10' : ''
                            }`}
                          >
                            <td className="px-4 py-4">
                              <input
                                type="checkbox"
                                checked={selectedIds.has(doc.id)}
                                onChange={(e) => handleSelectOne(doc.id, e.target.checked)}
                                className="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/40"
                              />
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex flex-col">
                                <span className="text-sm font-medium text-foreground">
                                  {doc.filename}
                                </span>
                                {doc.title && (
                                  <span className="text-xs text-muted-foreground">{doc.title}</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <Badge variant="outline" className="text-xs">
                                {doc.file_type || 'N/A'}
                              </Badge>
                            </td>
                            <td className="px-4 py-4 text-sm text-foreground">
                              {formatFileSize(doc.file_size)}
                            </td>
                            <td className="px-4 py-4">
                              <Badge variant="secondary" className="text-xs">
                                {doc.vector_count}
                              </Badge>
                            </td>
                            <td className="px-4 py-4 text-sm text-muted-foreground">
                              {formatDate(doc.upload_date)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="mt-4 text-sm text-muted-foreground">
                    Total: {documents.length} document{documents.length !== 1 ? 's' : ''}
                  </div>
                </>
              )}
            </TabsContent>

            <TabsContent value="contexts" className="space-y-4">
              {loadingContexts ? (
                <p className="text-sm text-muted-foreground">Loading contexts...</p>
              ) : contexts.length === 0 ? (
                <div className="text-center py-14">
                  <div className="mx-auto mb-6 h-16 w-16 rounded-2xl bg-muted/70 flex items-center justify-center">
                    <FileText className="h-8 w-8 text-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">No SQL contexts yet</h3>
                  <p className="text-muted-foreground mb-6">Create a schema context to reuse SQL knowledge.</p>
                  <Button onClick={() => router.push('/aurasql/contexts/new')} className="bg-foreground text-background shadow-lg">
                    Create SQL Context
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {contexts.map((context) => (
                    <div key={context.id} className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/70 px-4 py-3">
                      <div>
                        <p className="text-sm font-semibold text-foreground">{context.name}</p>
                        <p className="text-xs text-muted-foreground">{context.table_names.join(', ')}</p>
                      </div>
                      <Button size="sm" onClick={() => router.push(`/aurasql/query?context=${context.id}`)}>
                        Query
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
