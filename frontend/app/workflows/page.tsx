'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, BarChart3, FileText, Play, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PageShell, SectionPanel } from '@/components/layout/PageShell';
import { LoadingState } from '@/components/ui/loading-state';
import { useAuthStore } from '@/lib/store';

const workflows = [
  {
    title: 'Data Storyteller',
    status: 'Analysis agent',
    description:
      'Upload CSV or Excel data, ask a business question, and generate an analysis report with charts and slide-ready narrative.',
    href: '/analysis',
    cta: 'Start analysis',
    icon: BarChart3,
    meta: ['CSV/XLSX ingestion', 'Agent decomposition', 'Report generation'],
  },
  {
    title: 'Auto-Tailor Resume',
    status: 'Human review loop',
    description:
      'Tailor a master resume to a target job description with ATS scoring, gap review, diff inspection, and final PDF generation.',
    href: '/workflows/auto-tailor',
    cta: 'Start tailoring',
    icon: FileText,
    meta: ['Resume selection', 'Critic feedback', 'Approve or refine'],
  },
];

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
      <PageShell maxWidth="5xl">
        <LoadingState
          title="Loading workflows"
          description="Checking your session before opening the workflow hub."
          className="mx-auto mt-16 max-w-xl"
        />
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Agents & Workflows"
      eyebrow="Automation"
      description="Focused launch points for long-running AI workflows. Each workflow now has clearer status, simpler layout, and explicit progress feedback."
      maxWidth="6xl"
    >
      <div className="grid gap-5 md:grid-cols-2">
        {workflows.map((workflow) => (
          <SectionPanel key={workflow.href} className="flex min-h-[320px] flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-muted">
                    <workflow.icon className="h-5 w-5 text-foreground" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold tracking-tight">{workflow.title}</h2>
                    <p className="text-xs text-muted-foreground">{workflow.status}</p>
                  </div>
                </div>
                <Sparkles className="h-4 w-4 text-muted-foreground" />
              </div>

              <p className="text-sm leading-6 text-muted-foreground">{workflow.description}</p>

              <div className="grid gap-2">
                {workflow.meta.map((item) => (
                  <div key={item} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="h-1.5 w-1.5 rounded-full bg-foreground/50" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
              <Button variant="outline" size="sm" onClick={() => router.push(workflow.href)}>
                Details
              </Button>
              <Button onClick={() => router.push(workflow.href)} className="gap-2">
                {workflow.href.includes('auto-tailor') ? <Play className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
                {workflow.cta}
              </Button>
            </div>
          </SectionPanel>
        ))}
      </div>
    </PageShell>
  );
}
