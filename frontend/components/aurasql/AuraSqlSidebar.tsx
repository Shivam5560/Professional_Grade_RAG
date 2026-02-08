'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Database, Plus, RefreshCw, MessageSquare, Star } from 'lucide-react';
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
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());

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

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem('aurasql_pinned_sessions');
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as string[];
      setPinnedIds(new Set(parsed));
    } catch {
      setPinnedIds(new Set());
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('aurasql_pinned_sessions', JSON.stringify(Array.from(pinnedIds)));
  }, [pinnedIds]);

  const togglePin = (id: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const displayHistory = useMemo(() => {
    const source = sessions.length > 0 ? sessions : history;
    const sorted = [...source].sort((a, b) => {
      const aPinned = pinnedIds.has(a.id) ? 1 : 0;
      const bPinned = pinnedIds.has(b.id) ? 1 : 0;
      if (aPinned !== bPinned) return bPinned - aPinned;
      return 0;
    });
    return sorted.slice(0, 12);
  }, [sessions, history, pinnedIds]);

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
                const isPinned = pinnedIds.has(item.id);
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
                    <div className="flex items-start gap-2 px-3 py-3">
                      <button
                        type="button"
                        onClick={() => onSelectSession?.(item)}
                        className="flex w-full items-start gap-3 text-left"
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
                      <button
                        type="button"
                        className={cn(
                          'mt-0.5 rounded-md p-1 transition-colors',
                          isPinned ? 'text-amber-500' : 'text-muted-foreground hover:text-foreground'
                        )}
                        onClick={(event) => {
                          event.stopPropagation();
                          togglePin(item.id);
                        }}
                        title={isPinned ? 'Unpin' : 'Pin'}
                        aria-pressed={isPinned}
                      >
                        <Star className="h-3.5 w-3.5" fill={isPinned ? 'currentColor' : 'none'} />
                      </button>
                    </div>
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
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60 mt-2"
          onClick={() => router.push('/developer')}
        >
          <Star className="h-4 w-4" />
          Developer
        </Button>
      </div>
    </div>
  );
}
