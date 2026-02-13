'use client';

import { Bell, User, LogOut, Sun, Moon, PanelLeftOpen, PanelLeftClose, Palette, Compass, Waves, Flame, Hexagon, Leaf, Crown, Sunset, Contrast } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useAppTheme } from "@/hooks/useAppTheme";
import { type ThemePalette } from "@/lib/theme";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
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
  const pathname = usePathname();
  const isAuraSql = pathname?.startsWith('/aurasql');
  const isResume = pathname?.startsWith('/nexus');
  const isResumeGen = pathname?.startsWith('/nexus/generate');
  const brandTitle = isAuraSql ? 'AuraSQL' : isResumeGen ? 'ResumeGen' : isResume ? 'Nexus' : 'NexusMind';
  const brandSubtitle = isAuraSql ? 'SQL Studio' : isResumeGen ? 'PDF Builder' : isResume ? 'Resume Studio' : 'Studio';
  const brandMark = isAuraSql ? 'AS' : isResumeGen ? 'RG' : isResume ? 'RS' : 'NX';
  const mainNavLinks = [
    { label: 'Dashboard', href: '/', isActive: pathname === '/' },
    { label: 'RAG', href: '/chat', isActive: pathname?.startsWith('/chat') },
    { label: 'AuraSQL', href: '/aurasql', isActive: pathname?.startsWith('/aurasql') },
    { label: 'Resume', href: '/nexus', isActive: pathname?.startsWith('/nexus') && !pathname?.startsWith('/nexus/generate') },
    { label: 'ResumeGen', href: '/nexus/generate', isActive: pathname?.startsWith('/nexus/generate') },
    { label: 'KB', href: '/knowledge-base', isActive: pathname?.startsWith('/knowledge-base') },
    { label: 'Dev', href: '/developer', isActive: pathname?.startsWith('/developer') },
  ];
  const [llmHealthy, setLlmHealthy] = useState(true);
  const { mode, palette, setPalette, toggleMode } = useAppTheme();
  const paletteOptions: Array<{ value: ThemePalette; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { value: 'nexus', label: 'Nexus Slate', icon: Compass },
    { value: 'ocean', label: 'Arctic Cyan', icon: Waves },
    { value: 'ember', label: 'Solar Ember', icon: Flame },
    { value: 'graphite', label: 'Graphite Mint', icon: Hexagon },
    { value: 'forest', label: 'Verdant Core', icon: Leaf },
    { value: 'royal', label: 'Royal Flux', icon: Crown },
    { value: 'sunset', label: 'Amber Dusk', icon: Sunset },
    { value: 'mono', label: 'Mono Steel', icon: Contrast },
  ];

  useEffect(() => {
    // Listen for custom events from chat component about LLM health.
    // Navigation status intentionally reflects live LLM/chat outcome only
    // (not backend ping health such as BM25 index warmup state).
    const handleLlmHealth = (event: Event) => {
      if (event instanceof CustomEvent && typeof event.detail?.healthy === 'boolean') {
        setLlmHealthy(event.detail.healthy);
      }
    };
    window.addEventListener('llm-health-update', handleLlmHealth);

    return () => {
      window.removeEventListener('llm-health-update', handleLlmHealth);
    };
  }, []);

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
          <span className="text-primary-foreground font-black text-sm tracking-[0.2em]">{brandMark}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-black tracking-tight text-foreground">{brandTitle}</span>
          <span className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            {brandSubtitle}
          </span>
        </div>
        <div className="hidden lg:flex items-center gap-2 ml-6 whitespace-nowrap">
          {mainNavLinks.map((link) => (
            <Button
              key={link.href}
              variant="ghost"
              size="sm"
              className={`text-xs uppercase tracking-[0.2em] min-w-[84px] ${
                link.isActive
                  ? 'bg-foreground/10 text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => router.push(link.href)}
            >
              {link.label}
            </Button>
          ))}
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 mr-2">
          <div
            className={`h-2 w-2 rounded-full transition-all ${
              llmHealthy
                ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse'
                : 'bg-red-400 shadow-sm shadow-red-400/50'
            }`}
            title={llmHealthy ? 'LLM healthy' : 'LLM unhealthy'}
          />
        </div>
        
        <Button 
          variant="ghost" 
          size="icon" 
          className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
        >
          <Bell className="h-5 w-5" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
              aria-label="Theme options"
              title="Theme options"
            >
              <Palette className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-background/95 border-border/70 backdrop-blur-xl w-56">
            <DropdownMenuLabel>Theme</DropdownMenuLabel>
            <DropdownMenuItem onClick={toggleMode} className="cursor-pointer">
              {mode === 'dark' ? <Sun className="mr-2 h-4 w-4" /> : <Moon className="mr-2 h-4 w-4" />}
              {mode === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-border/60" />
            <DropdownMenuLabel>Palette</DropdownMenuLabel>
            <DropdownMenuRadioGroup value={palette} onValueChange={(value) => setPalette(value as ThemePalette)}>
              {paletteOptions.map((item) => (
                <DropdownMenuRadioItem key={item.value} value={item.value}>
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        
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
