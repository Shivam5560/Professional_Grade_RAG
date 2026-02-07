import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Plus, Settings, HelpCircle, Sparkles, RefreshCw, Database } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { useEffect, useState, useCallback, useMemo } from "react";
import { apiClient } from "@/lib/api";
import { ChatSession } from "@/lib/types";
import { cn, formatTimestamp } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface SidebarProps {
  onNewChat: () => void;
  onLoadSession?: (sessionId: string) => void;
  currentSessionId?: string;
}

export function Sidebar({ onNewChat, onLoadSession, currentSessionId }: SidebarProps) {
  const { user } = useAuthStore();
  const router = useRouter();
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const loadHistory = useCallback(async () => {
    if (user) {
      setIsRefreshing(true);
      try {
        const sessions = await apiClient.getChatHistory(user.id);
        setHistory(sessions);
        setHasLoadedOnce(true);
      } catch (error) {
        console.error("Failed to load chat history:", error);
      } finally {
        setIsRefreshing(false);
      }
    } else {
      setHistory([]);
      setHasLoadedOnce(false);
    }
  }, [user]);

  // Only load on mount if user is logged in
  useEffect(() => {
    if (user && !hasLoadedOnce) {
      loadHistory();
    }
  }, [user, hasLoadedOnce, loadHistory]);

  const handleSessionClick = async (sessionId: string) => {
    if (onLoadSession) {
      onLoadSession(sessionId);
    }
  };

  const sortedHistory = useMemo(() => {
    return [...history].sort((a, b) => {
      const aTime = new Date(a.updated_at || a.created_at).getTime();
      const bTime = new Date(b.updated_at || b.created_at).getTime();
      return bTime - aTime;
    });
  }, [history]);

  const primaryHistory = sortedHistory.slice(0, 6);
  const extraCount = Math.max(sortedHistory.length - primaryHistory.length, 0);

  const formatTitle = (title?: string, fallbackDate?: string) => {
    if (!title) {
      return fallbackDate ? `Untitled chat • ${fallbackDate}` : 'Untitled chat';
    }
    const cleaned = title.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const parsed = new Date(dateString);
    if (Number.isNaN(parsed.getTime())) return '';
    return formatTimestamp(parsed.toISOString());
  };

  const renderSessionList = (sessions: ChatSession[]) => (
    <div className="space-y-2">
      {sessions.map((session) => {
        const displayDate = formatDate(session.updated_at || session.created_at);
        const displayTitle = formatTitle(session.title, displayDate);

        return (
          <div
            key={session.id}
            className={cn(
              "rounded-xl border border-transparent transition-all",
              currentSessionId === session.id
                ? 'border-foreground/10 bg-foreground/5'
                : 'hover:border-border/60 hover:bg-muted/60'
            )}
          >
            <div className="flex items-start gap-3 px-3 py-3">
              <button
                type="button"
                onClick={() => handleSessionClick(session.id)}
                className="flex flex-1 items-start gap-2 text-left"
              >
                <MessageSquare
                  className={cn(
                    "h-4 w-4 mt-0.5 flex-shrink-0 transition-colors",
                    currentSessionId === session.id ? 'text-foreground' : 'text-muted-foreground'
                  )}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground whitespace-normal break-words leading-snug">
                    {displayTitle}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {displayDate}
                  </p>
                </div>
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <>
      <div className="flex h-full w-72 flex-col border-r border-border/60 bg-card/70 backdrop-blur-xl">
      <div className="p-4">
        <Button 
          onClick={onNewChat} 
          className="w-full justify-start gap-2 bg-foreground text-background hover:bg-foreground/90 shadow-lg h-11 font-semibold" 
        >
          <Plus className="h-5 w-5" />
          <span>New Chat</span>
          <Sparkles className="h-4 w-4 ml-auto" />
        </Button>
      </div>
      
      <div className="px-4 py-2 flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Recent Conversations
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-muted-foreground hover:text-foreground hover:bg-muted/60"
            onClick={loadHistory}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <ScrollArea className="flex-1 pr-2">
          <div className="space-y-2">
            {user ? (
              sortedHistory.length > 0 ? (
                <>
                  {renderSessionList(primaryHistory)}
                  {showAll && sortedHistory.length > primaryHistory.length && (
                    <div className="pt-2">
                      <div className="px-2 py-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                        More conversations
                      </div>
                      {renderSessionList(sortedHistory.slice(primaryHistory.length))}
                    </div>
                  )}
                </>
              ) : (
                <div className="px-2 py-8 text-center text-xs text-muted-foreground">
                  {isRefreshing ? 'Loading...' : 'No chat history yet. Start a new conversation!'}
                </div>
              )
            ) : (
              <div className="px-2 py-8 text-center text-xs text-muted-foreground">
                Login to view history
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="pt-3">
          <Button
            variant="ghost"
            className="w-full text-xs text-muted-foreground hover:text-foreground hover:bg-muted/60"
            onClick={() => setShowAll((prev) => !prev)}
            disabled={extraCount === 0}
          >
            {extraCount === 0
              ? 'All chats shown'
              : showAll
                ? 'Show less'
                : `Show more (${extraCount})`}
          </Button>
        </div>
      </div>

      <div className="mt-auto p-4 border-t border-border/60">
        <div className="space-y-1">
          <Button 
            variant="ghost" 
            className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60 rounded-lg transition-all"
            onClick={() => router.push('/knowledge-base')}
          >
            <Database className="h-4 w-4" />
            Knowledge Base
          </Button>
          <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60 rounded-lg transition-all">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/60 rounded-lg transition-all">
            <HelpCircle className="h-4 w-4" />
            Help & Support
          </Button>
        </div>
      </div>
      </div>
    </>
  );
}
