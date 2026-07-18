"use client";

import { useEffect, useState } from "react";
import { History, MessageSquarePlus, Sparkles } from "lucide-react";
import { useSearchParams } from "next/navigation";

import AuthPage from "@/app/auth/page";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { Sidebar } from "@/components/layout/Sidebar";
import { CanvasHeader } from "@/components/shell/CanvasHeader";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { FocusCanvas } from "@/components/shell/FocusCanvas";
import { Inspector } from "@/components/shell/Inspector";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/useChat";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const { isAuthenticated, user } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const {
    sessionId,
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    hydrateConversation,
    latestTokenUsage,
  } = useChat();
  const { toast } = useToast();

  useEffect(() => setIsMounted(true), []);

  useEffect(() => {
    if (searchParams.get("panel") === "history") setHistoryOpen(true);
  }, [searchParams]);

  useEffect(() => {
    const loadActiveConversation = async () => {
      if (!user) return;
      try {
        const bootstrap = await apiClient.getChatBootstrap();
        if (bootstrap.active_session_id) {
          hydrateConversation(bootstrap.active_session_id, bootstrap.messages);
        }
      } catch (bootstrapError) {
        console.error("Failed to load active Knowledge conversation:", bootstrapError);
      }
    };

    loadActiveConversation();
  }, [hydrateConversation, user]);

  const handleNewChat = async () => {
    await clearChat();
    setHistoryOpen(false);
  };

  const handleLoadSession = async (sessionIdToLoad: string) => {
    try {
      const bootstrap = await apiClient.getChatBootstrap(sessionIdToLoad);
      if (bootstrap.active_session_id) {
        hydrateConversation(bootstrap.active_session_id, bootstrap.messages);
      }
      setHistoryOpen(false);
    } catch (loadError) {
      toast({
        title: "Failed to load session",
        description: loadError instanceof Error ? loadError.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <FocusCanvas ariaLabel="Knowledge Studio conversation" className="min-h-0">
      <CanvasHeader
        actions={
          <>
            <Button onClick={() => setHistoryOpen(true)} size="sm" variant="outline">
              <History className="mr-2 h-4 w-4" />
              History
            </Button>
            <Button onClick={handleNewChat} size="sm">
              <MessageSquarePlus className="mr-2 h-4 w-4" />
              New chat
            </Button>
          </>
        }
        description="Ask across your evidence. Sources and confidence stay attached to every answer."
        eyebrow="Knowledge Studio"
        status={
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Ready
          </span>
        }
        title="Conversation"
      />

      <ContextRibbon label="Conversation context">
        <span className="inline-flex h-7 items-center rounded-md border border-border/70 bg-workspace-inset px-2.5 text-xs text-muted-foreground">
          {messages.length} message{messages.length === 1 ? "" : "s"}
        </span>
        <span className="inline-flex h-7 items-center gap-1.5 rounded-md border border-border/70 bg-workspace-inset px-2.5 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          {latestTokenUsage
            ? `${Math.round(latestTokenUsage.context_utilization_pct)}% context used`
            : "Context available"}
        </span>
      </ContextRibbon>

      <section
        aria-label="Active conversation"
        className="mt-4 h-[calc(100svh-15.5rem)] min-h-[32rem] overflow-hidden rounded-lg border border-border/70 bg-workspace-raised shadow-[0_28px_80px_-55px_hsl(var(--foreground)/0.4)] md:h-[calc(100svh-13rem)]"
      >
        <ChatInterface
          error={error}
          isLoading={isLoading}
          messages={messages}
          sendMessage={sendMessage}
          sessionId={sessionId}
          tokenUsage={latestTokenUsage}
        />
      </section>

      <Inspector onOpenChange={setHistoryOpen} open={historyOpen} title="Knowledge history">
        <Sidebar
          currentSessionId={sessionId}
          onLoadSession={handleLoadSession}
          onNewChat={handleNewChat}
        />
      </Inspector>
    </FocusCanvas>
  );
}
