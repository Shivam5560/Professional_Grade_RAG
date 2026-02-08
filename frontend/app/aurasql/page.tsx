'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Database, Plus, Sparkles, Layers, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlHistoryItem } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function AuraSqlHomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    const load = async () => {
      setLoading(true);
      try {
        const [connData, ctxData, historyData] = await Promise.all([
          apiClient.listAuraSqlConnections(),
          apiClient.listAuraSqlContexts(),
          apiClient.listAuraSqlHistory(),
        ]);
        setConnections(connData);
        setContexts(ctxData);
        setHistory(historyData);
      } catch (err) {
        console.error('Failed to load AuraSQL data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load AuraSQL data');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [isAuthenticated]);

  const handleDeleteConnection = async (connectionId: string) => {
    const confirmed = window.confirm('Delete this connection? This will remove its saved contexts.');
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlConnection(connectionId);
      setConnections((prev) => prev.filter((conn) => conn.id !== connectionId));
      setContexts((prev) => prev.filter((ctx) => ctx.connection_id !== connectionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete connection');
    }
  };

  const handleDeleteContext = async (contextId: string) => {
    const confirmed = window.confirm('Delete this context?');
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlContext(contextId);
      setContexts((prev) => prev.filter((ctx) => ctx.id !== contextId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete context');
    }
  };

  const generatedCount = useMemo(
    () => history.filter((item) => item.status === 'generated').length,
    [history]
  );
  const executedCount = useMemo(
    () => history.filter((item) => item.status === 'executed').length,
    [history]
  );

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="glass-panel rounded-3xl p-6 md:p-10 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                <Database className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-3xl font-black">AuraSQL Workspace</h1>
                <p className="text-sm text-muted-foreground">
                  Manage database connections and reusable schema contexts.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                {connections.length} connections
              </Badge>
              <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                {contexts.length} saved contexts
              </Badge>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => router.push('/aurasql/connections/new')}>
                <Plus className="h-4 w-4 mr-2" />
                New Connection
              </Button>
              <Button variant="outline" onClick={() => router.push('/aurasql/contexts/new')}>
                <Layers className="h-4 w-4 mr-2" />
                New Context
              </Button>
              <Button variant="ghost" onClick={() => router.push('/aurasql/query')}>
                <Sparkles className="h-4 w-4 mr-2" />
                Open AuraSQL Chat
              </Button>
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="grid gap-6 md:grid-cols-3">
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Generated SQL</CardTitle>
                <CardDescription>Total created queries.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-black">{generatedCount}</p>
              </CardContent>
            </Card>
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Executed SQL</CardTitle>
                <CardDescription>Total executed queries.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-black">{executedCount}</p>
              </CardContent>
            </Card>
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest SQL generations.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {history.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="line-clamp-1">
                      {item.natural_language_query || item.generated_sql || 'SQL execution'}
                    </span>
                    <span className="uppercase">{item.status}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Connections</CardTitle>
                <CardDescription>Pick a saved connection to start querying.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {loading ? (
                  <p className="text-sm text-muted-foreground">Loading connections...</p>
                ) : connections.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No connections yet.</p>
                ) : (
                  connections.map((connection) => (
                    <div key={connection.id} className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                      <div>
                        <p className="text-sm font-semibold text-foreground">{connection.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {connection.db_type} • {connection.database} • {connection.schema_name || 'default'}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => router.push(`/aurasql/query?connection=${connection.id}`)}>
                          Open
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => router.push(`/aurasql/connections/${connection.id}`)}>
                          Edit
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDeleteConnection(connection.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>SQL History</CardTitle>
                <CardDescription>Latest generated and executed queries.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {loading ? (
                  <p className="text-sm text-muted-foreground">Loading history...</p>
                ) : history.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No history yet.</p>
                ) : (
                  history.slice(0, 6).map((item) => (
                    <div key={item.id} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                      <p className="text-sm font-semibold text-foreground line-clamp-1">
                        {item.natural_language_query || item.generated_sql || 'SQL execution'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.status} • {item.created_at}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          <Card className="glass-panel border-border/60">
            <CardHeader>
              <CardTitle>Saved Contexts</CardTitle>
              <CardDescription>Manage context definitions per schema.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {loading ? (
                <p className="text-sm text-muted-foreground">Loading contexts...</p>
              ) : contexts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No contexts yet.</p>
              ) : (
                contexts.map((context) => (
                  <div key={context.id} className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{context.name}</p>
                      <p className="text-xs text-muted-foreground">{context.table_names.join(', ')}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => router.push(`/aurasql/query?context=${context.id}`)}>
                        Query
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleDeleteContext(context.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
