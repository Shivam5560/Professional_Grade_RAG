'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, Plus, Sparkles, Layers, Trash2, MessageSquare, Home, ChevronDown } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlHistoryItem, AuraSqlSession } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import { useToast } from '@/hooks/useToast';
import AuthPage from '@/app/auth/page';
import VerticalMagnificationDock from '@/components/ui/vertical-magnification-dock';
import { ShaderAnimation } from '@/components/ui/shader-animation';

export default function AuraSqlHomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [sessions, setSessions] = useState<AuraSqlSession[]>([]);
  const [contextPage, setContextPage] = useState(0);
  const [activePanel, setActivePanel] = useState<'history' | 'actions'>('history');
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [showAllHistory, setShowAllHistory] = useState(false);
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
  const trackedCount = generatedCount + executedCount;
  const executionRate = trackedCount > 0 ? Math.round((executedCount / trackedCount) * 100) : 0;

  const statusMix = useMemo(() => {
    const buckets = history.reduce(
      (acc, item) => {
        const status = (item.status || '').toLowerCase();
        if (status === 'generated') acc.generated += 1;
        else if (status === 'executed') acc.executed += 1;
        else if (status.includes('fail') || item.error_message) acc.failed += 1;
        else acc.other += 1;
        return acc;
      },
      { generated: 0, executed: 0, failed: 0, other: 0 }
    );

    const total = Math.max(1, buckets.generated + buckets.executed + buckets.failed + buckets.other);
    return {
      ...buckets,
      total,
      generatedPct: Math.round((buckets.generated / total) * 100),
      executedPct: Math.round((buckets.executed / total) * 100),
      failedPct: Math.round((buckets.failed / total) * 100),
      otherPct: Math.round((buckets.other / total) * 100),
    };
  }, [history]);

  const topConnectionActivity = useMemo(() => {
    if (!history.length || !connections.length) {
      return [] as Array<{ id: string; name: string; count: number; pct: number }>;
    }
    const counts = new Map<string, number>();
    history.forEach((item) => {
      if (!item.connection_id) return;
      counts.set(item.connection_id, (counts.get(item.connection_id) || 0) + 1);
    });

    const items = Array.from(counts.entries())
      .map(([id, count]) => {
        const conn = connections.find((connection) => connection.id === id);
        return { id, name: conn?.name || 'Unknown connection', count };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    const max = Math.max(1, ...items.map((item) => item.count));
    return items.map((item) => ({ ...item, pct: Math.round((item.count / max) * 100) }));
  }, [history, connections]);

  const activityByDay = useMemo(() => {
    const days = 7;
    const formatter = new Intl.DateTimeFormat('en-US', { weekday: 'short' });
    const base = new Date();
    base.setHours(0, 0, 0, 0);

    const parseDateSafe = (raw?: string) => {
      if (!raw) return null;
      const first = new Date(raw);
      if (!Number.isNaN(first.getTime())) return first;
      const normalized = raw.includes(' ') ? raw.replace(' ', 'T') : raw;
      const second = new Date(normalized);
      if (!Number.isNaN(second.getTime())) return second;
      return null;
    };

    const slots = Array.from({ length: days }, (_, idx) => {
      const date = new Date(base);
      date.setDate(base.getDate() - (days - 1 - idx));
      const key = date.toISOString().slice(0, 10);
      return {
        key,
        label: formatter.format(date),
        generated: 0,
        executed: 0,
        total: 0,
      };
    });

    const byKey = new Map(slots.map((slot) => [slot.key, slot]));
    history.forEach((item) => {
      const created = parseDateSafe(item.created_at);
      if (!created) return;
      const key = created.toISOString().slice(0, 10);
      const slot = byKey.get(key);
      if (!slot) return;
      if (item.status === 'generated') slot.generated += 1;
      if (item.status === 'executed') slot.executed += 1;
      slot.total += 1;
    });

    const recentHasData = slots.some((slot) => slot.total > 0);
    if (!recentHasData && history.length > 0) {
      const grouped = new Map<string, { key: string; date: Date; label: string; generated: number; executed: number; total: number }>();
      history.forEach((item) => {
        const created = parseDateSafe(item.created_at);
        if (!created) return;
        const day = new Date(created);
        day.setHours(0, 0, 0, 0);
        const key = day.toISOString().slice(0, 10);
        const existing = grouped.get(key) || {
          key,
          date: day,
          label: formatter.format(day),
          generated: 0,
          executed: 0,
          total: 0,
        };
        if (item.status === 'generated') existing.generated += 1;
        if (item.status === 'executed') existing.executed += 1;
        existing.total += 1;
        grouped.set(key, existing);
      });

      const fallback = Array.from(grouped.values())
        .sort((a, b) => a.date.getTime() - b.date.getTime())
        .slice(-days);
      const maxFallback = Math.max(1, ...fallback.map((slot) => slot.total));
      return fallback.map((slot) => ({
        ...slot,
        pct: Math.round((slot.total / maxFallback) * 100),
      }));
    }

    const max = Math.max(1, ...slots.map((slot) => slot.total));
    return slots.map((slot) => ({ ...slot, pct: Math.round((slot.total / max) * 100) }));
  }, [history]);

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

  const sortedSessions = [...sessions].sort((a, b) => {
    const aTime = new Date(a.updated_at || a.created_at).getTime();
    const bTime = new Date(b.updated_at || b.created_at).getTime();
    return bTime - aTime;
  });
  const topFiveSessions = sortedSessions.slice(0, 5);
  const extraSessions = sortedSessions.slice(5);

  const dockItems = [
    {
      icon: <MessageSquare size={18} />,
      label: 'History',
      onClick: () => setActivePanel('history' as const),
      className: activePanel === 'history' ? 'ring-2 ring-ring' : '',
    },
    {
      icon: <Plus size={18} />,
      label: 'New Chat',
      onClick: () => router.push('/aurasql/query'),
    },
    {
      icon: <Database size={18} />,
      label: 'Connection',
      onClick: () => router.push('/aurasql/connections/new'),
    },
    {
      icon: <Layers size={18} />,
      label: 'Context',
      onClick: () => router.push('/aurasql/contexts/new'),
    },
    {
      icon: <Sparkles size={18} />,
      label: 'Actions',
      onClick: () => setActivePanel('actions' as const),
      className: activePanel === 'actions' ? 'ring-2 ring-ring' : '',
    },
    {
      icon: <Home size={18} />,
      label: 'Dashboard',
      onClick: () => router.push('/'),
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-35">
        <ShaderAnimation className="w-full h-full" speed={0.08} />
      </div>
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
              <div className="glass-panel sheen-border border-border/60 bg-accent-soft h-full rounded-xl p-3 flex gap-3">
                <div className="pt-2">
                  <VerticalMagnificationDock items={dockItems} panelWidth={66} baseItemSize={44} magnification={64} />
                </div>

                <div className="flex-1 rounded-2xl border border-border/60 bg-card/60 p-3 min-w-0 h-[560px]">
                  {activePanel === 'history' ? (
                    <div className="h-full flex flex-col">
                      <button
                        type="button"
                        onClick={() => setIsHistoryExpanded((prev) => !prev)}
                        className="w-full flex items-center justify-between rounded-xl border border-border/60 bg-background/60 px-3 py-2 text-sm font-semibold"
                      >
                        <span>AuraSQL History</span>
                        <ChevronDown className={`h-4 w-4 transition-transform ${isHistoryExpanded ? 'rotate-180' : ''}`} />
                      </button>

                      {isHistoryExpanded && (
                        <>
                          <ScrollArea className="flex-1 mt-3 pr-1">
                            {loading ? (
                              <div className="space-y-3">
                                {[1,2,3,4].map(i => (
                                  <div key={i} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                                    <Skeleton className="h-4 w-3/4 mb-2" />
                                    <Skeleton className="h-3 w-1/2" />
                                  </div>
                                ))}
                              </div>
                            ) : topFiveSessions.length === 0 ? (
                              <p className="text-sm text-muted-foreground">No history yet.</p>
                            ) : (
                              <div className="space-y-2">
                                {topFiveSessions.map((session) => (
                                  <button
                                    key={session.id}
                                    type="button"
                                    onClick={() => router.push(`/aurasql/query?session=${session.id}`)}
                                    className="w-full text-left rounded-xl border border-border/60 bg-card/60 px-3 py-2 hover:border-foreground/20 hover:bg-card/80 transition-all"
                                  >
                                    <p className="text-sm font-semibold text-foreground line-clamp-2">
                                      {session.title || 'AuraSQL chat'}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Updated {session.updated_at || session.created_at}
                                    </p>
                                  </button>
                                ))}

                                {showAllHistory && extraSessions.map((session) => (
                                  <button
                                    key={session.id}
                                    type="button"
                                    onClick={() => router.push(`/aurasql/query?session=${session.id}`)}
                                    className="w-full text-left rounded-xl border border-border/60 bg-card/60 px-3 py-2 hover:border-foreground/20 hover:bg-card/80 transition-all"
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

                          <button
                            type="button"
                            className="mt-3 w-full rounded-xl border border-border/60 bg-background/60 px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
                            onClick={() => setShowAllHistory((prev) => !prev)}
                            disabled={extraSessions.length === 0}
                          >
                            {extraSessions.length === 0
                              ? 'All chats shown'
                              : showAllHistory
                                ? 'Show less'
                                : `Show more (${extraSessions.length})`}
                          </button>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="h-full flex flex-col gap-2">
                      <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Quick Actions</p>
                      <Button onClick={() => router.push('/aurasql/query')} className="justify-start">
                        <Plus className="h-4 w-4 mr-2" />
                        New Chat
                      </Button>
                      <Button variant="outline" onClick={() => router.push('/aurasql/connections/new')} className="justify-start">
                        <Database className="h-4 w-4 mr-2" />
                        New Connection
                      </Button>
                      <Button variant="outline" onClick={() => router.push('/aurasql/contexts/new')} className="justify-start">
                        <Layers className="h-4 w-4 mr-2" />
                        New Context
                      </Button>
                    </div>
                  )}
                </div>
              </div>
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

              <div className="grid gap-6 xl:grid-cols-3">
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft xl:col-span-1">
                  <CardHeader>
                    <CardTitle>Execution Funnel</CardTitle>
                    <CardDescription>From generated SQL to executed SQL.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center gap-4">
                      <div
                        className="relative h-24 w-24 rounded-full"
                        style={{
                          background: `conic-gradient(hsl(var(--chart-1)) 0 ${executionRate}%, hsl(var(--muted)) ${executionRate}% 100%)`,
                        }}
                      >
                        <div className="absolute inset-2 rounded-full bg-card/90 flex items-center justify-center">
                          <span className="text-lg font-black text-foreground">{executionRate}%</span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Generated</p>
                        <p className="text-2xl font-black text-foreground"><AnimatedCounter value={generatedCount} /></p>
                        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Executed</p>
                        <p className="text-2xl font-black text-foreground"><AnimatedCounter value={executedCount} /></p>
                      </div>
                    </div>
                    <div className="rounded-xl border border-border/60 bg-card/60 p-3">
                      <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                        <span>Executed out of tracked</span>
                        <span>{executedCount}/{trackedCount}</span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-border/70">
                        <div className="h-full rounded-full bg-[hsl(var(--chart-1))]" style={{ width: `${Math.max(3, executionRate)}%` }} />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft xl:col-span-1">
                  <CardHeader>
                    <CardTitle>Status Mix</CardTitle>
                    <CardDescription>Distribution across generation lifecycle states.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="rounded-xl border border-border/60 bg-card/60 p-3">
                      <div className="h-4 w-full overflow-hidden rounded-full bg-border/70 flex">
                        <div className="h-full bg-[hsl(var(--chart-2))]" style={{ width: `${statusMix.generatedPct}%` }} />
                        <div className="h-full bg-[hsl(var(--chart-1))]" style={{ width: `${statusMix.executedPct}%` }} />
                        <div className="h-full bg-[hsl(var(--chart-5))]" style={{ width: `${statusMix.failedPct}%` }} />
                        <div className="h-full bg-muted-foreground/40" style={{ width: `${statusMix.otherPct}%` }} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg border border-border/60 bg-card/60 px-3 py-2 text-muted-foreground">Generated <span className="float-right text-foreground font-semibold">{statusMix.generated}</span></div>
                      <div className="rounded-lg border border-border/60 bg-card/60 px-3 py-2 text-muted-foreground">Executed <span className="float-right text-foreground font-semibold">{statusMix.executed}</span></div>
                      <div className="rounded-lg border border-border/60 bg-card/60 px-3 py-2 text-muted-foreground">Failed <span className="float-right text-foreground font-semibold">{statusMix.failed}</span></div>
                      <div className="rounded-lg border border-border/60 bg-card/60 px-3 py-2 text-muted-foreground">Other <span className="float-right text-foreground font-semibold">{statusMix.other}</span></div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft xl:col-span-1">
                  <CardHeader>
                    <CardTitle>7-Day Activity</CardTitle>
                    <CardDescription>Daily query generation/execution volume trend.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-44 rounded-xl border border-border/60 bg-card/60 p-3 flex items-end gap-2">
                      {activityByDay.map((day) => (
                        <div key={day.key} className="flex-1 flex flex-col items-center gap-2">
                          <div className="w-full max-w-[24px] h-28 flex items-end">
                            <div className="w-full rounded-t-md bg-[hsl(var(--chart-3))]" style={{ height: `${Math.max(8, day.pct)}%` }} />
                          </div>
                          <span className="text-[10px] text-muted-foreground">{day.label}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 xl:grid-cols-2">
                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                  <CardHeader>
                    <CardTitle>Top Active Connections</CardTitle>
                    <CardDescription>Connections with highest query activity.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {topConnectionActivity.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No connection activity yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {topConnectionActivity.map((item) => (
                          <div key={item.id} className="rounded-xl border border-border/60 bg-card/60 px-3 py-2">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-foreground font-medium truncate max-w-[70%]">{item.name}</span>
                              <span className="text-muted-foreground">{item.count}</span>
                            </div>
                            <div className="h-2 w-full overflow-hidden rounded-full bg-border/70">
                              <div className="h-full rounded-full bg-[hsl(var(--chart-3))]" style={{ width: `${item.pct}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                  <CardHeader>
                    <CardTitle>Latest Generation Feed</CardTitle>
                    <CardDescription>Most recent generated SQL intents from user prompts.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {generatedHistory.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No activity yet.</p>
                    ) : (
                      generatedHistory.slice(0, 6).map((item) => (
                        <div key={item.id} className="flex items-start justify-between gap-3 rounded-xl border border-border/60 bg-card/60 px-3 py-2">
                          <div className="min-w-0">
                            <p className="text-sm text-foreground line-clamp-2">
                              {item.natural_language_query || item.generated_sql || 'SQL generation'}
                            </p>
                            <p className="text-[11px] text-muted-foreground mt-1">{new Date(item.created_at).toLocaleString()}</p>
                          </div>
                          <Badge variant="secondary" className="text-[9px] uppercase tracking-[0.14em] bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20">
                            generated
                          </Badge>
                        </div>
                      ))
                    )}
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
