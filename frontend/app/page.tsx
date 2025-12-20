'use client';

import { useEffect, useState } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { useChat } from '@/hooks/useChat';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const { sessionId, messages, isLoading, error, sendMessage, clearChat, loadHistory } = useChat();
  
  useEffect(() => {
    setIsMounted(true);
  }, []);

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
    // Load the chat history for the clicked session
    try {
      await loadHistory(sessionIdToLoad);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 dark relative overflow-hidden">
      {/* Ambient Background Effects - Cyberpunk Theme */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] rounded-full bg-cyan-500/10 blur-[120px] animate-pulse" />
        <div className="absolute top-[40%] -right-[10%] w-[60%] h-[60%] rounded-full bg-purple-500/10 blur-[120px] animate-pulse" style={{animationDelay: '1s'}} />
        <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] rounded-full bg-blue-500/8 blur-[100px] animate-pulse" style={{animationDelay: '2s'}} />
        
        {/* Grid Pattern Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      </div>

      <Header />
      <div className="flex flex-1 overflow-hidden relative z-10">
        <aside className="hidden md:block">
          <Sidebar 
            onNewChat={handleNewChat} 
            onLoadSession={handleLoadSession}
            currentSessionId={sessionId}
          />
        </aside>
        <main className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-hidden p-4 md:p-6">
            <ChatInterface 
              sessionId={sessionId}
              messages={messages}
              isLoading={isLoading}
              error={error}
              sendMessage={sendMessage}
            />
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}
