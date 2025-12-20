import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Plus, Settings, HelpCircle, Sparkles, RefreshCw } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { useEffect, useState, useCallback } from "react";
import { apiClient } from "@/lib/api";
import { ChatSession } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SidebarProps {
  onNewChat: () => void;
  onLoadSession?: (sessionId: string) => void;
  currentSessionId?: string;
}

export function Sidebar({ onNewChat, onLoadSession, currentSessionId }: SidebarProps) {
  const { user } = useAuthStore();
  const [history, setHistory] = useState<ChatSession[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

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

  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-800/50 bg-slate-900/50 backdrop-blur-xl">
      <div className="p-4">
        <Button 
          onClick={onNewChat} 
          className="w-full justify-start gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/30 h-11 font-semibold" 
        >
          <Plus className="h-5 w-5" />
          <span>New Chat</span>
          <Sparkles className="h-4 w-4 ml-auto" />
        </Button>
      </div>
      
      <div className="px-4 py-2 flex-1 overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Recent Conversations
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/50"
            onClick={loadHistory}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <ScrollArea className="h-full pr-2">
          <div className="space-y-2">
            {user ? (
              history.length > 0 ? (
                history.map((session) => (
                  <button 
                    key={session.id}
                    onClick={() => handleSessionClick(session.id)}
                    className={cn(
                      "w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group relative overflow-hidden",
                      currentSessionId === session.id 
                        ? 'bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 shadow-lg shadow-cyan-500/10' 
                        : 'hover:bg-slate-800/50 border border-transparent hover:border-slate-700/50'
                    )}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className={cn(
                        "h-4 w-4 mt-0.5 flex-shrink-0 transition-colors",
                        currentSessionId === session.id ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className={cn(
                          "text-sm font-medium truncate transition-colors",
                          currentSessionId === session.id ? 'text-white' : 'text-slate-300 group-hover:text-white'
                        )}>
                          {session.title || 'New Conversation'}
                        </p>
                        {session.created_at && (
                          <p className="text-xs text-slate-500 mt-0.5">
                            {new Date(session.created_at).toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        )}
                      </div>
                    </div>
                    {currentSessionId === session.id && (
                      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-blue-500/5 pointer-events-none" />
                    )}
                  </button>
                ))
              ) : (
                <div className="px-2 py-8 text-center text-xs text-slate-500">
                  {isRefreshing ? 'Loading...' : 'No chat history yet. Start a new conversation!'}
                </div>
              )
            ) : (
              <div className="px-2 py-8 text-center text-xs text-slate-500">
                Login to view history
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      <div className="mt-auto p-4 border-t border-slate-800/50">
        <div className="space-y-1">
          <Button variant="ghost" className="w-full justify-start gap-2 text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Button variant="ghost" className="w-full justify-start gap-2 text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all">
            <HelpCircle className="h-4 w-4" />
            Help & Support
          </Button>
        </div>
      </div>
    </div>
  );
}
