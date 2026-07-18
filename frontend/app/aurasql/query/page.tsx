'use client';

export const dynamic = 'force-dynamic';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { MessageInput } from '@/components/chat/MessageInput';
import { AuraSqlResultViewport } from '@/components/aurasql/AuraSqlResultViewport';
import { ContextNameDialog } from '@/components/aurasql/ContextNameDialog';
import { CanvasHeader } from '@/components/shell/CanvasHeader';
import { ContextRibbon } from '@/components/shell/ContextRibbon';
import { FocusCanvas } from '@/components/shell/FocusCanvas';
import { Inspector } from '@/components/shell/Inspector';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection, AuraSqlContext, AuraSqlExecuteResponse, AuraSqlSession } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { useToast } from '@/hooks/useToast';
import { format as formatSqlWithLib } from 'sql-formatter';
import type { SqlLanguage } from 'sql-formatter';
import {
  AlertCircle,
  ArrowRight,
  Copy,
  Database,
  Download,
  Loader2,
  MessageSquarePlus,
  PlayCircle,
  RefreshCw,
  Table,
  Wand2,
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
  validationErrors?: string[];
  executionError?: string | null;
};

const makeMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

const FORMAT_LANGUAGE_BY_DIALECT: Record<string, SqlLanguage> = {
  postgresql: 'postgresql',
  postgres: 'postgresql',
  mysql: 'mysql',
  oracle: 'plsql',
  bigquery: 'bigquery',
  snowflake: 'snowflake',
  sqlite: 'sqlite',
  tsql: 'tsql',
};

const OUTPUT_DIALECT_OPTIONS = [
  { value: 'connection', label: 'Connection DB (default)' },
  { value: 'postgres', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'oracle', label: 'Oracle' },
  { value: 'bigquery', label: 'BigQuery' },
  { value: 'snowflake', label: 'Snowflake' },
  { value: 'sqlite', label: 'SQLite' },
  { value: 'tsql', label: 'T-SQL' },
];

const formatSql = (sql: string, dialect: string) => {
  try {
    const language: SqlLanguage = FORMAT_LANGUAGE_BY_DIALECT[dialect] || 'postgresql';
    return formatSqlWithLib(sql, { language });
  } catch {
    return sql;
  }
};

