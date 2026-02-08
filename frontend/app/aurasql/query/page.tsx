'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { AuraSqlSidebar } from '@/components/aurasql/AuraSqlSidebar';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlHistoryItem, AuraSqlExecuteResponse, AuraSqlQueryResponse } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { Loader2, Wand2, PlayCircle, Plus, Info, Trash2 } from 'lucide-react';

export default function AuraSqlQueryPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>('');
  const [selectedContext, setSelectedContext] = useState<string>('');
  const [activeContextId, setActiveContextId] = useState<string>('');
  const [tableList, setTableList] = useState<string[]>([]);
  const [newTables, setNewTables] = useState<Set<string>>(new Set());
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());
  const [sessionContextId, setSessionContextId] = useState<string | null>(null);
  const [queryText, setQueryText] = useState('');
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [generated, setGenerated] = useState<AuraSqlQueryResponse | null>(null);
  const [generatedSql, setGeneratedSql] = useState('');
  const [execution, setExecution] = useState<AuraSqlExecuteResponse | null>(null);
  const [resultLimit, setResultLimit] = useState(5);
  const [historyItem, setHistoryItem] = useState<AuraSqlHistoryItem | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingTables, setLoadingTables] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [connData, ctxData] = await Promise.all([
          apiClient.listAuraSqlConnections(),
          apiClient.listAuraSqlContexts(),
        ]);
        setConnections(connData);
        setContexts(ctxData);

        const connectionParam = params.get('connection');
        const contextParam = params.get('context');

        if (contextParam) {
          const context = ctxData.find((ctx) => ctx.id === contextParam);
          if (context) {
            setSelectedContext(context.id);
            setSelectedConnection(context.connection_id);
            setActiveContextId(context.id);
          }
        } else if (connectionParam) {
          setSelectedConnection(connectionParam);
        } else if (connData.length > 0) {
          setSelectedConnection(connData[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load AuraSQL data');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [isAuthenticated, params]);

  useEffect(() => {
    if (!selectedConnection) return;
    setSelectedContext('');
    setActiveContextId('');
    setSessionContextId(null);
    setSelectedTables(new Set());
    setTableList([]);
    setNewTables(new Set());
  }, [selectedConnection]);

  useEffect(() => {
    if (!selectedContext) return;
    const loadContext = async () => {
      setLoadingContext(true);
      try {
        const context = await apiClient.getAuraSqlContext(selectedContext);
        setSelectedTables(new Set(context.table_names));
        setSessionContextId(null);
        setActiveContextId(context.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load context');
      } finally {
        setLoadingContext(false);
      }
    };

    loadContext();
  }, [selectedContext]);

  const connectionContexts = useMemo(
    () => contexts.filter((ctx) => ctx.connection_id === selectedConnection),
    [contexts, selectedConnection]
  );

  const selectedContextTables = useMemo(() => {
    const selected = contexts.find((ctx) => ctx.id === selectedContext);
    return new Set(selected?.table_names || []);
  }, [contexts, selectedContext]);

  const selectedContextRecord = useMemo(
    () => contexts.find((ctx) => ctx.id === selectedContext),
    [contexts, selectedContext]
  );

  const getDefaultContextName = () => {
    const base = 'Default context';
    const existing = new Set(connectionContexts.map((ctx) => ctx.name));
    if (!existing.has(base)) return base;
    let counter = 2;
    while (existing.has(`${base} ${counter}`)) {
      counter += 1;
    }
    return `${base} ${counter}`;
  };

  const hasUnsavedChanges = useMemo(() => {
    const selected = Array.from(selectedTables).sort();
    const original = Array.from(selectedContextTables).sort();
    if (selected.length !== original.length) return true;
    return selected.some((value, index) => value !== original[index]);
  }, [selectedTables, selectedContextTables]);

  if (!isAuthenticated) return <AuthPage />;

  const handleFetchTables = async () => {
    if (!selectedConnection) return;
    setLoadingTables(true);
    setError(null);
    try {
      const previous = new Set(tableList);
      const tables = await apiClient.listAuraSqlTables(selectedConnection);
      const newlyAdded = tables.filter((table) => !previous.has(table));
      setTableList(tables);
      setNewTables(new Set(newlyAdded));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tables');
    } finally {
      setLoadingTables(false);
    }
  };

  const handleToggleTable = (table: string) => {
    setSelectedTables((prev) => {
      const next = new Set(prev);
      if (next.has(table)) {
        next.delete(table);
      } else {
        next.add(table);
      }
      return next;
    });
  };

  const handleUseSessionContext = async () => {
    if (!selectedConnection || selectedTables.size === 0) return;
    setSavingContext(true);
    setError(null);
    try {
      if (sessionContextId) {
        const context = await apiClient.updateAuraSqlContext(sessionContextId, {
          table_names: Array.from(selectedTables),
          is_temporary: true,
        });
        setActiveContextId(context.id);
      } else {
        const context = await apiClient.createAuraSqlContext({
          connection_id: selectedConnection,
          name: 'Session context',
          table_names: Array.from(selectedTables),
          is_temporary: true,
        });
        setSessionContextId(context.id);
        setActiveContextId(context.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session context');
    } finally {
      setSavingContext(false);
    }
  };

  const handleSaveContext = async () => {
    if (!selectedConnection || selectedTables.size === 0) return;
    setSavingContext(true);
    setError(null);
    try {
      const context = await apiClient.createAuraSqlContext({
        connection_id: selectedConnection,
        name: getDefaultContextName(),
        table_names: Array.from(selectedTables),
        is_temporary: false,
      });
      setContexts((prev) => [context, ...prev]);
      setSelectedContext(context.id);
      setActiveContextId(context.id);
      setSessionContextId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save context');
    } finally {
      setSavingContext(false);
    }
  };

  const handleUpdateContext = async () => {
    if (!selectedContextRecord || selectedTables.size === 0) return;
    setSavingContext(true);
    setError(null);
    try {
      const context = await apiClient.updateAuraSqlContext(selectedContext, {
        table_names: Array.from(selectedTables),
        is_temporary: false,
      });
      setContexts((prev) => prev.map((ctx) => (ctx.id === context.id ? context : ctx)));
      setActiveContextId(context.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update context');
    } finally {
      setSavingContext(false);
    }
  };

  const handleDeleteContext = async () => {
    if (!selectedContext) return;
    const confirmed = window.confirm('Delete this context? This cannot be undone.');
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlContext(selectedContext);
      setContexts((prev) => prev.filter((ctx) => ctx.id !== selectedContext));
      setSelectedContext('');
      setActiveContextId('');
      setSelectedTables(new Set());
      setNewTables(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete context');
    }
  };

  const handleDeleteConnection = async () => {
    if (!selectedConnection) return;
    const confirmed = window.confirm('Delete this connection? This will remove its saved contexts.');
    if (!confirmed) return;
    try {
      await apiClient.deleteAuraSqlConnection(selectedConnection);
      setConnections((prev) => prev.filter((conn) => conn.id !== selectedConnection));
      setContexts((prev) => prev.filter((ctx) => ctx.connection_id !== selectedConnection));
      setSelectedConnection('');
      setSelectedContext('');
      setActiveContextId('');
      setSelectedTables(new Set());
      setTableList([]);
      setNewTables(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete connection');
    }
  };

  const handleSelectNewTables = () => {
    if (newTables.size === 0) return;
    setSelectedTables((prev) => {
      const next = new Set(prev);
      newTables.forEach((table) => next.add(table));
      return next;
    });
  };

  const handleRecommendations = async () => {
    if (!activeContextId) return;
    setLoadingContext(true);
    try {
      const recs = await apiClient.getAuraSqlRecommendations(activeContextId);
      setRecommendations(recs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setLoadingContext(false);
    }
  };

  const handleGenerate = async () => {
    if (!activeContextId || !queryText.trim()) return;
    setLoadingGenerate(true);
    setGenerated(null);
    setGeneratedSql('');
    setExecution(null);
    setResultLimit(5);
    try {
      const result = await apiClient.generateAuraSqlQuery(activeContextId, queryText.trim());
      setGenerated(result);
      setGeneratedSql(result.sql);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate SQL');
    } finally {
      setLoadingGenerate(false);
    }
  };

  const handleExecute = async () => {
    const connection = connections.find((conn) => conn.id === selectedConnection);
    if (!generated || !connection || !generatedSql.trim()) return;
    setLoadingExecute(true);
    setExecution(null);
    try {
      const result = await apiClient.executeAuraSql(connection.id, generatedSql.trim());
      setExecution(result);
      setResultLimit(5);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute SQL');
    } finally {
      setLoadingExecute(false);
    }
  };

  return (
    <div className="relative h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header
        showSidebarToggle
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      <div className="relative z-10 flex h-[calc(100vh-4rem)] overflow-hidden">
        <aside
          className={`hidden md:block transition-all duration-300 ease-out ${
            isSidebarOpen ? 'w-72 opacity-100' : 'w-0 opacity-0'
          }`}
        >
          <div
            className={`h-full transition-all duration-300 ${
              isSidebarOpen ? 'translate-x-0' : '-translate-x-6 pointer-events-none'
            }`}
          >
            <AuraSqlSidebar
              currentHistoryId={historyItem?.id}
              onSelectHistory={(item) => {
                setHistoryItem(item);
                if (item.natural_language_query) {
                  setQueryText(item.natural_language_query);
                }
                if (item.generated_sql) {
                  setGenerated({
                    sql: item.generated_sql,
                    explanation: 'Loaded from history.',
                    source_tables: [],
                  });
                }
              }}
            />
          </div>
        </aside>

        <main className="flex flex-1 flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-hidden p-3 md:p-6">
            <div className="glass-panel h-full rounded-3xl p-4 md:p-6 overflow-auto">
              <div className="grid gap-6 lg:grid-cols-2">
                <Card className="border-border/60">
                  <div className="p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h2 className="text-lg font-semibold">Connection & Context</h2>
                      <Button variant="ghost" size="sm" onClick={() => router.push('/aurasql')}>Back to AuraSQL</Button>
                    </div>

                    {loading ? (
                      <p className="text-sm text-muted-foreground">Loading connections...</p>
                    ) : connections.length === 0 ? (
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">No connections found.</p>
                        <Button onClick={() => router.push('/aurasql/connections/new')}>
                          <Plus className="h-4 w-4 mr-2" />
                          Create connection
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="space-y-2">
                          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Connection</p>
                          <select
                            value={selectedConnection}
                            onChange={(event) => setSelectedConnection(event.target.value)}
                            className="w-full rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                          >
                            {connections.map((conn) => (
                              <option key={conn.id} value={conn.id}>
                                {conn.name} • {conn.database} • {conn.schema_name || 'default'}
                              </option>
                            ))}
                          </select>
                          {selectedConnection && (
                            <div className="flex flex-wrap gap-2">
                              <Button size="sm" variant="ghost" onClick={handleDeleteConnection}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Connection
                              </Button>
                            </div>
                          )}
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Saved Contexts</p>
                          {connectionContexts.length === 0 ? (
                            <p className="text-sm text-muted-foreground">No contexts yet.</p>
                          ) : (
                            <select
                              value={selectedContext}
                              onChange={(event) => setSelectedContext(event.target.value)}
                              className="w-full rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                            >
                              <option value="">Select a context</option>
                              {connectionContexts.map((ctx) => (
                                <option key={ctx.id} value={ctx.id}>
                                  {ctx.name} • {ctx.table_names.join(', ')}
                                </option>
                              ))}
                            </select>
                          )}
                          {selectedContext && (
                            <div className="flex flex-wrap gap-2">
                              <Button size="sm" variant="ghost" onClick={handleDeleteContext}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Context
                              </Button>
                            </div>
                          )}
                        </div>

                        <div className="rounded-2xl border border-border/60 bg-card/60 p-3 space-y-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-medium">Table Contexts</p>
                              <p className="text-xs text-muted-foreground">Refresh to pull newly added tables.</p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <Button size="sm" variant="outline" onClick={handleFetchTables} disabled={loadingTables}>
                                {loadingTables ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Refresh tables'}
                              </Button>
                              <Button size="sm" variant="ghost" onClick={handleSelectNewTables} disabled={newTables.size === 0}>
                                Add new tables
                              </Button>
                            </div>
                          </div>

                          {tableList.length === 0 ? (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Info className="h-3.5 w-3.5" />
                              Fetch tables to select new context.
                            </div>
                          ) : (
                            <div className="grid gap-2 md:grid-cols-2">
                              {tableList.map((table) => {
                                const isSelected = selectedTables.has(table);
                                const isSelectedContext = selectedContextTables.has(table);
                                const isNew = newTables.has(table);
                                return (
                                  <label
                                    key={table}
                                    className="flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-sm cursor-pointer"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={isSelected}
                                      onChange={() => handleToggleTable(table)}
                                      className="h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/40"
                                    />
                                    <span className={isSelectedContext ? 'font-semibold' : ''}>{table}</span>
                                    {isNew && <Badge variant="outline">New</Badge>}
                                  </label>
                                );
                              })}
                            </div>
                          )}

                          {selectedTables.size > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {Array.from(selectedTables).map((table) => (
                                <Badge
                                  key={table}
                                  variant="secondary"
                                  className="cursor-pointer"
                                  onClick={() => handleToggleTable(table)}
                                >
                                  {table}
                                </Badge>
                              ))}
                            </div>
                          )}

                          <div className="flex flex-wrap gap-2">
                            <Button
                              variant="outline"
                              onClick={handleUseSessionContext}
                              disabled={selectedTables.size === 0 || savingContext}
                            >
                              {savingContext ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                              Use selection for session
                            </Button>
                            <Button
                              onClick={handleSaveContext}
                              disabled={selectedTables.size === 0 || savingContext || !!selectedContextRecord}
                            >
                              Save as default context
                            </Button>
                            <Button
                              variant="ghost"
                              onClick={handleUpdateContext}
                              disabled={!selectedContextRecord || !hasUnsavedChanges || savingContext}
                            >
                              Update saved context
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>

                <Card className="border-border/60">
                  <div className="p-4 space-y-4">
                    <h2 className="text-lg font-semibold">Prompt</h2>
                    <Textarea
                      value={queryText}
                      onChange={(e) => setQueryText(e.target.value)}
                      placeholder="Ask about your schema..."
                      className="min-h-[140px]"
                    />
                    <div className="flex flex-wrap gap-2">
                      <Button
                        onClick={handleGenerate}
                        disabled={
                          loadingGenerate ||
                          !queryText.trim() ||
                          !activeContextId ||
                          (hasUnsavedChanges && !sessionContextId)
                        }
                      >
                        {loadingGenerate ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Wand2 className="h-4 w-4 mr-2" />}
                        Generate SQL
                      </Button>
                      <Button variant="outline" onClick={handleRecommendations} disabled={loadingContext || !activeContextId}>
                        {loadingContext ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : 'Get recommendations'}
                      </Button>
                    </div>
                    {recommendations.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {recommendations.map((rec) => (
                          <Badge key={rec} variant="secondary" className="cursor-pointer" onClick={() => setQueryText(rec)}>
                            {rec}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {hasUnsavedChanges && !sessionContextId && selectedTables.size > 0 && (
                      <p className="text-xs text-muted-foreground">
                        Apply the selection to this session or update the saved context before generating.
                      </p>
                    )}
                  </div>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-2 mt-6">
                <Card className="border-border/60">
                  <div className="p-4 space-y-3">
                    <h2 className="text-lg font-semibold">Generated SQL</h2>
                    {generated ? (
                      <>
                        <Textarea
                          value={generatedSql}
                          onChange={(e) => setGeneratedSql(e.target.value)}
                          className="min-h-[140px] font-mono"
                        />
                        <div className="text-sm text-muted-foreground">{generated.explanation}</div>
                        {generated.source_tables.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {generated.source_tables.map((table) => (
                              <Badge key={table} variant="outline">
                                {table}
                              </Badge>
                            ))}
                          </div>
                        )}
                        <Button onClick={handleExecute} disabled={loadingExecute || !generatedSql.trim()}>
                          {loadingExecute ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <PlayCircle className="h-4 w-4 mr-2" />}
                          Execute SQL
                        </Button>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">Generate a SQL query to see results here.</p>
                    )}
                  </div>
                </Card>

                <Card className="border-border/60">
                  <div className="p-4 space-y-3">
                    <h2 className="text-lg font-semibold">Results</h2>
                    {execution ? (
                      execution.rows.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No rows returned.</p>
                      ) : (
                        <div className="overflow-x-auto rounded-xl border border-border/60">
                          <table className="min-w-full divide-y divide-border">
                            <thead className="bg-muted/60">
                              <tr>
                                {execution.columns.map((column) => (
                                  <th key={column} className="px-4 py-2 text-left text-xs font-semibold text-muted-foreground">
                                    {column}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                              {execution.rows.slice(0, resultLimit).map((row, index) => (
                                <tr key={index}>
                                  {execution.columns.map((column) => (
                                    <td key={column} className="px-4 py-2 text-sm text-foreground">
                                      {String(row[column] ?? '')}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )
                    ) : (
                      <p className="text-sm text-muted-foreground">Run a query to see results.</p>
                    )}
                    {execution && execution.rows.length > resultLimit && (
                      <Button variant="outline" size="sm" onClick={() => setResultLimit((prev) => prev + 5)}>
                        Show more
                      </Button>
                    )}
                  </div>
                </Card>
              </div>

              {error && <p className="text-sm text-red-500 mt-4">{error}</p>}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
