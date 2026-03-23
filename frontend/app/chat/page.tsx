'use client';

import { useEffect, useMemo, useState } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Header } from '@/components/layout/Header';
import { useChat } from '@/hooks/useChat';
import { useAuthStore } from '@/lib/store';
import { useToast } from '@/hooks/useToast';
import AuthPage from '@/app/auth/page';
import VerticalMagnificationDock from '@/components/ui/vertical-magnification-dock';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/lib/api';
import { ChatSession } from '@/lib/types';
import { formatTimestamp } from '@/lib/utils';
import { ChevronDown, Database, HelpCircle, MessageSquare, Plus, Sparkles, Trash2 } from 'lucide-react';

export default function ChatPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isHistoryPanelVisible, setIsHistoryPanelVisible] = useState(false);
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const { sessionId, messages, isLoading, error, sendMessage, clearChat, hydrateConversation, latestTokenUsage } = useChat();
  const { toast, confirm } = useToast();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    const stored = window.localStorage.getItem('sidebar');
    if (stored === 'closed') {
      setIsSidebarOpen(false);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem('sidebar', isSidebarOpen ? 'open' : 'closed');
  }, [isSidebarOpen]);

  useEffect(() => {
    const fetchBootstrap = async () => {
      if (!user) return;
      setIsHistoryLoading(true);
      try {
        const bootstrap = await apiClient.getChatBootstrap();
        setHistory(bootstrap.sessions);
        if (bootstrap.active_session_id) {
          hydrateConversation(bootstrap.active_session_id, bootstrap.messages);
        }
      } catch (historyError) {
        console.error('Failed to load chat history:', historyError);
      } finally {
        setIsHistoryLoading(false);
      }
    };

    fetchBootstrap();
  }, [hydrateConversation, user]);

  useEffect(() => {
    const refreshHistoryOnly = async (event: Event) => {
      const detail = (event as CustomEvent<{ userId?: number }>).detail;
      if (!user || (detail?.userId && detail.userId !== user.id)) return;

      try {
        const bootstrap = await apiClient.getChatBootstrap(sessionId, { includeMessages: false });
        setHistory(bootstrap.sessions);
      } catch (historyError) {
        console.error('Failed to refresh chat history:', historyError);
      }
    };

    window.addEventListener('chat-history-updated', refreshHistoryOnly as EventListener);
    return () => {
      window.removeEventListener('chat-history-updated', refreshHistoryOnly as EventListener);
    };
  }, [sessionId, user]);

  const handleNewChat = async () => {
    await clearChat();
    setIsHistoryPanelVisible(false);
  };

  const handleLoadSession = async (sessionIdToLoad: string) => {
    try {
      setIsHistoryLoading(true);
      const bootstrap = await apiClient.getChatBootstrap(sessionIdToLoad);
      setHistory(bootstrap.sessions);
      if (bootstrap.active_session_id) {
        hydrateConversation(bootstrap.active_session_id, bootstrap.messages);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
      toast({ title: 'Failed to load session', description: error instanceof Error ? error.message : 'Unknown error', variant: 'destructive' });
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleDeleteAllHistory = async () => {
    if (!user || history.length === 0) return;
    const confirmed = await confirm({
      title: 'Delete all chats?',
      description: 'This will permanently remove your entire chat history.',
      confirmLabel: 'Delete all',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    });
    if (!confirmed) return;

    try {
      await apiClient.deleteAllChatHistory(user.id);
      setHistory([]);
      await clearChat();
      setIsHistoryPanelVisible(false);
      toast({
        title: 'History deleted',
        description: 'All chats were removed.',
      });
    } catch (historyError) {
      toast({
        title: 'Delete failed',
        description: historyError instanceof Error ? historyError.message : 'Unable to delete all chat history.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteSession = async (entry: ChatSession) => {
    const title = entry.title || 'Untitled chat';
    const confirmed = await confirm({
      title: 'Delete chat?',
      description: `Delete "${title}"? This cannot be undone.`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    });
    if (!confirmed) return;

    try {
      await apiClient.deleteChatSession(entry.id);
      setHistory((prev) => prev.filter((item) => item.id !== entry.id));
      if (sessionId === entry.id) {
        await clearChat();
      }
      toast({
        title: 'Chat deleted',
        description: 'The conversation has been removed.',
      });
    } catch (sessionError) {
      toast({
        title: 'Delete failed',
        description: sessionError instanceof Error ? sessionError.message : 'Unable to delete chat.',
        variant: 'destructive',
      });
    }
  };

  const renderHistoryEntry = (entry: ChatSession) => (
    <div
      key={entry.id}
      className={`w-full rounded-xl border px-2 py-2 transition-all ${
        sessionId === entry.id
          ? 'border-foreground/20 bg-foreground/10'
          : 'border-border/60 bg-background/40 hover:bg-background/70'
      }`}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={() => handleLoadSession(entry.id)}
          className="flex-1 text-left"
        >
          <p className="text-xs font-semibold text-foreground line-clamp-2">
            {entry.title || 'Untitled chat'}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            {formatTimestamp(entry.updated_at || entry.created_at)}
          </p>
        </button>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            handleDeleteSession(entry);
          }}
          className="h-7 w-7 rounded-md border border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/60"
          title="Delete chat"
          aria-label="Delete chat"
        >
          <Trash2 className="h-3.5 w-3.5 mx-auto" />
        </button>
      </div>
    </div>
  );

  const sortedHistory = useMemo(() => {
    return [...history].sort((a, b) => {
      const aTime = new Date(a.updated_at || a.created_at).getTime();
      const bTime = new Date(b.updated_at || b.created_at).getTime();
      return bTime - aTime;
    });
  }, [history]);

  const topFiveHistory = sortedHistory.slice(0, 5);
  const extraHistory = sortedHistory.slice(5);

  const dockItems = [
    {
      icon: <MessageSquare size={18} />,
      label: isHistoryPanelVisible ? 'Hide Chats' : 'Show Chats',
      onClick: () => setIsHistoryPanelVisible((prev) => !prev),
      className: isHistoryPanelVisible ? 'ring-2 ring-ring' : '',
    },
    {
      icon: <Plus size={18} />,
      label: 'New Chat',
      onClick: handleNewChat,
    },
    {
      icon: <Database size={18} />,
      label: 'Knowledge Base',
      onClick: () => (window.location.href = '/knowledge-base'),
    },
    {
      icon: <Sparkles size={18} />,
      label: 'Home',
      onClick: () => (window.location.href = '/'),
    },
    {
      icon: <HelpCircle size={18} />,
      label: 'Developer',
      onClick: () => (window.location.href = '/developer'),
    },
  ];

  if (!isMounted) {
    return null;
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

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
          className={`hidden md:block relative z-30 transition-all duration-300 ease-out ${
            isSidebarOpen
              ? isHistoryPanelVisible
                ? 'w-[400px] opacity-100'
                : 'w-[140px] opacity-100'
              : 'w-0 opacity-0'
          }`}
        >
          <div
            className={`h-full transition-all duration-300 ${
              isSidebarOpen ? 'translate-x-0' : '-translate-x-6 pointer-events-none'
            }`}
          >
            <div className="h-full border-r border-border/60 bg-card/70 backdrop-blur-xl p-3 flex gap-3 items-center overflow-visible">
              <div className="h-full flex items-center">
                <VerticalMagnificationDock items={dockItems} panelWidth={66} baseItemSize={44} magnification={64} />
              </div>

              {isHistoryPanelVisible && (
                <div className="flex-1 rounded-2xl border border-border/60 bg-card/60 p-3 min-w-0">
                  <div className="h-full flex flex-col">
                    <button
                      type="button"
                      onClick={() => setIsHistoryPanelVisible(false)}
                      className="w-full flex items-center justify-between rounded-xl border border-border/60 bg-background/60 px-3 py-2 text-sm font-semibold"
                    >
                      <span>Chat History</span>
                      <ChevronDown className="h-4 w-4 rotate-180" />
                    </button>

                    <ScrollArea className="flex-1 mt-3 pr-1">
                      {isHistoryLoading ? (
                        <p className="text-xs text-muted-foreground px-1">Loading history...</p>
                      ) : topFiveHistory.length === 0 ? (
                        <p className="text-xs text-muted-foreground px-1">No history yet. Start a new chat.</p>
                      ) : (
                        <div className="space-y-2">
                          {topFiveHistory.map((entry) => renderHistoryEntry(entry))}

                          {showAllHistory && extraHistory.map((entry) => renderHistoryEntry(entry))}
                        </div>
                      )}
                    </ScrollArea>

                    <button
                      type="button"
                      className="mt-3 w-full rounded-xl border border-border/60 bg-background/60 px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
                      onClick={() => setShowAllHistory((prev) => !prev)}
                      disabled={extraHistory.length === 0}
                    >
                      {extraHistory.length === 0
                        ? 'All chats shown'
                        : showAllHistory
                          ? 'Show less'
                          : `Show more (${extraHistory.length})`}
                    </button>
                    <button
                      type="button"
                      className="mt-2 w-full rounded-xl border border-destructive/40 bg-destructive/5 px-3 py-2 text-xs text-destructive hover:bg-destructive/10 disabled:opacity-50"
                      onClick={handleDeleteAllHistory}
                      disabled={history.length === 0}
                    >
                      <span className="inline-flex items-center gap-1.5">
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete all history
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </aside>
        <main className="relative z-10 flex flex-1 flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-hidden p-3 md:p-6">
            <div className="glass-panel h-full rounded-3xl">
              <ChatInterface
                sessionId={sessionId}
                messages={messages}
                isLoading={isLoading}
                error={error}
                sendMessage={sendMessage}
                tokenUsage={latestTokenUsage}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
