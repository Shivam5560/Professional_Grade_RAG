'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, Plus, Sparkles, Layers, Trash2, Code2, PlayCircle, Clock } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlHistoryItem, AuraSqlSession } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import { useToast } from '@/hooks/useToast';
import AuthPage from '@/app/auth/page';

export default function AuraSqlHomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [sessions, setSessions] = useState<AuraSqlSession[]>([]);
  const [contextPage, setContextPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast, confirm: toastConfirm } = useToast();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    const load = async () => {
      setLoading(true);
      try {
        const [connData, ctxData, historyData, sessionData] = await Promise.all([
          apiClient.listAuraSqlConnections(),
          apiClient.listAuraSqlContexts(),
          apiClient.listAuraSqlHistory(),
          apiClient.listAuraSqlSessions(),
        ]);
        setConnections(connData);
        setContexts(ctxData);
        setHistory(historyData);
        setSessions(sessionData);
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
    const confirmed = await toastConfirm({
      title: 'Delete connection?',
      description: 'This will remove the connection and its saved contexts.',
      confirmLabel: 'Delete',
      variant: 'destructive',
    });
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlConnection(connectionId);
      setConnections((prev) => prev.filter((conn) => conn.id !== connectionId));
      setContexts((prev) => prev.filter((ctx) => ctx.connection_id !== connectionId));
      toast({ title: 'Connection deleted' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete connection';
      setError(msg);
      toast({ title: 'Delete failed', description: msg, variant: 'destructive' });
    }
  };

  const handleDeleteContext = async (contextId: string) => {
    const confirmed = await toastConfirm({
      title: 'Delete context?',
      description: 'This will remove the saved context.',
      confirmLabel: 'Delete',
      variant: 'destructive',
    });
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlContext(contextId);
      setContexts((prev) => prev.filter((ctx) => ctx.id !== contextId));
      toast({ title: 'Context deleted' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete context';
      setError(msg);
      toast({ title: 'Delete failed', description: msg, variant: 'destructive' });
    }
  };

  const generatedHistory = useMemo(
    () => history.filter((item) => item.status === 'generated'),
    [history]
  );
  const generatedCount = generatedHistory.length;
  const executedCount = useMemo(
    () => history.filter((item) => item.status === 'executed').length,
    [history]
  );

  const recentContexts = useMemo(() => {
    if (generatedHistory.length === 0 || contexts.length === 0) return contexts;
    const seen = new Set<string>();
    const ordered: AuraSqlContext[] = [];
    for (const item of generatedHistory) {
      if (!item.context_id || seen.has(item.context_id)) continue;
      const context = contexts.find((ctx) => ctx.id === item.context_id);
      if (context) {
        ordered.push(context);
        seen.add(context.id);
      }
    }
    return ordered.length > 0 ? ordered : contexts;
  }, [generatedHistory, contexts]);

  const contextPageSize = 3;
  const totalContextPages = Math.max(1, Math.ceil(recentContexts.length / contextPageSize));
  const clampedContextPage = Math.min(contextPage, totalContextPages - 1);
  const pagedContexts = recentContexts.slice(
    clampedContextPage * contextPageSize,
    clampedContextPage * contextPageSize + contextPageSize
  );

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.18),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[12%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl float-slower" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[8%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.16),transparent_70%)] blur-3xl float-slowest" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex flex-col lg:flex-row gap-6">
            <aside className="w-full lg:w-[34%]">
              <Card className="glass-panel sheen-border border-border/60 bg-accent-soft h-full">
                <CardHeader>
                  <CardTitle>History</CardTitle>
                  <CardDescription>Chat sessions powered by AuraSQL.</CardDescription>
                </CardHeader>
                <CardContent className="h-[520px]">
                  <ScrollArea className="h-full pr-3">
                    {loading ? (
                      <div className="space-y-3">
                        {[1,2,3,4].map(i => (
                          <div key={i} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                            <Skeleton className="h-4 w-3/4 mb-2" />
                            <Skeleton className="h-3 w-1/2" />
                          </div>
                        ))}
                      </div>
                    ) : sessions.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No history yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {sessions.map((session) => (
                          <button
                            key={session.id}
                            type="button"
                            onClick={() => router.push(`/aurasql/query?session=${session.id}`)}
                            className="w-full text-left rounded-2xl border border-border/60 bg-card/60 px-4 py-3 hover:border-foreground/20 hover:bg-card/80 hover:shadow-sm transition-all"
                          >
                            <p className="text-sm font-semibold text-foreground line-clamp-2">
                              {session.title || 'AuraSQL chat'}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Updated {session.updated_at || session.created_at}
                            </p>
                          </button>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </aside>

            <section className="flex-1 space-y-8">
              <div className="glass-panel sheen-border rounded-3xl p-6 md:p-10 bg-accent-soft flex flex-col gap-4">
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

              {error && (
                <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 dark:bg-rose-500/[0.03] px-5 py-3 text-sm text-rose-600 dark:text-rose-300 flex items-center gap-2">
                  <span className="flex-shrink-0 h-2 w-2 rounded-full bg-rose-500" />
                  {error}
                </div>
              )}

              <div className="grid gap-6 md:grid-cols-3">
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft hover-glow transition-transform hover:-translate-y-1">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center">
                        <Code2 className="h-5 w-5 text-indigo-500" />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Generated SQL</p>
                        <p className="text-xs text-muted-foreground">Total created queries</p>
                      </div>
                    </div>
                    <p className="text-4xl font-black text-foreground">
                      <AnimatedCounter value={generatedCount} />
                    </p>
                  </CardContent>
                </Card>
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft hover-glow transition-transform hover:-translate-y-1">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center">
                        <PlayCircle className="h-5 w-5 text-emerald-500" />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Executed SQL</p>
                        <p className="text-xs text-muted-foreground">Total executed queries</p>
                      </div>
                    </div>
                    <p className="text-4xl font-black text-foreground">
                      <AnimatedCounter value={executedCount} />
                    </p>
                  </CardContent>
                </Card>
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft hover-glow transition-transform hover:-translate-y-1">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/20 flex items-center justify-center">
                        <Clock className="h-5 w-5 text-amber-500" />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Recent Activity</p>
                        <p className="text-xs text-muted-foreground">Latest generations</p>
                      </div>
                    </div>
                    <div className="space-y-2 mt-1">
                      {generatedHistory.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No activity yet</p>
                      ) : generatedHistory.slice(0, 3).map((item) => (
                        <div key={item.id} className="flex items-center justify-between text-xs text-muted-foreground">
                          <span className="line-clamp-1 max-w-[180px]">
                            {item.natural_language_query || item.generated_sql || 'SQL execution'}
                          </span>
                          <Badge variant="secondary" className="text-[9px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border-emerald-500/20">generated</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                  <CardHeader>
                    <CardTitle>Connections</CardTitle>
                    <CardDescription>Pick a saved connection to start querying.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {loading ? (
                      <div className="space-y-3">
                        {[1,2].map(i => (
                          <div key={i} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                            <Skeleton className="h-4 w-2/3 mb-2" />
                            <Skeleton className="h-3 w-1/2" />
                          </div>
                        ))}
                      </div>
                    ) : connections.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No connections yet.</p>
                    ) : (
                      connections.map((connection) => (
                        <div key={connection.id} className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/60 px-4 py-3 hover:border-foreground/20 hover:shadow-sm transition-all group">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                              <Database className="h-4 w-4 text-indigo-500" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-foreground">{connection.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {connection.db_type} • {connection.database} • {connection.schema_name || 'default'}
                              </p>
                            </div>
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

                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                  <CardHeader>
                    <CardTitle>Saved Contexts</CardTitle>
                    <CardDescription>Latest used contexts.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {loading ? (
                      <div className="space-y-3">
                        {[1,2].map(i => (
                          <div key={i} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                            <Skeleton className="h-4 w-2/3 mb-2" />
                            <Skeleton className="h-3 w-1/3" />
                          </div>
                        ))}
                      </div>
                    ) : contexts.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No contexts yet.</p>
                    ) : (
                      pagedContexts.map((context) => (
                        <div key={context.id} className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/60 px-4 py-3 hover:border-foreground/20 hover:shadow-sm transition-all group">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                              <Layers className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-foreground">{context.name}</p>
                              <p className="text-xs text-muted-foreground">{context.table_names.join(', ')}</p>
                            </div>
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
                    <div className="flex items-center justify-between">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setContextPage((prev) => Math.max(0, prev - 1))}
                        disabled={clampedContextPage === 0}
                      >
                        Prev
                      </Button>
                      <span className="text-xs text-muted-foreground">
                        Page {clampedContextPage + 1} of {totalContextPages}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setContextPage((prev) => Math.min(totalContextPages - 1, prev + 1))}
                        disabled={clampedContextPage >= totalContextPages - 1}
                      >
                        Next
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>
          </div>
        </div>
      </main>

    </div>
  );
}

function AnimatedCounter({ value, duration = 1400 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * value));
      if (progress < 1) {
        frame = requestAnimationFrame(step);
      }
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return <span>{display}</span>;
}
