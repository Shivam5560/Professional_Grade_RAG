"use client";

import { useState } from "react";
import { Loader2, RefreshCw, ShieldCheck } from "lucide-react";

import { ResumeIntake } from "./ResumeIntake";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { careerStudioClient } from "@/lib/studios/career/client";
import type { ResumeAnalyzeResponse, ResumeFileInfo } from "@/lib/types";

export function ScoreWorkspace({ onTailor, resumes, userId }: { onTailor(resumeId: string, jobDescription: string): void; resumes: ResumeFileInfo[]; userId: number }): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState(resumes[0]?.resume_id ?? "");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [latest, setLatest] = useState<ResumeAnalyzeResponse | null>(null);

  const runScore = async () => {
    if (jobDescription.trim().length < 10 || (!resumeId && !file)) return;
    setLoading(true); setError(null); setMessage(null);
    try {
      if (file) {
        const evidence = await careerStudioClient.uploadResume(file);
        if (!evidence.resume) throw new Error("The resume was extracted but could not be stored for scoring");
        const result = await careerStudioClient.scoreResume(evidence.resume.resume_id, jobDescription);
        setResumeId(evidence.resume.resume_id);
        setLatest(result);
        setMessage(`${evidence.claims.length} evidence claims extracted. Review uncertain evidence before using it for tailoring.`);
      } else {
        const result = await careerStudioClient.scoreResume(resumeId, jobDescription);
        setLatest(result);
        setMessage("Scoring is complete. Your original resume has not been changed.");
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not start resume scoring"); }
    finally { setLoading(false); }
  };
  const refresh = async () => {
    setLoading(true); setError(null);
    try { const history = await apiClient.getResumeHistory(userId); setLatest(history.list[0] ?? null); if (!history.list.length) setMessage("No completed score yet. Processing may still be running."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load score results"); }
    finally { setLoading(false); }
  };

  return <div className="grid gap-6 lg:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]"><section className="rounded-xl border border-border bg-workspace-raised p-5 sm:p-6"><h2 className="text-xl font-semibold">Score without changing your resume</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Choose an existing resume or upload a new one, then add the job description you want to evaluate.</p>{resumes.length ? <label className="mt-6 block text-sm font-medium">Saved resume<select className="mt-2 h-11 w-full rounded-md border border-border bg-workspace-inset px-3" value={resumeId} onChange={(e) => { setResumeId(e.target.value); setFile(null); }}><option value="">Upload a new resume</option>{resumes.map((resume) => <option key={resume.resume_id} value={resume.resume_id}>{resume.filename}</option>)}</select></label> : null}<div className="mt-5"><ResumeIntake file={file} onFileChange={(next) => { setFile(next); if (next) setResumeId(""); }} /></div><label className="mt-5 block text-sm font-medium">Target job description<Textarea className="mt-2 min-h-48" value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste the complete job description…" /></label><Button className="mt-5" disabled={loading || jobDescription.trim().length < 10 || (!resumeId && !file)} onClick={runScore}>{loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}Run score</Button></section><section className="rounded-xl border border-border bg-workspace-raised p-5 sm:p-6"><div className="flex items-start justify-between gap-4"><div><h2 className="text-xl font-semibold">Compatibility and evidence</h2><p className="mt-2 text-sm text-muted-foreground">ATS compatibility is kept separate from role evidence and truthful gaps.</p></div><Button size="sm" variant="outline" onClick={refresh}><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button></div>{error ? <p role="alert" className="mt-5 text-sm text-destructive">{error}</p> : null}{message ? <p className="mt-5 rounded-lg bg-workspace-inset p-4 text-sm">{message}</p> : null}{latest ? <ScoreResult result={latest} /> : <div className="mt-8 border-y border-border py-10 text-center text-sm text-muted-foreground">Run a score to see compatibility, strengths, keywords, and gaps.</div>}{latest && resumeId ? <Button className="mt-6" onClick={() => onTailor(resumeId, jobDescription)}>Tailor this resume</Button> : null}</section></div>;
}

function ScoreResult({ result }: { result: ResumeAnalyzeResponse }) { const analysis = result.analysis ?? {}; return <div className="mt-6 space-y-4"><div className="grid grid-cols-2 gap-3"><Metric label="Overall score" value={result.overall_score == null ? "—" : `${Math.round(result.overall_score)}%`} /><Metric label="Evidence status" value="Reviewed" /></div><pre className="max-h-96 overflow-auto rounded-lg bg-workspace-inset p-4 text-xs whitespace-pre-wrap">{JSON.stringify(analysis, null, 2)}</pre></div>; }
function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg border border-border p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></div>; }
