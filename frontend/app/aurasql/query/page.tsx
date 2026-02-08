'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AuraSqlSidebar } from '@/components/aurasql/AuraSqlSidebar';
import { MessageInput } from '@/components/chat/MessageInput';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlExecuteResponse, AuraSqlSession } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import Prism from 'prismjs';
import 'prismjs/components/prism-sql';
import { format as formatSqlWithLib } from 'sql-formatter';
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  Database,
  Download,
  Layers,
  Loader2,
  PlayCircle,
  RefreshCw,
  Save,
  Table,
  Wand2,
  X,
} from 'lucide-react';

type AuraSqlChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  editedSql?: string;
  explanation?: string;
  sourceTables?: string[];
  confidenceScore?: number | null;
  confidenceLevel?: 'high' | 'medium' | 'low' | null;
  execution?: AuraSqlExecuteResponse | null;
  showRows?: number;
  showResults?: boolean;
};

const makeMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

const formatSql = (sql: string) => {
  try {
    return formatSqlWithLib(sql, { language: 'postgresql' });
  } catch {
    return sql;
  }
};

const highlightSql = (sql: string) => Prism.highlight(formatSql(sql), Prism.languages.sql, 'sql');

export default function AuraSqlQueryPage() {
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [sessions, setSessions] = useState<AuraSqlSession[]>([]);
  const [selectedConnection, setSelectedConnection] = useState('');
  const [selectedContext, setSelectedContext] = useState('');
  const [activeContextId, setActiveContextId] = useState('');
  const [tableList, setTableList] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());
  const [newTables, setNewTables] = useState<Set<string>>(new Set());
  const [tableFilter, setTableFilter] = useState('');
  const [showConnectionMenu, setShowConnectionMenu] = useState(false);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [showTablesMenu, setShowTablesMenu] = useState(false);
  const [sessionContextId, setSessionContextId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<AuraSqlChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [recsOpen, setRecsOpen] = useState(false);
  const [recsLocked, setRecsLocked] = useState(false);
  const [recsByContext, setRecsByContext] = useState<Record<string, string[]>>({});
  const [lastRecsContextId, setLastRecsContextId] = useState<string | null>(null);
  const [recsConfirmOpen, setRecsConfirmOpen] = useState(false);
  const [recsConfirmContextId, setRecsConfirmContextId] = useState<string | null>(null);
  const [recsConfirmPrevContextId, setRecsConfirmPrevContextId] = useState<string | null>(null);
  const [historyBanner, setHistoryBanner] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadingTables, setLoadingTables] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const connectionContexts = useMemo(
    () => contexts.filter((ctx) => ctx.connection_id === selectedConnection),
    [contexts, selectedConnection]
  );

  const selectedContextRecord = useMemo(
    () => connectionContexts.find((ctx) => ctx.id === selectedContext) || null,
    [connectionContexts, selectedContext]
  );

  const baselineTables = useMemo(
    () => new Set(selectedContextRecord?.table_names ?? []),
    [selectedContextRecord]
  );

  const filteredTables = useMemo(() => {
    const filter = tableFilter.trim().toLowerCase();
    if (!filter) return tableList;
    return tableList.filter((table) => table.toLowerCase().includes(filter));
  }, [tableFilter, tableList]);

  const displayTables = useMemo(
    () => (tableList.length > 0 ? tableList : Array.from(selectedTables)),
    [tableList, selectedTables]
  );

  const hasUnsavedChanges = useMemo(() => {
    if (!selectedContextRecord) return selectedTables.size > 0;
    const current = Array.from(selectedTables).sort();
    const baseline = [...selectedContextRecord.table_names].sort();
    if (current.length !== baseline.length) return true;
    return current.some((value, index) => value !== baseline[index]);
  }, [selectedContextRecord, selectedTables]);

  useEffect(() => {
    if (sessionContextId) {
      setActiveContextId(sessionContextId);
      return;
    }
    setActiveContextId(selectedContext);
  }, [selectedContext, sessionContextId]);

  useEffect(() => {
    if (activeContextId) {
      setHistoryBanner(null);
    }
  }, [activeContextId]);

  useEffect(() => {
    if (autoScrollEnabled) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [chatMessages, autoScrollEnabled]);

  useEffect(() => {
    if (!selectedContextRecord) {
      setSelectedTables(new Set());
      setNewTables(new Set());
      return;
    }
    setSelectedTables(new Set(selectedContextRecord.table_names));
    setNewTables(new Set());
  }, [selectedContextRecord?.id]);

  useEffect(() => {
    if (!isAuthenticated) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [connData, ctxData, sessionData] = await Promise.all([
          apiClient.listAuraSqlConnections(),
          apiClient.listAuraSqlContexts(),
          apiClient.listAuraSqlSessions(),
        ]);
        setConnections(connData);
        setContexts(ctxData);
        setSessions(sessionData);

        const connectionParam = params.get('connection');
        const contextParam = params.get('context');
        const sessionParam = params.get('session');

        if (contextParam) {
          const context = ctxData.find((ctx) => ctx.id === contextParam);
          if (context) {
            setSelectedContext(context.id);
            setSelectedConnection(context.connection_id);
          }
        } else if (connectionParam) {
          setSelectedConnection(connectionParam);
        } else if (connData.length > 0) {
          setSelectedConnection(connData[0].id);
        }

        if (sessionParam) {
          const session = sessionData.find((item) => item.id === sessionParam);
          if (session) {
            await loadSessionHistory(session, ctxData);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load AuraSQL data');
      } finally {
        setLoading(false);
      }
    };

    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const handleStartNewChat = () => {
    setSessionId(null);
    setChatMessages([]);
    setHistoryBanner(null);
    setRecommendations([]);
    setRecsOpen(false);
  };

  useEffect(() => {
    const sessionParam = params.get('session');
    if (!sessionParam && sessionId) {
      handleStartNewChat();
    }
  }, [params, sessionId]);

  const loadSessionHistory = async (session: AuraSqlSession, ctxData = contexts) => {
    setSessionId(session.id);
    if (session.context_id) {
      let context = ctxData.find((ctx) => ctx.id === session.context_id) || null;
      if (!context) {
        try {
          context = await apiClient.getAuraSqlContext(session.context_id);
          setContexts((prev) => [context!, ...prev]);
        } catch {
          context = null;
        }
      }
      if (context) {
        setSelectedConnection(context.connection_id);
        setSelectedContext(context.id);
        setSessionContextId(null);
        setHistoryBanner(null);
      } else {
        setHistoryBanner('Select a context to continue this chat.');
      }
    } else {
      setHistoryBanner('Select a context to continue this chat.');
    }

    try {
      const logs = await apiClient.getAuraSqlSessionHistory(session.id);
      const nextMessages: AuraSqlChatMessage[] = [];
      logs.forEach((log) => {
        if (log.natural_language_query) {
          nextMessages.push({
            id: makeMessageId(),
            role: 'user',
            content: log.natural_language_query,
          });
        }
        if (log.generated_sql && log.status === 'generated') {
          nextMessages.push({
            id: makeMessageId(),
            role: 'assistant',
            content: 'SQL generated.',
            sql: log.generated_sql,
            editedSql: log.generated_sql,
            sourceTables: log.source_tables ?? [],
            confidenceScore: log.confidence_score ?? null,
            confidenceLevel: log.confidence_level ?? null,
            execution: null,
            showRows: 10,
            showResults: false,
          });
        }
      });
      setChatMessages(nextMessages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat history');
    }
  };

  const handleFetchTables = async () => {
    if (!selectedConnection) return;
    setLoadingTables(true);
    setError(null);
    try {
      const tables = await apiClient.listAuraSqlTables(selectedConnection);
      setTableList(tables);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tables');
    } finally {
      setLoadingTables(false);
    }
  };

  useEffect(() => {
    if (!selectedConnection) {
      setTableList([]);
      return;
    }
    handleFetchTables();
  }, [selectedConnection]);

  const handleToggleTable = (table: string) => {
    setSelectedTables((prev) => {
      const next = new Set(prev);
      if (next.has(table)) {
        next.delete(table);
      } else {
        next.add(table);
      }
      setNewTables(new Set([...next].filter((name) => !baselineTables.has(name))));
      return next;
    });
  };

  const handleSelectNewTables = () => {
    if (newTables.size === 0) return;
    setSelectedTables((prev) => new Set([...prev, ...newTables]));
    setNewTables(new Set());
  };

  const handleUseSessionContext = async () => {
    if (!selectedConnection || selectedTables.size === 0) return;
    setSavingContext(true);
    setError(null);
    try {
      const payload = {
        connection_id: selectedConnection,
        name: 'Session context',
        table_names: Array.from(selectedTables),
        is_temporary: true,
      };
      const context = await apiClient.createAuraSqlContext(payload);
      setSessionContextId(context.id);
      setActiveContextId(context.id);
      setHistoryBanner(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply session context');
    } finally {
      setSavingContext(false);
    }
  };

  const handleSaveContext = async () => {
    if (!selectedConnection || selectedTables.size === 0) return;
    const name = window.prompt('Name this context', 'New context');
    if (!name) return;
    setSavingContext(true);
    setError(null);
    try {
      const context = await apiClient.createAuraSqlContext({
        connection_id: selectedConnection,
        name,
        table_names: Array.from(selectedTables),
      });
      setContexts((prev) => [context, ...prev]);
      setSelectedContext(context.id);
      setSessionContextId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save context');
    } finally {
      setSavingContext(false);
    }
  };

  const handleUpdateContext = async () => {
    if (!selectedContextRecord) return;
    setSavingContext(true);
    setError(null);
    try {
      const context = await apiClient.updateAuraSqlContext(selectedContextRecord.id, {
        table_names: Array.from(selectedTables),
      });
      setContexts((prev) => prev.map((item) => (item.id === context.id ? context : item)));
      setNewTables(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update context');
    } finally {
      setSavingContext(false);
    }
  };

  const runRecommendationsFetch = async (contextId: string) => {
    setLoadingContext(true);
    setError(null);
    try {
      const recs = await apiClient.getAuraSqlRecommendations(contextId);
      setRecommendations(recs);
      setRecsByContext((prev) => ({ ...prev, [contextId]: recs }));
      setLastRecsContextId(contextId);
      setRecsOpen(true);
      setRecsLocked(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate recommendations');
    } finally {
      setLoadingContext(false);
    }
  };

  const handleRecommendations = async () => {
    if (!activeContextId) return;
    const currentRecs = recsByContext[activeContextId];
    if (currentRecs && currentRecs.length > 0) {
      setRecommendations(currentRecs);
      setRecsOpen(true);
      setRecsLocked(true);
      setLastRecsContextId(activeContextId);
      return;
    }

    if (
      lastRecsContextId &&
      lastRecsContextId !== activeContextId &&
      recsByContext[lastRecsContextId]?.length
    ) {
      setRecsConfirmContextId(activeContextId);
      setRecsConfirmPrevContextId(lastRecsContextId);
      setRecsConfirmOpen(true);
      return;
    }

    await runRecommendationsFetch(activeContextId);
  };

  const handleSendMessage = async (text: string) => {
    if (!activeContextId) {
      setError('Select a context to generate SQL.');
      return;
    }
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage: AuraSqlChatMessage = {
      id: makeMessageId(),
      role: 'user',
      content: trimmed,
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setLoadingGenerate(true);
    setError(null);

    try {
      const response = await apiClient.generateAuraSqlQueryWithSession(
        activeContextId,
        trimmed,
        sessionId || undefined
      );

      if (!response.sql) {
        setChatMessages((prev) => [
          ...prev,
          {
            id: makeMessageId(),
            role: 'assistant',
            content: response.explanation || 'Could not generate SQL with the selected context.',
            confidenceScore: response.confidence_score ?? 0,
            confidenceLevel: response.confidence_level ?? 'low',
          },
        ]);
        return;
      }

      const assistantMessage: AuraSqlChatMessage = {
        id: makeMessageId(),
        role: 'assistant',
        content: 'SQL generated.',
        sql: response.sql,
        editedSql: response.sql,
        explanation: response.explanation,
        sourceTables: response.source_tables,
        confidenceScore: response.confidence_score ?? null,
        confidenceLevel: response.confidence_level ?? null,
        execution: null,
        showRows: 10,
        showResults: false,
      };
      setChatMessages((prev) => [...prev, assistantMessage]);

      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        const updatedSessions = await apiClient.listAuraSqlSessions();
        setSessions(updatedSessions);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate SQL');
    } finally {
      setLoadingGenerate(false);
    }
  };

  const handleExecuteMessage = async (messageId: string) => {
    if (!selectedConnection) return;
    const message = chatMessages.find((item) => item.id === messageId);
    const sql = message?.editedSql || message?.sql;
    if (!sql) return;

    setLoadingExecute(true);
    setError(null);
    try {
      const result = await apiClient.executeAuraSqlWithSession(
        selectedConnection,
        sql,
        sessionId || undefined
      );
      setChatMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, execution: result, showRows: msg.showRows ?? 10, showResults: true }
            : msg
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute SQL');
    } finally {
      setLoadingExecute(false);
    }
  };

  const handleToggleResults = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, showResults: !msg.showResults } : msg
      )
    );
  };

  const handleShowMoreRows = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, showRows: (msg.showRows || 10) + 10 }
          : msg
      )
    );
  };

  const handleCopySql = async (sql: string) => {
    try {
      await navigator.clipboard.writeText(sql);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to copy SQL');
    }
  };

  const handleDownloadSql = (sql: string) => {
    const blob = new Blob([sql], { type: 'text/sql' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'query.sql';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

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
              currentHistoryId={sessionId}
              sessions={sessions}
              onSelectSession={(session) => loadSessionHistory(session)}
              onNewChat={handleStartNewChat}
            />
          </div>
        </aside>

        <main className="flex flex-1 flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-hidden p-3 md:p-6">
            <div className="glass-panel h-full rounded-3xl p-4 md:p-6 overflow-hidden flex flex-col">
              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full pr-2">
                  <div className="space-y-4 pb-4">
                    {chatMessages.length === 0 && !loadingGenerate && (
                      <div className="rounded-2xl border border-dashed border-border/70 bg-card/40 p-6 text-sm text-muted-foreground">
                        Start by asking a question about your schema. The assistant will generate SQL you can refine and execute.
                      </div>
                    )}

                    {chatMessages.map((message) => (
                      <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] space-y-3 ${message.role === 'user' ? 'text-right' : ''}`}>
                          <div
                            className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${
                              message.role === 'user'
                                ? 'bg-foreground text-background'
                                : 'bg-card/70 border border-border/60 text-foreground'
                            }`}
                          >
                            {message.content}
                          </div>

                          {message.role === 'assistant' && message.sql && (
                            <div className="rounded-2xl border border-border/60 bg-muted/40 p-4 space-y-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">SQL Canvas</p>
                                  {message.confidenceScore !== null && message.confidenceScore !== undefined && (
                                    <Badge
                                      variant="secondary"
                                      className={`text-[10px] uppercase tracking-[0.2em] ${
                                        message.confidenceLevel === 'high'
                                          ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-200'
                                          : message.confidenceLevel === 'medium'
                                          ? 'bg-amber-500/15 text-amber-800 dark:text-amber-200'
                                          : 'bg-rose-500/15 text-rose-800 dark:text-rose-200'
                                      }`}
                                    >
                                      {message.confidenceLevel || 'low'} {Math.round(message.confidenceScore)}%
                                    </Badge>
                                  )}
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  <Button size="sm" variant="ghost" onClick={() => handleCopySql(message.editedSql || message.sql)}>
                                    <Copy className="h-4 w-4 mr-1" />
                                    Copy
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleDownloadSql(message.editedSql || message.sql)}>
                                    <Download className="h-4 w-4 mr-1" />
                                    Download
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => handleExecuteMessage(message.id)}
                                    disabled={loadingExecute || !(message.editedSql || message.sql)}
                                  >
                                    {loadingExecute ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <PlayCircle className="h-4 w-4 mr-1" />}
                                    Execute
                                  </Button>
                                </div>
                              </div>

                              <div className="rounded-xl border border-border/60 bg-card/60 p-3">
                                <pre
                                  className="prism-sql text-xs font-mono whitespace-pre-wrap leading-relaxed outline-none min-h-[220px]"
                                  contentEditable
                                  suppressContentEditableWarning
                                  onInput={(event) => {
                                    const nextValue = event.currentTarget.textContent || '';
                                    setChatMessages((prev) =>
                                      prev.map((msg) =>
                                        msg.id === message.id ? { ...msg, editedSql: nextValue } : msg
                                      )
                                    );
                                  }}
                                  dangerouslySetInnerHTML={{
                                    __html: highlightSql(formatSql(message.editedSql ?? message.sql)),
                                  }}
                                />
                              </div>

                              {message.sourceTables && message.sourceTables.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                  {message.sourceTables.map((table) => (
                                    <Badge key={table} variant="outline">
                                      {table}
                                    </Badge>
                                  ))}
                                </div>
                              )}

                              {message.execution && (
                                <div className="space-y-3">
                                  <Button size="sm" variant="ghost" onClick={() => handleToggleResults(message.id)}>
                                    {message.showResults ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                                    {message.showResults ? 'Hide results' : 'Show results'}
                                  </Button>

                                  {message.showResults && (
                                    <>
                                      {message.execution.rows.length === 0 ? (
                                        <p className="text-sm text-muted-foreground">No rows returned.</p>
                                      ) : (
                                        <div className="overflow-x-auto rounded-xl border border-border/60">
                                          <table className="min-w-full divide-y divide-border">
                                            <thead className="bg-muted/60">
                                              <tr>
                                                {message.execution.columns.map((column) => (
                                                  <th
                                                    key={column}
                                                    className="px-4 py-2 text-left text-xs font-semibold text-muted-foreground"
                                                  >
                                                    {column}
                                                  </th>
                                                ))}
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border">
                                              {message.execution.rows
                                                .slice(0, message.showRows || 10)
                                                .map((row, index) => (
                                                  <tr key={index}>
                                                    {message.execution.columns.map((column) => (
                                                      <td key={column} className="px-4 py-2 text-sm text-foreground">
                                                        {String(row[column] ?? '')}
                                                      </td>
                                                    ))}
                                                  </tr>
                                                ))}
                                            </tbody>
                                          </table>
                                        </div>
                                      )}
                                      {message.execution.rows.length > (message.showRows || 10) && (
                                        <Button variant="outline" size="sm" onClick={() => handleShowMoreRows(message.id)}>
                                          Show more
                                        </Button>
                                      )}
                                    </>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {loadingGenerate && (
                      <div className="rounded-2xl border border-dashed border-border/60 bg-card/40 px-4 py-3 text-sm text-muted-foreground">
                        Generating SQL...
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </div>
                </ScrollArea>
              </div>

              <div className="sticky bottom-0 z-20">
                <div className="bg-gradient-to-t from-background/95 via-background/80 to-transparent px-2 pt-6 pb-4">
                  <div className="mx-auto w-full max-w-4xl glass-panel rounded-3xl p-4 space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <div className="relative">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => setShowConnectionMenu((prev) => !prev)}
                            disabled={loading || connections.length === 0}
                            aria-label="Select connection"
                            title={
                              connections.find((conn) => conn.id === selectedConnection)?.name ||
                              'Select connection'
                            }
                          >
                            <Database className="h-4 w-4" />
                            <ChevronDown className="h-3 w-3 ml-1" />
                          </Button>
                          {showConnectionMenu && (
                            <div className="absolute left-0 bottom-full z-30 mb-2 w-72 rounded-xl border border-border/60 bg-card/95 p-2 shadow-lg">
                              <div className="max-h-64 overflow-y-auto">
                                {connections.length === 0 ? (
                                  <p className="px-3 py-2 text-sm text-muted-foreground">No connections</p>
                                ) : (
                                  connections.map((conn) => (
                                    <button
                                      key={conn.id}
                                      type="button"
                                      onClick={() => {
                                        setSelectedConnection(conn.id);
                                        setShowConnectionMenu(false);
                                      }}
                                      className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                                        conn.id === selectedConnection
                                          ? 'bg-foreground/10 text-foreground'
                                          : 'hover:bg-muted/60'
                                      }`}
                                    >
                                      {conn.name} • {conn.database} • {conn.schema_name || 'default'}
                                    </button>
                                  ))
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="relative">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => setShowContextMenu((prev) => !prev)}
                            disabled={loading || connectionContexts.length === 0}
                            aria-label="Select context"
                            title={selectedContextRecord?.name || 'Select context'}
                          >
                            <Layers className="h-4 w-4" />
                            <ChevronDown className="h-3 w-3 ml-1" />
                          </Button>
                          {showContextMenu && (
                            <div className="absolute left-0 bottom-full z-30 mb-2 w-72 rounded-xl border border-border/60 bg-card/95 p-2 shadow-lg">
                              <div className="max-h-64 overflow-y-auto">
                                {connectionContexts.length === 0 ? (
                                  <p className="px-3 py-2 text-sm text-muted-foreground">No contexts</p>
                                ) : (
                                  connectionContexts.map((ctx) => (
                                    <button
                                      key={ctx.id}
                                      type="button"
                                      onClick={() => {
                                        setSelectedContext(ctx.id);
                                        setShowContextMenu(false);
                                      }}
                                      className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                                        ctx.id === selectedContext
                                          ? 'bg-foreground/10 text-foreground'
                                          : 'hover:bg-muted/60'
                                      }`}
                                    >
                                      {ctx.name} • {ctx.table_names.join(', ')}
                                    </button>
                                  ))
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={handleRecommendations}
                          disabled={loadingContext || !activeContextId}
                          aria-label="Recommendations"
                          title={recsByContext[activeContextId]?.length ? 'Recommendations' : 'Generate recommendations'}
                        >
                          {loadingContext ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                        </Button>

                        <div className="relative">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => {
                              setShowTablesMenu((prev) => {
                                const next = !prev;
                                if (next && tableList.length === 0) {
                                  handleFetchTables();
                                }
                                return next;
                              });
                            }}
                            disabled={!selectedConnection}
                            aria-label="Tables"
                            title="Tables"
                          >
                            <Table className="h-4 w-4" />
                            <ChevronDown className="h-3 w-3 ml-1" />
                          </Button>
                          {showTablesMenu && (
                            <div className="absolute left-0 bottom-full z-30 mb-2 w-[520px] rounded-xl border border-border/60 bg-card/95 p-3 shadow-lg">
                              <div className="flex items-center gap-2 mb-3">
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={handleFetchTables}
                                  disabled={loadingTables || !selectedConnection}
                                  aria-label="Refresh tables"
                                  title="Refresh tables"
                                >
                                  <RefreshCw className={`h-4 w-4 ${loadingTables ? 'animate-spin' : ''}`} />
                                </Button>
                                <input
                                  value={tableFilter}
                                  onChange={(event) => setTableFilter(event.target.value)}
                                  placeholder="Filter tables..."
                                  className="w-full rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                                />
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={handleUseSessionContext}
                                  disabled={selectedTables.size === 0 || savingContext}
                                  aria-label="Apply to session"
                                  title="Apply to session"
                                >
                                  {savingContext ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                                </Button>
                                {selectedContextRecord ? (
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    onClick={handleUpdateContext}
                                    disabled={!hasUnsavedChanges || savingContext}
                                    aria-label="Update saved context"
                                    title="Update saved context"
                                  >
                                    {savingContext ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                                  </Button>
                                ) : (
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    onClick={handleSaveContext}
                                    disabled={selectedTables.size === 0 || savingContext}
                                    aria-label="Save context"
                                    title="Save context"
                                  >
                                    {savingContext ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                                  </Button>
                                )}
                              </div>
                              {filteredTables.length === 0 ? (
                                <p className="text-xs text-muted-foreground">No tables found.</p>
                              ) : (
                                <div className="flex flex-wrap gap-2 max-h-[220px] overflow-y-auto pr-2">
                                  {filteredTables.map((table) => {
                                    const isSelected = selectedTables.has(table);
                                    const isNew = newTables.has(table);
                                    return (
                                      <Badge
                                        key={table}
                                        variant={isSelected ? 'default' : 'outline'}
                                        className={`cursor-pointer transition-all ${
                                          isSelected ? 'bg-foreground text-background' : 'bg-card/70 text-muted-foreground'
                                        } ${isNew ? 'ring-1 ring-amber-400/70' : ''}`}
                                        onClick={() => handleToggleTable(table)}
                                      >
                                        {table}
                                        {isSelected && <X className="ml-1 h-3 w-3" />}
                                      </Badge>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                    </div>

                    {historyBanner && <p className="text-xs text-amber-500">{historyBanner}</p>}

                    <MessageInput
                      onSend={handleSendMessage}
                      disabled={loadingGenerate || !activeContextId || (hasUnsavedChanges && !sessionContextId)}
                      value={inputValue}
                      onChange={setInputValue}
                      placeholder="Ask a question about your schema..."
                    />
                  </div>
                </div>
              </div>

              {error && <p className="text-sm text-red-500 mt-3">{error}</p>}
            </div>
          </div>
        </main>
      </div>

      {recsOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-background/50 backdrop-blur-sm">
          <div className="w-full max-w-md h-full bg-card/95 border-l border-border/70 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">Recommendations</p>
                <p className="text-xs text-muted-foreground">Pick a question to drop into chat.</p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setRecsOpen(false)}>
                Close
              </Button>
            </div>

            {loadingContext ? (
              <p className="text-sm text-muted-foreground">Generating recommendations...</p>
            ) : recommendations.length === 0 ? (
              <p className="text-sm text-muted-foreground">No recommendations yet.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {recommendations.map((rec) => (
                  <Badge
                    key={rec}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => {
                      setInputValue(rec);
                      setRecsOpen(false);
                      setRecsLocked(true);
                    }}
                  >
                    {rec}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {recsConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-border/60 bg-card/95 p-5 space-y-4">
            <div className="space-y-1">
              <p className="text-sm font-semibold">Context changed</p>
              <p className="text-xs text-muted-foreground">
                Use previous recommendations or regenerate for the current context.
              </p>
            </div>
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  if (recsConfirmPrevContextId && recsByContext[recsConfirmPrevContextId]) {
                    setRecommendations(recsByContext[recsConfirmPrevContextId]);
                    setRecsOpen(true);
                    setRecsLocked(true);
                  }
                  setRecsConfirmOpen(false);
                }}
              >
                Use previous
              </Button>
              <Button
                onClick={async () => {
                  if (recsConfirmContextId) {
                    await runRecommendationsFetch(recsConfirmContextId);
                  }
                  setRecsConfirmOpen(false);
                }}
              >
                Regenerate
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}