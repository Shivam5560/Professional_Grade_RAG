'use client';

export const dynamic = 'force-dynamic';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AuraSqlSidebar } from '@/components/aurasql/AuraSqlSidebar';
import { MessageInput } from '@/components/chat/MessageInput';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlExecuteResponse, AuraSqlSession } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { useToast } from '@/hooks/useToast';
import Prism from 'prismjs';
import 'prismjs/components/prism-sql';
import { format as formatSqlWithLib } from 'sql-formatter';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  Database,
  Download,
  Layers,
  Loader2,
  Pencil,
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
  originalSql?: string;
  resultFilter?: string;
  isEditingSql?: boolean;
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

function AuraSqlQueryPageContent() {
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const { toast } = useToast();

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
  const [recsByContext, setRecsByContext] = useState<Record<string, string[]>>({});
  const [lastRecsContextId, setLastRecsContextId] = useState<string | null>(null);
  const [recsConfirmOpen, setRecsConfirmOpen] = useState(false);
  const [recsConfirmContextId, setRecsConfirmContextId] = useState<string | null>(null);
  const [recsConfirmPrevContextId, setRecsConfirmPrevContextId] = useState<string | null>(null);
  const [historyBanner, setHistoryBanner] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [autoScrollEnabled] = useState(true);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const toastRef = useRef(toast);

  const [loading, setLoading] = useState(true);
  const [loadingTables, setLoadingTables] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    toastRef.current = toast;
  }, [toast]);

  const reportError = useCallback((message: string) => {
    setError(message);
    toastRef.current({
      title: 'Action failed',
      description: message,
      variant: 'destructive',
    });
  }, []);

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
  }, [selectedContextRecord]);

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
        reportError(err instanceof Error ? err.message : 'Failed to load AuraSQL data');
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
            originalSql: log.generated_sql,
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
      reportError(err instanceof Error ? err.message : 'Failed to load chat history');
    }
  };

  const handleFetchTables = useCallback(async () => {
    if (!selectedConnection) return;
    setLoadingTables(true);
    setError(null);
    try {
      const tables = await apiClient.listAuraSqlTables(selectedConnection);
      setTableList(tables);
    } catch (err) {
      reportError(err instanceof Error ? err.message : 'Failed to load tables');
    } finally {
      setLoadingTables(false);
    }
  }, [selectedConnection, reportError]);

  useEffect(() => {
    if (!selectedConnection) {
      setTableList([]);
      return;
    }
    handleFetchTables();
  }, [selectedConnection, handleFetchTables]);

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
      reportError(err instanceof Error ? err.message : 'Failed to apply session context');
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
      reportError(err instanceof Error ? err.message : 'Failed to save context');
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
      reportError(err instanceof Error ? err.message : 'Failed to update context');
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
    } catch (err) {
      reportError(err instanceof Error ? err.message : 'Failed to generate recommendations');
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
      reportError('Select a context to generate SQL.');
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
        originalSql: response.sql,
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
      reportError(err instanceof Error ? err.message : 'Failed to generate SQL');
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
      reportError(err instanceof Error ? err.message : 'Failed to execute SQL');
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

  const handleToggleSqlEdit = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, isEditingSql: !msg.isEditingSql } : msg
      )
    );
  };

  const handleFormatSql = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, editedSql: formatSql(msg.editedSql ?? msg.sql ?? '') }
          : msg
      )
    );
  };

  const handleResetSql = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, editedSql: msg.originalSql ?? msg.sql ?? '' }
          : msg
      )
    );
  };

  const handleResultFilterChange = (messageId: string, value: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, resultFilter: value, showRows: 10 } : msg
      )
    );
  };

  const getFilteredRows = (message: AuraSqlChatMessage) => {
    const execution = message.execution;
    if (!execution) return [];
    const needle = (message.resultFilter ?? '').trim().toLowerCase();
    if (!needle) return execution.rows;
    return execution.rows.filter((row) =>
      execution.columns.some((column) =>
        String(row[column] ?? '').toLowerCase().includes(needle)
      )
    );
  };

  const handleCopySql = async (sql?: string) => {
    if (!sql) {
      reportError('No SQL available to copy.');
      return;
    }
    try {
      await navigator.clipboard.writeText(sql);
    } catch (err) {
      reportError(err instanceof Error ? err.message : 'Failed to copy SQL');
    }
  };

  const handleDownloadSql = (sql?: string) => {
    if (!sql) {
      reportError('No SQL available to download.');
      return;
    }
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

  const handleExportCsv = (messageId: string) => {
    const message = chatMessages.find((item) => item.id === messageId);
    const execution = message?.execution;
    if (!execution || !message) return;
    const rows = getFilteredRows(message);
    const columns = execution.columns;
    const escapeValue = (value: unknown) => {
      const stringValue = String(value ?? '');
      if (/[",\n]/.test(stringValue)) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    };
    const lines = [
      columns.map(escapeValue).join(','),
      ...rows.map((row) => columns.map((column) => escapeValue(row[column])).join(',')),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'results.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const getContextInsights = (message: AuraSqlChatMessage) => {
    if (!message.sourceTables?.length || !selectedContextRecord?.table_names?.length) return null;
    const contextTables = selectedContextRecord.table_names;
    const contextSet = new Set(contextTables.map((table) => table.toLowerCase()));
    const usedTables = message.sourceTables.filter((table) => contextSet.has(table.toLowerCase()));
    const missingTables = contextTables.filter(
      (table) => !message.sourceTables?.some((used) => used.toLowerCase() === table.toLowerCase())
    );
    const percent = contextTables.length > 0 ? Math.round((usedTables.length / contextTables.length) * 100) : 0;
    return {
      used: usedTables.length,
      total: contextTables.length,
      percent,
      missing: missingTables.slice(0, 3),
      missingCount: missingTables.length,
    };
  };

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const showLoader = loading || loadingTables || loadingContext || savingContext || loadingGenerate || loadingExecute;

  return (
    <div className="relative h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.16),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[12%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.18),transparent_65%)] blur-3xl float-slower" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[8%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.14),transparent_70%)] blur-3xl float-slowest" />

      <Header
        showSidebarToggle
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {showLoader ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-background/70 backdrop-blur-sm">
          <div className="glass-panel sheen-border rounded-3xl px-6 py-4 text-center">
            <p className="text-sm font-semibold">Working on AuraSQL</p>
            <p className="text-xs text-muted-foreground mt-1">Preparing schema context and SQL output.</p>
            <div className="mt-4 grid gap-2 text-left text-[11px] text-muted-foreground">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/60 animate-pulse" />
                Loading connections and tables
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/40" />
                Applying schema context
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/40" />
                Generating SQL output
              </div>
            </div>
          </div>
        </div>
      ) : null}

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
            <div className="glass-panel sheen-border h-full rounded-3xl p-4 md:p-6 overflow-hidden flex flex-col bg-accent-soft">
              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full pr-2">
                  <div className="space-y-4 pb-4">
                    {loading && (
                      <div className="rounded-2xl border border-dashed border-border/70 bg-card/40 px-4 py-3 text-sm text-muted-foreground">
                        Loading AuraSQL workspace...
                      </div>
                    )}

                    {error && (
                      <Alert variant="destructive" className="rounded-2xl">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    )}

                    {chatMessages.length === 0 && !loadingGenerate && !loading && (
                      <div className="rounded-2xl border border-dashed border-border/70 bg-card/40 p-6 text-sm text-muted-foreground">
                        Start by asking a question about your schema. The assistant will generate SQL you can refine and execute.
                      </div>
                    )}

                    {chatMessages.map((message) => (
                      <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`${message.role === 'assistant' && message.sql ? 'max-w-[95%]' : 'max-w-[85%]'} space-y-3 ${message.role === 'user' ? 'text-right' : ''}`}
                        >
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
                                  <Button size="sm" variant="ghost" onClick={() => handleFormatSql(message.id)}>
                                    <Wand2 className="h-4 w-4 mr-1" />
                                    Format
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleResetSql(message.id)}>
                                    <RefreshCw className="h-4 w-4 mr-1" />
                                    Reset
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleToggleSqlEdit(message.id)}>
                                    <Pencil className="h-4 w-4 mr-1" />
                                    {message.isEditingSql ? 'Done' : 'Edit'}
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleCopySql(message.editedSql ?? message.sql)}>
                                    <Copy className="h-4 w-4 mr-1" />
                                    Copy
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleDownloadSql(message.editedSql ?? message.sql)}>
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

                              {(() => {
                                const insights = getContextInsights(message);
                                if (!insights) return null;
                                return (
                                  <div className="rounded-xl border border-border/60 bg-card/60 p-3 text-xs space-y-2">
                                    <div className="flex items-center justify-between text-muted-foreground">
                                      <span>Context coverage</span>
                                      <span>
                                        {insights.used}/{insights.total} tables
                                      </span>
                                    </div>
                                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-border/70">
                                      <div
                                        className="h-full rounded-full bg-foreground/70"
                                        style={{ width: `${insights.percent}%` }}
                                      />
                                    </div>
                                    {insights.missingCount > 0 && (
                                      <p className="text-muted-foreground">
                                        Missing context: {insights.missing.join(', ')}
                                        {insights.missingCount > insights.missing.length ? '…' : ''}
                                      </p>
                                    )}
                                  </div>
                                );
                              })()}

                              <div className="rounded-xl border border-border/60 bg-card/60 p-3">
                                {message.isEditingSql ? (
                                  <Textarea
                                    value={message.editedSql ?? message.sql ?? ''}
                                    onChange={(event) => {
                                      const nextValue = event.target.value;
                                      setChatMessages((prev) =>
                                        prev.map((msg) =>
                                          msg.id === message.id ? { ...msg, editedSql: nextValue } : msg
                                        )
                                      );
                                    }}
                                    onBlur={() => {
                                      setChatMessages((prev) =>
                                        prev.map((msg) =>
                                          msg.id === message.id
                                            ? { ...msg, editedSql: formatSql(msg.editedSql ?? msg.sql ?? '') }
                                            : msg
                                        )
                                      );
                                    }}
                                    className="min-h-[280px] w-full resize-none text-xs font-mono leading-relaxed"
                                    spellCheck={false}
                                  />
                                ) : (
                                  <pre
                                    className="prism-sql text-xs font-mono whitespace-pre-wrap leading-relaxed min-h-[280px]"
                                    dangerouslySetInnerHTML={{
                                      __html: highlightSql(formatSql(message.editedSql ?? message.sql ?? '')),
                                    }}
                                  />
                                )}
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
                                      {(() => {
                                        const execution = message.execution;
                                        if (!execution) return null;
                                        const filteredRows = getFilteredRows(message);
                                        if (execution.rows.length === 0) {
                                          return <p className="text-sm text-muted-foreground">No rows returned.</p>;
                                        }
                                        if (filteredRows.length === 0) {
                                          return <p className="text-sm text-muted-foreground">No rows match the filter.</p>;
                                        }
                                        return (
                                          <div className="space-y-3">
                                            <div className="flex flex-wrap items-center gap-2">
                                              <input
                                                value={message.resultFilter ?? ''}
                                                onChange={(event) => handleResultFilterChange(message.id, event.target.value)}
                                                placeholder="Filter results..."
                                                className="min-w-[220px] flex-1 rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                                              />
                                              <Button size="sm" variant="outline" onClick={() => handleExportCsv(message.id)}>
                                                <Download className="h-4 w-4 mr-1" />
                                                Download CSV
                                              </Button>
                                            </div>
                                            <div className="overflow-x-auto rounded-xl border border-border/60">
                                              <table className="min-w-full divide-y divide-border">
                                                <thead className="bg-muted/60">
                                                  <tr>
                                                    {execution.columns.map((column) => (
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
                                                  {filteredRows
                                                    .slice(0, message.showRows || 10)
                                                    .map((row, index) => (
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
                                          </div>
                                        );
                                      })()}
                                      {getFilteredRows(message).length > (message.showRows || 10) && (
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
                      <div className="rounded-2xl border border-dashed border-border/60 bg-card/40 px-4 py-3 text-sm text-muted-foreground flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
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

                    {selectedContextRecord?.table_names?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {selectedContextRecord.table_names.slice(0, 4).map((table) => {
                          const prompt = `Show recent rows from ${table}`;
                          return (
                            <button
                              key={table}
                              type="button"
                              onClick={() => setInputValue(prompt)}
                              className="rounded-full border border-border/70 bg-card/70 px-3 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
                            >
                              {prompt}
                            </button>
                          );
                        })}
                      </div>
                    ) : null}

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

export default function AuraSqlQueryPage() {
  return (
    <Suspense fallback={null}>
      <AuraSqlQueryPageContent />
    </Suspense>
  );
}
