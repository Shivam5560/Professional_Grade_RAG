"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { ResumeIntake } from "./ResumeIntake";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { careerStudioClient } from "@/lib/studios/career/client";
import type { ResumeFileInfo } from "@/lib/types";

export function TailorWorkspace({ initialJobDescription = "", initialResumeId = "", resumes }: { initialJobDescription?: string; initialResumeId?: string; resumes: ResumeFileInfo[] }): JSX.Element {
  const [resumeId, setResumeId] = useState(initialResumeId || resumes[0]?.resume_id || "");
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState(initialJobDescription);
  const [reviewed, setReviewed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidenceMessage, setEvidenceMessage] = useState<string | null>(null);
  const review = async () => {
    setLoading(true); setError(null);
    try {
      if (file) {
        const uploaded = await careerStudioClient.uploadResume(file);
        if (!uploaded.resume) throw new Error("The resume was extracted but could not be stored for tailoring");
        setResumeId(uploaded.resume.resume_id);
        setEvidenceMessage(`${uploaded.claims.length} extracted evidence claims are ready for review.`);
      }
      setReviewed(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Resume preparation failed"); }
    finally { setLoading(false); }
  };
  const start = async () => { setLoading(true); setError(null); try { setResult(await apiClient.startAutoTailor({ resume_id: resumeId, job_description: jobDescription, target_score: 85, max_iterations: 3 })); } catch (reason) { setError(reason instanceof Error ? reason.message : "Tailoring failed"); } finally { setLoading(false); } };
  return <div className="grid gap-6 lg:grid-cols-2"><section className="rounded-xl border border-border bg-workspace-raised p-6"><h2 className="text-xl font-semibold">Tailor deliberately</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Nothing changes until you review the plan and explicitly start tailoring.</p><label className="mt-6 block text-sm font-medium">Saved resume<select className="mt-2 h-11 w-full rounded-md border border-border bg-workspace-inset px-3" value={file ? "" : resumeId} onChange={(e) => { setResumeId(e.target.value); setFile(null); setReviewed(false); }}><option value="">Upload a new resume</option>{resumes.map((resume) => <option key={resume.resume_id} value={resume.resume_id}>{resume.filename}</option>)}</select></label><div className="mt-5"><ResumeIntake file={file} onFileChange={(next) => { setFile(next); if (next) setResumeId(""); setReviewed(false); }} /></div><label className="mt-5 block text-sm font-medium">Target job description<Textarea className="mt-2 min-h-52" value={jobDescription} onChange={(e) => { setJobDescription(e.target.value); setReviewed(false); }} /></label>{evidenceMessage ? <p className="mt-4 rounded-lg bg-workspace-inset p-3 text-xs text-muted-foreground">{evidenceMessage}</p> : null}{!reviewed ? <Button className="mt-5" disabled={loading || (!resumeId && !file) || jobDescription.trim().length < 10} onClick={review} variant="outline">{loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}Review tailoring plan</Button> : <div className="mt-5 rounded-xl border border-border bg-workspace-inset p-4"><h3 className="font-semibold">Proposed strategy</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground"><li>Prioritize verified experience relevant to this role.</li><li>Add keywords only where evidence supports them.</li><li>Keep unsupported requirements visible as truthful gaps.</li><li>Pause for your approval before final publication.</li></ul><Button className="mt-4" disabled={loading} onClick={start}>{loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}Start tailoring</Button></div>}{error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}</section><section className="rounded-xl border border-border bg-workspace-raised p-6"><h2 className="text-xl font-semibold">Revision review</h2><p className="mt-2 text-sm text-muted-foreground">Before/after changes, scores, and critic feedback appear here.</p>{result ? <pre className="mt-5 max-h-[36rem] overflow-auto rounded-lg bg-workspace-inset p-4 text-xs whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre> : <div className="mt-8 border-y border-border py-12 text-center text-sm text-muted-foreground">Start tailoring after reviewing the strategy.</div>}</section></div>;
}