function AuraSqlQueryPageContent() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const { toast } = useToast();

  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [selectedConnection, setSelectedConnection] = useState('');
  const [selectedContext, setSelectedContext] = useState('');
  const [activeContextId, setActiveContextId] = useState('');
  const [tableList, setTableList] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());
  const [tableFilter, setTableFilter] = useState('');
  const [showTablesMenu, setShowTablesMenu] = useState(false);
  const [outputDialect, setOutputDialect] = useState('connection');
  const [sessionContextId, setSessionContextId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<AuraSqlChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [recsOpen, setRecsOpen] = useState(false);
  const [recsByContext, setRecsByContext] = useState<Record<string, string[]>>({});
  const [historyBanner, setHistoryBanner] = useState<string | null>(null);
  const [autoScrollEnabled] = useState(true);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const toastRef = useRef(toast);

  const [loading, setLoading] = useState(true);
  const [loadingTables, setLoadingTables] = useState(false);
  const [loadingContext, setLoadingContext] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [contextNameOpen, setContextNameOpen] = useState(false);
  const [contextSaveError, setContextSaveError] = useState<string | null>(null);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [executingMessageId, setExecutingMessageId] = useState<string | null>(null);
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
  const sqlDisplayDialect = useMemo(() => {
    if (outputDialect !== 'connection') return outputDialect;
    return connections.find((conn) => conn.id === selectedConnection)?.db_type || 'postgresql';
  }, [connections, outputDialect, selectedConnection]);

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
      return;
    }
    setSelectedTables(new Set(selectedContextRecord.table_names));
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

  const handleSaveContext = async (name: string) => {
    if (!selectedConnection || selectedTables.size === 0) return;
    setSavingContext(true);
    setContextSaveError(null);
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
      setContextNameOpen(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save context';
      setContextSaveError(message);
      reportError(message);
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
        sessionId || undefined,
        outputDialect === 'connection' ? undefined : outputDialect
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
            validationErrors: response.validation_errors ?? [],
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
        validationErrors: response.validation_errors ?? [],
      };
      setChatMessages((prev) => [...prev, assistantMessage]);

      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
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

    setExecutingMessageId(messageId);
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
            ? { ...msg, execution: result, executionError: null, showRows: msg.showRows ?? 10, showResults: true }
            : msg
        )
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to execute SQL';
      setChatMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, executionError: errorMessage }
            : msg
        )
      );
      reportError(err instanceof Error ? err.message : 'Failed to execute SQL');
    } finally {
      setExecutingMessageId(null);
    }
  };

  const handleFormatSql = (messageId: string) => {
    setChatMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, editedSql: formatSql(msg.editedSql ?? msg.sql ?? '', sqlDisplayDialect) }
          : msg
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

  const getMessageChecks = (message: AuraSqlChatMessage) => {
    const joinedErrors = (message.validationErrors ?? []).join(' ').toLowerCase();
    const hasSyntaxError = joinedErrors.includes('syntax') || joinedErrors.includes('parse');
    const hasSchemaError =
      joinedErrors.includes('table') ||
      joinedErrors.includes('column') ||
      joinedErrors.includes('schema');

    const syntax: 'pass' | 'fail' | 'pending' = hasSyntaxError
      ? 'fail'
      : message.sql
      ? 'pass'
      : 'pending';
    const verification: 'pass' | 'fail' | 'pending' = hasSchemaError
      ? 'fail'
      : message.sourceTables?.length
      ? 'pass'
      : message.sql
      ? 'pass'
      : 'pending';
    const typeCheck: 'pass' | 'fail' | 'pending' = message.sql
      ? 'pass'
      : (message.validationErrors?.length ?? 0) > 0
      ? 'fail'
      : 'pending';
    const executionStatus: 'pass' | 'fail' | 'pending' = message.execution
      ? 'pass'
      : message.executionError
      ? 'fail'
      : 'pending';
    const optimization: 'pass' | 'warn' | 'fail' | 'pending' =
      message.confidenceLevel === 'high'
        ? 'pass'
        : message.confidenceLevel === 'medium'
        ? 'warn'
        : message.confidenceLevel === 'low'
        ? 'fail'
        : 'pending';

    return [
      { label: 'Verification', status: verification },
      { label: 'Types', status: typeCheck },
      { label: 'Syntax', status: syntax },
      { label: 'Execution', status: executionStatus },
      { label: 'Optimized', status: optimization },
    ];
  };

  const getCheckBadgeClass = (status: 'pass' | 'warn' | 'fail' | 'pending') => {
    if (status === 'pass') return 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-200';
    if (status === 'warn') return 'bg-amber-500/15 text-amber-800 dark:text-amber-200';
    if (status === 'fail') return 'bg-rose-500/15 text-rose-800 dark:text-rose-200';
    return 'bg-muted text-muted-foreground';
  };

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const latestUserMessage = [...chatMessages].reverse().find((message) => message.role === 'user');
  const latestSqlMessage = [...chatMessages].reverse().find(
    (message) => message.role === 'assistant' && Boolean(message.sql)
  );
  const activeConnectionRecord = connections.find((connection) => connection.id === selectedConnection);
  const activeStep = latestSqlMessage?.execution ? 3 : latestSqlMessage?.sql ? 2 : 1;
  const detailsOpen = recsOpen || showTablesMenu;

  return (
    <FocusCanvas ariaLabel="AuraSQL query workspace" className="h-[calc(100svh-2rem)] min-h-0 overflow-hidden">
      <CanvasHeader
        eyebrow="AuraSQL"
        title="Ask the business. Inspect the truth."
        description="Move from a plain-language question to reviewed SQL and an explorable result without leaving the canvas."
        status={
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            {activeConnectionRecord ? 'Connection ready' : 'Connection required'}
          </span>
        }
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => setShowTablesMenu(true)}>
              <Table className="mr-2 h-4 w-4" />
              Schema
            </Button>
            <Button variant="ghost" size="icon" aria-label="Start new query" title="Start new query" onClick={handleStartNewChat}>
              <MessageSquarePlus className="h-4 w-4" />
            </Button>
          </>
        }
      />

      <ContextRibbon label="Query context">
        <label className="sr-only" htmlFor="aurasql-connection">Connection</label>
        <select
          id="aurasql-connection"
          value={selectedConnection}
          onChange={(event) => setSelectedConnection(event.target.value)}
          className="h-8 max-w-56 rounded-md border border-border/70 bg-workspace-inset px-2 text-xs text-foreground"
        >
          {connections.length === 0 ? <option value="">No connection</option> : null}
          {connections.map((connection) => <option key={connection.id} value={connection.id}>{connection.name} · {connection.database}</option>)}
        </select>
        <label className="sr-only" htmlFor="aurasql-context">Context</label>
        <select
          id="aurasql-context"
          value={selectedContext}
          onChange={(event) => setSelectedContext(event.target.value)}
          className="h-8 max-w-56 rounded-md border border-border/70 bg-workspace-inset px-2 text-xs text-foreground"
        >
          <option value="">Select context</option>
          {connectionContexts.map((context) => <option key={context.id} value={context.id}>{context.name} · {context.table_names.length} tables</option>)}
        </select>
        <label className="sr-only" htmlFor="sql-output-dialect">SQL dialect</label>
        <select id="sql-output-dialect" value={outputDialect} onChange={(event) => setOutputDialect(event.target.value)} className="h-8 rounded-md border border-border/70 bg-workspace-inset px-2 text-xs text-foreground">
          {OUTPUT_DIALECT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </ContextRibbon>

      <section aria-label="Query progress" className="grid grid-cols-3 border-b border-border/60 py-4">
        {[
          { number: 1, label: 'Ask' },
          { number: 2, label: 'Review SQL' },
          { number: 3, label: 'Explore results' },
        ].map((step, index) => (
          <div key={step.label} className="flex min-w-0 items-center">
            <div className="flex min-w-0 items-center gap-2">
              <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border text-[11px] font-semibold ${activeStep >= step.number ? 'border-foreground bg-foreground text-background' : 'border-border bg-workspace-inset text-muted-foreground'}`}>{step.number}</span>
              <span className={`truncate text-xs font-medium ${activeStep >= step.number ? 'text-foreground' : 'text-muted-foreground'}`}>{step.label}</span>
            </div>
            {index < 2 ? <ArrowRight className="mx-2 h-3.5 w-3.5 shrink-0 text-muted-foreground sm:mx-4" /> : null}
          </div>
        ))}
      </section>

      <div data-scroll-owner="query-results" className="relative flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto py-5">
        {(loading || loadingGenerate) ? (
          <div className="flex min-h-24 items-center justify-center gap-3 border-y border-border/50 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            {loading ? 'Preparing connections and context' : 'Drafting and validating SQL'}
          </div>
        ) : null}

        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {connections.length === 0 && !loading ? (
          <section className="grid min-h-64 place-items-center border-y border-border/60 bg-workspace-raised px-5 text-center">
            <div className="max-w-sm">
              <Database className="mx-auto h-7 w-7 text-muted-foreground" />
              <h2 className="mt-4 text-lg font-semibold">Connect a database first</h2>
              <p className="mt-2 text-sm text-muted-foreground">AuraSQL keeps credentials in your existing connection profile and uses its schema to ground every query.</p>
              <Button className="mt-5" onClick={() => router.push('/aurasql/connections/new')}>Create connection</Button>
            </div>
          </section>
        ) : (
          <>
            <section data-fixed-composer="aurasql" aria-label="Ask a data question" className="sticky top-0 z-20 mx-auto w-full max-w-4xl rounded-lg border border-border/70 bg-workspace-raised p-4 shadow-sm">
              {latestUserMessage ? <p className="mb-3 text-sm leading-6 text-muted-foreground"><span className="font-medium text-foreground">Current question:</span> {latestUserMessage.content}</p> : null}
              <MessageInput
                onSend={handleSendMessage}
                disabled={loadingGenerate || !activeContextId || (hasUnsavedChanges && !sessionContextId)}
                value={inputValue}
                onChange={setInputValue}
                placeholder={activeContextId ? 'Ask a question about the selected data…' : 'Select a schema context to begin'}
              />
              {historyBanner ? <p className="mt-2 text-xs text-amber-600 dark:text-amber-300">{historyBanner}</p> : null}
              {!activeContextId ? <p className="mt-2 text-xs text-muted-foreground">Choose a saved context above, or open Schema to select tables.</p> : null}
            </section>

            {latestSqlMessage?.sql ? (
              <section aria-label="Review generated SQL" className="overflow-hidden rounded-lg border border-border/70 bg-workspace-raised">
                <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 px-4 py-3">
                  <div>
                    <h2 className="text-sm font-semibold">Review generated SQL</h2>
                    <p className="mt-0.5 text-xs text-muted-foreground">Validate the statement before executing it against {activeConnectionRecord?.name ?? 'the database'}.</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button size="icon" variant="ghost" aria-label="Format SQL" title="Format SQL" onClick={() => handleFormatSql(latestSqlMessage.id)}><Wand2 className="h-4 w-4" /></Button>
                    <Button size="icon" variant="ghost" aria-label="Copy SQL" title="Copy SQL" onClick={() => handleCopySql(latestSqlMessage.editedSql || latestSqlMessage.sql)}><Copy className="h-4 w-4" /></Button>
                    <Button size="icon" variant="ghost" aria-label="Download SQL" title="Download SQL" onClick={() => handleDownloadSql(latestSqlMessage.editedSql || latestSqlMessage.sql)}><Download className="h-4 w-4" /></Button>
                  </div>
                </header>
                <Textarea
                  aria-label="Generated SQL"
                  value={latestSqlMessage.editedSql || latestSqlMessage.sql}
                  onChange={(event) => setChatMessages((previous) => previous.map((message) => message.id === latestSqlMessage.id ? { ...message, editedSql: event.target.value } : message))}
                  className="min-h-40 resize-y rounded-none border-0 bg-transparent p-4 font-mono text-xs leading-6 shadow-none focus-visible:ring-0"
                />
                <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border/60 px-4 py-3">
                  <div className="flex flex-wrap gap-1.5">
                    {getMessageChecks(latestSqlMessage).map((check) => <Badge key={check.label} className={getCheckBadgeClass(check.status)} variant="secondary">{check.label}</Badge>)}
                  </div>
                  <Button onClick={() => handleExecuteMessage(latestSqlMessage.id)} disabled={executingMessageId === latestSqlMessage.id}>
                    {executingMessageId === latestSqlMessage.id ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-2 h-4 w-4" />}
                    Run query
                  </Button>
                </footer>
                {latestSqlMessage.executionError ? <p className="border-t border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-700 dark:text-rose-300">{latestSqlMessage.executionError}</p> : null}
              </section>
            ) : null}

            {latestSqlMessage?.execution ? (
              <AuraSqlResultViewport execution={latestSqlMessage.execution} onExport={() => handleExportCsv(latestSqlMessage.id)} />
            ) : latestSqlMessage?.sql ? (
              <div className="flex min-h-28 items-center justify-center border-y border-dashed border-border/70 text-center text-sm text-muted-foreground">
                Run the reviewed SQL to unlock table and graph exploration.
              </div>
            ) : null}
          </>
        )}
      </div>

      <Inspector
        open={detailsOpen}
        onOpenChange={(open) => { if (!open) { setRecsOpen(false); setShowTablesMenu(false); } }}
        title="Schema and query guidance"
      >
        <div className="space-y-7">
          <section>
            <div className="flex items-center justify-between gap-3">
              <div><h3 className="text-sm font-semibold">Question ideas</h3><p className="mt-1 text-xs text-muted-foreground">Grounded in the active schema context.</p></div>
              <Button size="sm" variant="outline" onClick={handleRecommendations} disabled={!activeContextId || loadingContext}>{loadingContext ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Generate'}</Button>
            </div>
            <div className="mt-3 grid gap-2">
              {recommendations.length === 0 ? <p className="border-y border-border/50 py-4 text-xs text-muted-foreground">Generate focused starting questions when you need them.</p> : recommendations.map((recommendation) => <button key={recommendation} type="button" className="border-b border-border/50 py-3 text-left text-sm leading-5 transition-colors hover:text-[hsl(var(--chart-2))]" onClick={() => { setInputValue(recommendation); setRecsOpen(false); setShowTablesMenu(false); }}>{recommendation}</button>)}
            </div>
          </section>
          <section>
            <div className="flex items-center justify-between gap-3"><div><h3 className="text-sm font-semibold">Tables in context</h3><p className="mt-1 text-xs text-muted-foreground">{selectedTables.size} of {tableList.length} selected</p></div><Button size="icon" variant="ghost" aria-label="Refresh tables" onClick={handleFetchTables}><RefreshCw className={`h-4 w-4 ${loadingTables ? 'animate-spin' : ''}`} /></Button></div>
            <input value={tableFilter} onChange={(event) => setTableFilter(event.target.value)} placeholder="Filter tables" className="mt-3 h-10 w-full rounded-md border border-border/70 bg-background px-3 text-sm" />
            <div className="mt-3 max-h-72 divide-y divide-border/50 overflow-y-auto border-y border-border/50">
              {filteredTables.map((table) => <label key={table} className="flex cursor-pointer items-center gap-3 py-3 text-sm"><input type="checkbox" checked={selectedTables.has(table)} onChange={() => handleToggleTable(table)} className="h-4 w-4" /><span className="min-w-0 flex-1 truncate font-mono text-xs">{table}</span></label>)}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={handleUseSessionContext} disabled={selectedTables.size === 0 || savingContext}>Use for session</Button>
              <Button size="sm" onClick={selectedContextRecord ? handleUpdateContext : () => setContextNameOpen(true)} disabled={selectedTables.size === 0 || savingContext}>{selectedContextRecord ? 'Update context' : 'Save context'}</Button>
            </div>
          </section>
        </div>
      </Inspector>
      <ContextNameDialog
        connectionLabel={activeConnectionRecord?.name ?? ''}
        error={contextSaveError}
        onCancel={() => { if (!savingContext) { setContextNameOpen(false); setContextSaveError(null); } }}
        onSave={handleSaveContext}
        open={contextNameOpen}
        saving={savingContext}
        selectedTables={Array.from(selectedTables)}
      />
    </FocusCanvas>
  );


}

export default function AuraSqlQueryPage() {
  return (
    <Suspense fallback={null}>
      <AuraSqlQueryPageContent />
    </Suspense>
  );
}
