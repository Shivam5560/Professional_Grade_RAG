'use client';

import { Brain, Bell, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import type { PingResponse } from "@/lib/types";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [lastPingStatus, setLastPingStatus] = useState<PingResponse | null>(null);
  const [llmHealthy, setLlmHealthy] = useState(true); // Default LLM to healthy, updated by actual requests

  // Poll services (excluding LLM health check) every 60 seconds
  useEffect(() => {
    const pingServices = async () => {
      try {
        const pingResult = await apiClient.pingServices();
        // Update services but override LLM status with our tracked status
        setLastPingStatus({
          ...pingResult,
          services: {
            ...pingResult.services,
            llm: {
              type: pingResult.services.llm?.type || 'groq',
              status: llmHealthy ? 'healthy' : 'unhealthy',
              model: pingResult.services.llm?.model
            }
          }
        });
      } catch (err) {
        console.warn('[Header] Failed to ping services:', err);
        setLastPingStatus({
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          services: {
            embedding: { type: 'unknown', status: 'unhealthy' },
            reranker: { type: 'unknown', status: 'unhealthy' },
            llm: { type: 'unknown', status: llmHealthy ? 'healthy' : 'unhealthy' },
            database: { type: 'unknown', status: 'unhealthy' },
            bm25: { type: 'unknown', status: 'unhealthy' }
          },
          summary: { total: 5, healthy: 0, unhealthy: 5 }
        });
      }
    };

    // Initial ping
    pingServices();

    // Poll every 60 seconds
    const pingInterval = setInterval(pingServices, 60 * 1000);

    // Listen for custom events from chat component about LLM health
    const handleLlmHealth = (event: any) => {
      setLlmHealthy(event.detail.healthy);
    };
    window.addEventListener('llm-health-update', handleLlmHealth);

    return () => {
      clearInterval(pingInterval);
      window.removeEventListener('llm-health-update', handleLlmHealth);
    };
  }, [llmHealthy]);

  const handleLogout = () => {
    logout();
    router.push("/auth");
  };

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl px-6 shadow-lg shadow-cyan-500/5">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30 ring-2 ring-cyan-500/20">
          <Brain className="h-6 w-6 text-white" />
        </div>
        <span className="text-xl font-black tracking-tight bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
          NexusMind RAG
        </span>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Service Status Badges */}
        {lastPingStatus && (
          <div className="flex items-center gap-1.5 mr-2">
            {lastPingStatus.services.embedding && (
              <div className={`h-2 w-2 rounded-full transition-all ${
                lastPingStatus.services.embedding.status === 'healthy' 
                  ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse' 
                  : 'bg-red-400 shadow-sm shadow-red-400/50'
              }`} title="Embedding Service" />
            )}
            {lastPingStatus.services.reranker && (
              <div className={`h-2 w-2 rounded-full transition-all ${
                lastPingStatus.services.reranker.status === 'healthy' 
                  ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse' 
                  : 'bg-red-400 shadow-sm shadow-red-400/50'
              }`} title="Reranker Service" />
            )}
            {lastPingStatus.services.llm && (
              <div className={`h-2 w-2 rounded-full transition-all ${
                lastPingStatus.services.llm.status === 'healthy' 
                  ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse' 
                  : 'bg-red-400 shadow-sm shadow-red-400/50'
              }`} title="LLM Service" />
            )}
            {lastPingStatus.services.database && (
              <div className={`h-2 w-2 rounded-full transition-all ${
                lastPingStatus.services.database.status === 'healthy' 
                  ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse' 
                  : 'bg-red-400 shadow-sm shadow-red-400/50'
              }`} title="Database" />
            )}
            {lastPingStatus.services.bm25 && (
              <div className={`h-2 w-2 rounded-full transition-all ${
                lastPingStatus.services.bm25.status === 'healthy' 
                  ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse' 
                  : 'bg-red-400 shadow-sm shadow-red-400/50'
              }`} title="BM25 Service" />
            )}
          </div>
        )}
        
        <Button 
          variant="ghost" 
          size="icon" 
          className="text-slate-400 hover:text-cyan-400 hover:bg-slate-800/50 transition-all"
        >
          <Bell className="h-5 w-5" />
        </Button>
        
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="icon" 
                className="rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/30"
              >
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-slate-900/95 border-slate-800/50 backdrop-blur-xl">
              <DropdownMenuLabel className="text-white">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-slate-800/50" />
              <DropdownMenuItem className="text-xs text-slate-400 focus:text-white focus:bg-slate-800/50">
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-slate-800/50" />
              <DropdownMenuItem 
                onClick={handleLogout} 
                className="text-red-400 focus:text-red-300 focus:bg-red-500/10"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button onClick={() => router.push("/auth")} className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/30">
            Login
          </Button>
        )}
      </div>
    </header>
  );
}
