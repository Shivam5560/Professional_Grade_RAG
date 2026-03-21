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
import { ChevronDown, Database, HelpCircle, MessageSquare, Plus, Sparkles } from 'lucide-react';

export default function ChatPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isHistoryPanelVisible, setIsHistoryPanelVisible] = useState(false);
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const { sessionId, messages, isLoading, error, sendMessage, clearChat, loadHistory } = useChat();
  const { toast } = useToast();

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
    const fetchHistory = async () => {
      if (!user) return;
      setIsHistoryLoading(true);
      try {
        const sessions = await apiClient.getChatHistory(user.id);
        setHistory(sessions);
      } catch (historyError) {
        console.error('Failed to load chat history:', historyError);
      } finally {
        setIsHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [user, sessionId]);

  const handleNewChat = async () => {
    await clearChat();
    setIsHistoryPanelVisible(false);
  };

  const handleLoadSession = async (sessionIdToLoad: string) => {
    try {
      await loadHistory(sessionIdToLoad);
    } catch (error) {
      console.error('Failed to load session:', error);
      toast({ title: 'Failed to load session', description: error instanceof Error ? error.message : 'Unknown error', variant: 'destructive' });
    }
  };

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
                          {topFiveHistory.map((entry) => (
                            <button
                              key={entry.id}
                              type="button"
                              onClick={() => handleLoadSession(entry.id)}
                              className={`w-full text-left rounded-xl border px-3 py-2 transition-all ${
                                sessionId === entry.id
                                  ? 'border-foreground/20 bg-foreground/10'
                                  : 'border-border/60 bg-background/40 hover:bg-background/70'
                              }`}
                            >
                              <p className="text-xs font-semibold text-foreground line-clamp-2">
                                {entry.title || 'Untitled chat'}
                              </p>
                              <p className="text-[11px] text-muted-foreground mt-1">
                                {formatTimestamp(entry.updated_at || entry.created_at)}
                              </p>
                            </button>
                          ))}

                          {showAllHistory && extraHistory.map((entry) => (
                            <button
                              key={entry.id}
                              type="button"
                              onClick={() => handleLoadSession(entry.id)}
                              className={`w-full text-left rounded-xl border px-3 py-2 transition-all ${
                                sessionId === entry.id
                                  ? 'border-foreground/20 bg-foreground/10'
                                  : 'border-border/60 bg-background/40 hover:bg-background/70'
                              }`}
                            >
                              <p className="text-xs font-semibold text-foreground line-clamp-2">
                                {entry.title || 'Untitled chat'}
                              </p>
                              <p className="text-[11px] text-muted-foreground mt-1">
                                {formatTimestamp(entry.updated_at || entry.created_at)}
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
                      disabled={extraHistory.length === 0}
                    >
                      {extraHistory.length === 0
                        ? 'All chats shown'
                        : showAllHistory
                          ? 'Show less'
                          : `Show more (${extraHistory.length})`}
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
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
