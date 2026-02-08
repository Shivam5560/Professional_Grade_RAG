'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Database, Plus, History, ChevronRight } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AuraSqlHistoryItem } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { cn, formatTimestamp } from '@/lib/utils';

interface AuraSqlSidebarProps {
  currentHistoryId?: string | null;
  onSelectHistory?: (item: AuraSqlHistoryItem) => void;
}

export function AuraSqlSidebar({ currentHistoryId, onSelectHistory }: AuraSqlSidebarProps) {
  const router = useRouter();
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadHistory = async () => {
      setIsLoading(true);
      try {
        const rows = await apiClient.listAuraSqlHistory();
        setHistory(rows);
      } catch (err) {
        console.error('Failed to load AuraSQL history:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadHistory();
  }, []);

  const displayHistory = useMemo(() => history.slice(0, 10), [history]);

  const formatStatus = (status: string) => status.replace('_', ' ');

  return (
    <div className="flex h-full w-72 flex-col border-r border-border/60 bg-card/70 backdrop-blur-xl">
      <div className="p-4 space-y-2">
        <Button className="w-full justify-start gap-2 bg-foreground text-background hover:bg-foreground/90" onClick={() => router.push('/aurasql/contexts/new')}>
          <Plus className="h-4 w-4" />
          New Context
        </Button>
        <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60" onClick={() => router.push('/aurasql/connections/new')}>
          <Database className="h-4 w-4" />
          New Connection
        </Button>
      </div>

      <div className="px-4 py-2 flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Recent SQL</h2>
          <History className="h-4 w-4 text-muted-foreground" />
        </div>
        <ScrollArea className="flex-1 pr-2">
          {isLoading ? (
            <div className="px-2 py-6 text-xs text-muted-foreground">Loading history...</div>
          ) : displayHistory.length === 0 ? (
            <div className="px-2 py-6 text-xs text-muted-foreground">No SQL history yet.</div>
          ) : (
            <div className="space-y-2">
              {displayHistory.map((item) => {
                const created = item.created_at ? formatTimestamp(item.created_at) : '';
                const label = item.natural_language_query || item.generated_sql || 'SQL execution';
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => onSelectHistory?.(item)}
                    className={cn(
                      'w-full text-left rounded-xl border border-transparent px-3 py-2 transition-all',
                      currentHistoryId === item.id
                        ? 'border-foreground/10 bg-foreground/5'
                        : 'hover:border-border/60 hover:bg-muted/60'
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-foreground line-clamp-2">{label}</p>
                      <ChevronRight className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      {formatStatus(item.status)} • {created}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </div>

      <div className="mt-auto p-4 border-t border-border/60">
        <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60" onClick={() => router.push('/')}>
          <Database className="h-4 w-4" />
          Dashboard
        </Button>
      </div>
    </div>
  );
}
