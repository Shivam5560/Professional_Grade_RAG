'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Header } from '@/components/layout/Header';
import { useAuthStore } from '@/lib/store';
import { ShaderAnimation } from '@/components/ui/shader-animation';
import { BarChart3, ArrowRight, Play, Cpu, Sparkles } from 'lucide-react';

export default function WorkflowsHubPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    if (!user) {
      router.push('/auth');
    }
  }, [user, isHydrated, router]);

  if (!isHydrated || !user) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 opacity-35">
          <ShaderAnimation className="w-full h-full" speed={0.08} />
        </div>
        <div className="pointer-events-none absolute inset-0 app-aurora" />
        <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
        <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
        <Header />
        <div className="relative z-10 flex min-h-[calc(100vh-4rem)] items-center justify-center">
          <div className="text-center glass-panel rounded-3xl px-8 py-10">
            <Cpu className="h-8 w-8 animate-spin text-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Loading Workflows Hub...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-35">
        <ShaderAnimation className="w-full h-full" speed={0.08} />
      </div>
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.18),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[12%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl float-slower" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-8">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {/* Header Banner */}
          <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-2xl logo-mark flex items-center justify-center shadow-lg ring-2 ring-foreground/10 pulse-glow">
                <Cpu className="h-6 w-6 text-primary-foreground animate-pulse" />
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-foreground">Agents & Workflows</h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Automate complex procedures using iterative multi-agent LlamaIndex workflows.
                </p>
              </div>
            </div>
          </div>

          {/* Cards Grid */}
          <div className="grid gap-6 md:grid-cols-2">
            
            {/* Card 1: Data Storyteller */}
            <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-card/45 flex flex-col justify-between hover-glow transition-all duration-300 group hover:-translate-y-1">
              <div className="space-y-4">
                <div className="h-12 w-12 rounded-2xl bg-foreground/5 flex items-center justify-center border border-border/50 group-hover:border-primary/40 group-hover:bg-primary/5 transition-colors">
                  <BarChart3 className="h-6 w-6 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
                    <span>Data Storyteller</span>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-foreground/10 text-muted-foreground">Active</span>
                  </h2>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Transform tabular datasets (CSV/Excel) into premium, slide-ready business presentations. 
                    The workflow automatically decomposes tasks, checks context, issues live database queries via text-to-SQL (auraSQL), and generates executive narrative and PowerPoint decks.
                  </p>
                </div>
              </div>
              <div className="mt-8 pt-4 border-t border-border/40 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Rebranded Data Analysis</span>
                <Button 
                  onClick={() => router.push('/analysis')}
                  className="bg-foreground text-background hover:bg-foreground/90 font-semibold group-hover:shadow-lg transition-all gap-1.5"
                >
                  <span>Open Storyteller</span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </div>
            </div>

            {/* Card 2: Auto-Tailor Resume */}
            <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-card/45 flex flex-col justify-between hover-glow transition-all duration-300 group hover:-translate-y-1">
              <div className="space-y-4">
                <div className="h-12 w-12 rounded-2xl bg-foreground/5 flex items-center justify-center border border-border/50 group-hover:border-primary/40 group-hover:bg-primary/5 transition-colors">
                  <Sparkles className="h-6 w-6 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
                    <span>Auto-Tailor Resume</span>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">HITL Enabled</span>
                  </h2>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Iteratively tailors your resume experiences, skills, and projects to match a target Job Description. 
                    Uses computational ATS scoring & gap analysis to guide rewrites, with human-in-the-loop controls to approve drafts or guide refinements.
                  </p>
                </div>
              </div>
              <div className="mt-8 pt-4 border-t border-border/40 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Self-Improving Loop</span>
                <Button 
                  onClick={() => router.push('/workflows/auto-tailor')}
                  className="bg-foreground text-background hover:bg-foreground/90 font-semibold group-hover:shadow-lg transition-all gap-1.5"
                >
                  <span>Start Auto-Tailoring</span>
                  <Play className="h-4 w-4 fill-current transition-transform group-hover:scale-110" />
                </Button>
              </div>
            </div>

          </div>

        </div>
      </main>
    </div>
  );
}
