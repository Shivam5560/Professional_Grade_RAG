"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { MessageSquare, Plus, RefreshCw, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import type { ChatSession } from "@/lib/types";
import { cn, formatTimestamp } from "@/lib/utils";

interface SidebarProps {
  onNewChat: () => void;
  onLoadSession?: (sessionId: string) => void;
  currentSessionId?: string;
}

export function Sidebar({ onNewChat, onLoadSession, currentSessionId }: SidebarProps) {
  const { user } = useAuthStore();
  const { confirm, toast } = useToast();
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadHistory = useCallback(async () => {
    if (!user) {
      setHistory([]);
      return;
    }

    setIsRefreshing(true);
    try {
      const bootstrap = await apiClient.getChatBootstrap(undefined, { includeMessages: false });
      setHistory(bootstrap.sessions);
    } catch (error) {
      console.error("Failed to load chat history:", error);
    } finally {
      setIsRefreshing(false);
    }
  }, [user]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    const handleHistoryUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ userId?: number }>).detail;
      if (!user || (detail?.userId && detail.userId !== user.id)) return;
      loadHistory();
    };

    window.addEventListener("chat-history-updated", handleHistoryUpdate as EventListener);
    return () => window.removeEventListener("chat-history-updated", handleHistoryUpdate as EventListener);
  }, [loadHistory, user]);

  const sortedHistory = useMemo(
    () =>
      [...history].sort(
        (a, b) =>
          new Date(b.updated_at || b.created_at).getTime() -
          new Date(a.updated_at || a.created_at).getTime(),
      ),
    [history],
  );

  const deleteSession = async (session: ChatSession) => {
    const confirmed = await confirm({
      title: "Delete chat?",
      description: `Delete "${session.title || "Untitled chat"}"? This cannot be undone.`,
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      variant: "destructive",
    });
    if (!confirmed) return;

    try {
      await apiClient.deleteChatSession(session.id);
      setHistory((current) => current.filter((item) => item.id !== session.id));
      if (currentSessionId === session.id) onNewChat();
      toast({ title: "Chat deleted", description: "The conversation has been removed." });
    } catch (error) {
      toast({
        title: "Delete failed",
        description: error instanceof Error ? error.message : "Unable to delete this conversation.",
        variant: "destructive",
      });
    }
  };

  const deleteAllHistory = async () => {
    if (!user || history.length === 0) return;
    const confirmed = await confirm({
      title: "Delete all chats?",
      description: "This permanently removes Knowledge Studio conversation history.",
      confirmLabel: "Delete all",
      cancelLabel: "Cancel",
      variant: "destructive",
    });
    if (!confirmed) return;

    try {
      await apiClient.deleteAllChatHistory(user.id);
      setHistory([]);
      onNewChat();
      toast({ title: "History deleted", description: "All Knowledge chats were removed." });
    } catch (error) {
      toast({
        title: "Delete failed",
        description: error instanceof Error ? error.message : "Unable to delete chat history.",
        variant: "destructive",
      });
    }
  };

  return (
    <section className="flex h-full min-h-0 flex-col" aria-label="Knowledge chat history">
      <div className="flex items-center gap-2 border-b border-border/60 pb-4">
        <Button className="flex-1 justify-start gap-2" onClick={onNewChat}>
          <Plus className="h-4 w-4" />
          New conversation
        </Button>
        <Button
          aria-label="Refresh chat history"
          disabled={isRefreshing}
          onClick={loadHistory}
          size="icon"
          title="Refresh chat history"
          variant="outline"
        >
          <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
        </Button>
      </div>

      <ScrollArea className="min-h-0 flex-1 py-4 pr-3">
        {sortedHistory.length === 0 ? (
          <div className="grid min-h-52 place-items-center px-6 text-center">
            <div>
              <MessageSquare className="mx-auto h-5 w-5 text-muted-foreground" />
              <p className="mt-3 text-sm font-medium text-foreground">No conversations yet</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                New Knowledge chats will remain here, separate from every other studio.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-1.5">
            {sortedHistory.map((session) => (
              <div
                className={cn(
                  "group flex items-start gap-2 rounded-md border px-3 py-3 transition-colors",
                  currentSessionId === session.id
                    ? "border-foreground/20 bg-foreground/[0.07]"
                    : "border-transparent hover:border-border/70 hover:bg-muted/55",
                )}
                key={session.id}
              >
                <button
                  className="min-w-0 flex-1 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  onClick={() => onLoadSession?.(session.id)}
                  type="button"
                >
                  <span className="block truncate text-sm font-medium text-foreground">
                    {session.title || "Untitled chat"}
                  </span>
                  <span className="mt-1 block text-xs text-muted-foreground">
                    {formatTimestamp(session.updated_at || session.created_at)}
                  </span>
                </button>
                <button
                  aria-label={`Delete ${session.title || "untitled chat"}`}
                  className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground opacity-70 transition-colors hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover:opacity-100"
                  onClick={() => deleteSession(session)}
                  title="Delete chat"
                  type="button"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      <Button
        className="mt-4 w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
        disabled={history.length === 0}
        onClick={deleteAllHistory}
        variant="ghost"
      >
        <Trash2 className="mr-2 h-4 w-4" />
        Delete Knowledge history
      </Button>
    </section>
  );
}
