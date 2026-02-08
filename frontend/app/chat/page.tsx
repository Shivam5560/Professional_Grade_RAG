'use client';

import { useEffect, useState } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { useChat } from '@/hooks/useChat';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function ChatPage() {
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { sessionId, messages, isLoading, error, sendMessage, clearChat, loadHistory } = useChat();

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

  if (!isMounted) {
    return null;
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const handleNewChat = async () => {
    await clearChat();
  };

  const handleLoadSession = async (sessionIdToLoad: string) => {
    try {
      await loadHistory(sessionIdToLoad);
    } catch (error) {
      console.error('Failed to load session:', error);
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
            <Sidebar
              onNewChat={handleNewChat}
              onLoadSession={handleLoadSession}
              currentSessionId={sessionId}
            />
          </div>
        </aside>
        <main className="flex flex-1 flex-col overflow-hidden min-h-0">
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
