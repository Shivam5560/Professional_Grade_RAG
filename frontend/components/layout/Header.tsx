'use client';

import { Bell, User, LogOut, Sun, Moon, PanelLeftOpen, PanelLeftClose } from "lucide-react";
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

interface HeaderProps {
  showSidebarToggle?: boolean;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function Header({
  showSidebarToggle = false,
  isSidebarOpen = true,
  onToggleSidebar,
}: HeaderProps) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [lastPingStatus, setLastPingStatus] = useState<PingResponse | null>(null);
  const [llmHealthy, setLlmHealthy] = useState(true); // Default LLM to healthy, updated by actual requests
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const stored = window.localStorage.getItem('theme');
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const nextTheme = stored === 'light' || stored === 'dark' ? stored : preferred;
    setTheme(nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    window.localStorage.setItem('theme', theme);
  }, [theme]);

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
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-border/60 bg-background/80 backdrop-blur-xl px-6 shadow-[0_10px_30px_-20px_rgba(0,0,0,0.35)]">
      <div className="flex items-center gap-3">
        {showSidebarToggle && (
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
            onClick={onToggleSidebar}
            aria-label={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="h-5 w-5" />
            ) : (
              <PanelLeftOpen className="h-5 w-5" />
            )}
          </Button>
        )}
        <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center shadow-lg ring-2 ring-foreground/10 pulse-glow">
          <span className="text-primary-foreground font-black text-sm tracking-[0.2em]">NX</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-black tracking-tight text-foreground">
            NexusMind
          </span>
          <span className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            Studio RAG
          </span>
        </div>
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
          className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
        >
          <Bell className="h-5 w-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>
        
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="icon" 
                className="rounded-full bg-foreground text-background hover:bg-foreground/90 shadow-lg"
              >
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-background/95 border-border/70 backdrop-blur-xl">
              <DropdownMenuLabel className="text-foreground">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border/60" />
              <DropdownMenuItem className="text-xs text-muted-foreground focus:text-foreground focus:bg-muted/60">
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border/60" />
              <DropdownMenuItem 
                onClick={handleLogout} 
                className="text-red-500 focus:text-red-500 focus:bg-red-500/10"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button onClick={() => router.push("/auth")} className="bg-foreground text-background hover:bg-foreground/90 shadow-lg">
            Login
          </Button>
        )}
      </div>
    </header>
  );
}
