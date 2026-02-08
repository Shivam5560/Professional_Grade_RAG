'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Database, Plus, RefreshCw, MessageSquare } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AuraSqlSession } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { cn, formatTimestamp } from '@/lib/utils';

interface AuraSqlSidebarProps {
  currentHistoryId?: string | null;
  sessions?: AuraSqlSession[];
  onSelectSession?: (session: AuraSqlSession) => void;
  onNewChat?: () => void;
}

export function AuraSqlSidebar({ currentHistoryId, sessions = [], onSelectSession, onNewChat }: AuraSqlSidebarProps) {
  const router = useRouter();
  const [history, setHistory] = useState<AuraSqlSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadHistory = async () => {
      setIsLoading(true);
      try {
        const rows = await apiClient.listAuraSqlSessions();
        setHistory(rows);
      } catch (err) {
        console.error('Failed to load AuraSQL history:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadHistory();
  }, []);

  const displayHistory = useMemo(() => {
    const source = sessions.length > 0 ? sessions : history;
    return source.slice(0, 12);
  }, [sessions, history]);

  return (
    <div className="flex h-full w-72 flex-col border-r border-border/60 bg-card/70 backdrop-blur-xl">
      <div className="p-4 space-y-2">
        <Button
          className="w-full justify-start gap-2 bg-foreground text-background hover:bg-foreground/90"
          onClick={() => {
            onNewChat?.();
            router.push('/aurasql/query');
          }}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
        <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60" onClick={() => router.push('/aurasql/connections/new')}>
          <Database className="h-4 w-4" />
          New Connection
        </Button>
      </div>

      <div className="px-4 py-2 flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Recent Conversations</h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-muted-foreground hover:text-foreground hover:bg-muted/60"
            onClick={() => {
              setIsLoading(true);
              apiClient
                .listAuraSqlSessions()
                .then(setHistory)
                .finally(() => setIsLoading(false));
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <ScrollArea className="flex-1 pr-2">
          {isLoading ? (
            <div className="px-2 py-6 text-xs text-muted-foreground">Loading history...</div>
          ) : displayHistory.length === 0 ? (
            <div className="px-2 py-6 text-xs text-muted-foreground">No chat history yet.</div>
          ) : (
            <div className="space-y-2">
                        {displayHistory.map((item) => {
                const created = item.updated_at || item.created_at ? formatTimestamp(item.updated_at || item.created_at) : '';
                const label = item.title || 'Untitled chat';
                return (
                  <div
                    key={item.id}
                    className={cn(
                      'rounded-xl border border-transparent transition-all',
                      currentHistoryId === item.id
                        ? 'border-foreground/10 bg-foreground/5'
                        : 'hover:border-border/60 hover:bg-muted/60'
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelectSession?.(item)}
                      className="flex w-full items-start gap-3 px-3 py-3 text-left"
                    >
                      <MessageSquare className="h-4 w-4 mt-0.5 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground whitespace-normal break-words leading-snug">
                          {label}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {created}
                        </p>
                      </div>
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </div>

      <div className="mt-auto p-4 border-t border-border/60">
        <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60" onClick={() => router.push('/') }>
          <Database className="h-4 w-4" />
          Dashboard
        </Button>
        <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60 mt-2" onClick={() => router.push('/chat')}>
          <MessageSquare className="h-4 w-4" />
          RAG Chat
        </Button>
      </div>
    </div>
  );
}
