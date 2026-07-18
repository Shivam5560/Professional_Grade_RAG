"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, BookOpen } from "lucide-react";

import AuthPage from "@/app/auth/page";
import { PageShell } from "@/components/layout/PageShell";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { Inspector } from "@/components/shell/Inspector";
import { CareerHome, type CareerWorkflow } from "@/components/studios/career/CareerHome";
import { ResumeCreator } from "@/components/studios/career/ResumeCreator";
import { ScoreWorkspace } from "@/components/studios/career/ScoreWorkspace";
import { TailorWorkspace } from "@/components/studios/career/TailorWorkspace";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import type { ResumeFileInfo } from "@/lib/types";

const workflowCopy: Record<CareerWorkflow, { title: string; description: string }> = {
  score: {
    title: "Score Resume",
    description: "Understand compatibility, evidence, keywords, and truthful gaps without changing your resume.",
  },
  tailor: {
    title: "Tailor Resume",
    description: "Review the evidence-grounded strategy first, then explicitly start a role-specific revision.",
  },
  create: {
    title: "Create Resume",
    description: "Build your complete professional story and export it through the existing LaTeX-to-PDF engine.",
  },
};

export default function CareerStudioPage(): JSX.Element | null {
  const { isAuthenticated, user } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [workflow, setWorkflow] = useState<CareerWorkflow | null>(null);
  const [resumes, setResumes] = useState<ResumeFileInfo[]>([]);
  const [resumeLoadError, setResumeLoadError] = useState<string | null>(null);
  const [tailorContext, setTailorContext] = useState({ resumeId: "", jobDescription: "" });
  const [guideOpen, setGuideOpen] = useState(false);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("workflow");
    if (requested === "score" || requested === "tailor" || requested === "create") setWorkflow(requested);
    setMounted(true);
  }, []);
  useEffect(() => {
    if (!user) return;
    apiClient.listResumes(user.id)
      .then((result) => setResumes(result.list))
      .catch((reason) => setResumeLoadError(reason instanceof Error ? reason.message : "Saved resumes could not be loaded"));
  }, [user]);

  if (!mounted) return null;
  if (!isAuthenticated || !user) return <AuthPage />;

  const selectWorkflow = (next: CareerWorkflow | null) => {
    setWorkflow(next);
    window.history.replaceState(null, "", next ? `/career?workflow=${next}` : "/career");
  };
  const activeCopy = workflow ? workflowCopy[workflow] : null;
  return (
    <PageShell
      actions={<><Button onClick={() => setGuideOpen(true)} size="sm" variant="outline"><BookOpen className="mr-2 h-4 w-4" />How it works</Button>{workflow ? <Button onClick={() => selectWorkflow(null)} size="sm" variant="outline"><ArrowLeft className="mr-2 h-4 w-4" />All career tools</Button> : null}</>}
      description={activeCopy?.description ?? "Choose the outcome you need today. Scoring never edits, tailoring only starts when you ask, and creation exports through your LaTeX pipeline."}
      eyebrow="Career Studio"
      maxWidth="full"
      title={activeCopy?.title ?? "Turn experience into your next opportunity"}
    >
      <ContextRibbon label="Your journey">
        <span className="rounded-md bg-workspace-inset px-3 py-1.5 text-xs font-medium">Evidence first</span>
        <span className="text-xs text-muted-foreground">→</span>
        <span className="rounded-md bg-workspace-inset px-3 py-1.5 text-xs font-medium">You choose the action</span>
        <span className="text-xs text-muted-foreground">→</span>
        <span className="rounded-md bg-workspace-inset px-3 py-1.5 text-xs font-medium">Review before export</span>
      </ContextRibbon>

      {resumeLoadError ? <p role="status" className="mt-5 rounded-lg border border-border bg-workspace-inset p-3 text-sm text-muted-foreground">Saved resumes are temporarily unavailable: {resumeLoadError}. You can still upload or create a resume.</p> : null}
      <main className="py-7 sm:py-10">
        {!workflow ? <CareerHome onSelect={selectWorkflow} /> : null}
        {workflow === "score" ? <ScoreWorkspace resumes={resumes} userId={user.id} onTailor={(resumeId, jobDescription) => { setTailorContext({ resumeId, jobDescription }); selectWorkflow("tailor"); }} /> : null}
        {workflow === "tailor" ? <TailorWorkspace initialJobDescription={tailorContext.jobDescription} initialResumeId={tailorContext.resumeId} resumes={resumes} /> : null}
        {workflow === "create" ? <ResumeCreator /> : null}
      </main>
      <Inspector open={guideOpen} onOpenChange={setGuideOpen} title="How Career Studio protects your story">
        <div className="space-y-6 text-sm leading-6">
          <section><p className="text-xs font-semibold uppercase text-muted-foreground">Score</p><h2 className="mt-1 text-lg font-semibold">See the gap before changing anything</h2><p className="mt-2 text-muted-foreground">Scoring evaluates ATS compatibility and role evidence. It does not edit your uploaded resume.</p></section>
          <section><p className="text-xs font-semibold uppercase text-muted-foreground">Tailor</p><h2 className="mt-1 text-lg font-semibold">You remain in control</h2><p className="mt-2 text-muted-foreground">Tailoring begins only after you choose it, review the strategy, and press Start tailoring. Unsupported claims remain visible as gaps.</p></section>
          <section><p className="text-xs font-semibold uppercase text-muted-foreground">Create</p><h2 className="mt-1 text-lg font-semibold">From complete details to a polished PDF</h2><p className="mt-2 text-muted-foreground">The creator saves your progress locally, gives you a formatted preview, and uses the existing LaTeX engine for PDF and source export.</p></section>
        </div>
      </Inspector>
    </PageShell>
  );
}
