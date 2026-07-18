"use client";

import { useState } from "react";
import { Check, FileCheck2, Loader2, Send, ShieldCheck, Sparkles, X } from "lucide-react";

import { ResumeIntake } from "./ResumeIntake";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { careerStudioClient, type CareerClaimRevisionWire, type CareerDraftWorkflowResponseWire } from "@/lib/studios/career/client";
import type { ResumeFileInfo } from "@/lib/types";

type BusyAction = "review" | "tailor" | "approve" | "revise" | "abort" | "publish" | string;

export function TailorWorkspace({ initialJobDescription = "", initialResumeId = "", resumes }: { initialJobDescription?: string; initialResumeId?: string; resumes: ResumeFileInfo[] }): JSX.Element {
  const [resumeId, setResumeId] = useState(initialResumeId || resumes[0]?.resume_id || "");
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState(initialJobDescription);
  const [sourceId, setSourceId] = useState("");
  const [claims, setClaims] = useState<CareerClaimRevisionWire[]>([]);
  const [result, setResult] = useState<CareerDraftWorkflowResponseWire | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<string | null>(null);
  const [revisionNote, setRevisionNote] = useState("");
  const [published, setPublished] = useState(false);
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const resetReview = () => { setSourceId(""); setClaims([]); setResult(null); setApprovalStatus(null); setPublished(false); };
  const review = async () => {
    setBusy("review"); setError(null);
    try {
      const ingested = file ? await careerStudioClient.uploadResume(file) : await careerStudioClient.ingestStoredResume(resumeId);
      setSourceId(ingested.source.id); setClaims(ingested.claims); setResult(null); setApprovalStatus(null); setPublished(false);
      if (ingested.resume) setResumeId(ingested.resume.resume_id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Resume preparation failed"); }
    finally { setBusy(null); }
  };
  const decideClaim = async (logicalId: string, action: "verify" | "reject") => {
    setBusy(`claim-${logicalId}`); setError(null);
    try {
      const revision = await careerStudioClient.decideClaim(logicalId, action);
      setClaims((items) => items.map((item) => item.logical_claim_id === logicalId ? revision : item));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Evidence review failed"); }
    finally { setBusy(null); }
  };
  const start = async () => {
    setBusy("tailor"); setError(null);
    try { const response = await careerStudioClient.prepareTailoring(sourceId, jobDescription); setResult(response); setApprovalStatus(response.approval.status); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Tailoring failed"); }
    finally { setBusy(null); }
  };
  const decideApproval = async (decision: "approve" | "revise" | "reject") => {
    if (!result) return;
    const action = decision === "reject" ? "abort" : decision;
    setBusy(action); setError(null);
    try {
      const approval = await careerStudioClient.decideApproval(result.approval.id, decision, revisionNote.trim() || undefined);
      setApprovalStatus(approval.status);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Approval update failed"); }
    finally { setBusy(null); }
  };
  const publish = async () => {
    if (!result) return;
    setBusy("publish"); setError(null);
    try { await careerStudioClient.publishDraft(result.draft.id); setPublished(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Publication failed"); }
    finally { setBusy(null); }
  };
  const verifiedCount = claims.filter((item) => item.claim.verification_status === "verified").length;

  return <div className="grid gap-6 xl:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]">
    <section className="rounded-xl border border-border bg-workspace-raised p-5 sm:p-6">
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-muted-foreground">1 · Choose your source</p><h2 className="mt-2 text-xl font-semibold">Tailor deliberately</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">We extract evidence first. You decide what is true before a single tailored line is proposed.</p>
      <label className="mt-6 block text-sm font-medium">Saved resume<select className="mt-2 h-11 w-full rounded-md border border-border bg-workspace-inset px-3" value={file ? "" : resumeId} onChange={(event) => { setResumeId(event.target.value); setFile(null); resetReview(); }}><option value="">Upload a new resume</option>{resumes.map((resume) => <option key={resume.resume_id} value={resume.resume_id}>{resume.filename}</option>)}</select></label>
      <div className="mt-5"><ResumeIntake file={file} onFileChange={(next) => { setFile(next); if (next) setResumeId(""); resetReview(); }} /></div>
      <label className="mt-5 block text-sm font-medium">Target job description<Textarea className="mt-2 min-h-52" value={jobDescription} onChange={(event) => { setJobDescription(event.target.value); setResult(null); }} /></label>
      <Button className="mt-5" disabled={Boolean(busy) || (!resumeId && !file) || jobDescription.trim().length < 10} onClick={review} variant="outline">{busy === "review" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileCheck2 className="mr-2 h-4 w-4" />}Review tailoring plan</Button>
      {error ? <p role="alert" className="mt-4 text-sm text-destructive">{error}</p> : null}
    </section>

    <section className="rounded-xl border border-border bg-workspace-raised p-5 sm:p-6">
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-muted-foreground">2 · Verify, tailor, approve</p><h2 className="mt-2 text-xl font-semibold">Your evidence desk</h2>
      {!sourceId ? <div className="mt-8 border-y border-border py-14 text-center text-sm text-muted-foreground">Review a resume to see the claims that may be used.</div> : <>
        <div className="mt-5 flex items-center justify-between rounded-lg bg-workspace-inset p-3"><span className="text-sm"><strong>{verifiedCount}</strong> of {claims.length} claims verified</span><ShieldCheck className="h-5 w-5 text-muted-foreground" /></div>
        <div className="mt-4 max-h-72 space-y-2 overflow-y-auto pr-1">{claims.map((item) => <article className="rounded-lg border border-border bg-workspace-inset p-3" key={item.logical_claim_id}><p className="text-sm font-medium">{String(item.claim.object.value)}</p><p className="mt-1 text-xs capitalize text-muted-foreground">{item.claim.predicate.replaceAll("-", " ")} · {item.claim.verification_status}</p><div className="mt-3 flex gap-2"><Button disabled={Boolean(busy)} onClick={() => decideClaim(item.logical_claim_id, "verify")} size="sm" variant={item.claim.verification_status === "verified" ? "default" : "outline"}><Check className="mr-1 h-3.5 w-3.5" />Verify</Button><Button disabled={Boolean(busy)} onClick={() => decideClaim(item.logical_claim_id, "reject")} size="sm" variant="ghost"><X className="mr-1 h-3.5 w-3.5" />Reject</Button></div></article>)}</div>
        {!result ? <div className="mt-5 rounded-xl border border-border bg-workspace-inset p-4"><h3 className="font-semibold">Evidence-grounded strategy</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Prioritize verified experience, add only supported keywords, and preserve unmet requirements as honest gaps.</p><Button className="mt-4" disabled={Boolean(busy) || verifiedCount === 0} onClick={start}>{busy === "tailor" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}Start tailoring</Button>{verifiedCount === 0 ? <p className="mt-2 text-xs text-muted-foreground">Verify at least one claim to continue.</p> : null}</div> : <DraftReview result={result} approvalStatus={approvalStatus} revisionNote={revisionNote} setRevisionNote={setRevisionNote} busy={busy} published={published} decideApproval={decideApproval} publish={publish} />}
      </>}
    </section>
  </div>;
}

function DraftReview({ result, approvalStatus, revisionNote, setRevisionNote, busy, published, decideApproval, publish }: { result: CareerDraftWorkflowResponseWire; approvalStatus: string | null; revisionNote: string; setRevisionNote(value: string): void; busy: BusyAction | null; published: boolean; decideApproval(decision: "approve" | "revise" | "reject"): void; publish(): void }) {
  return <div className="mt-5 space-y-4"><div className="rounded-xl border border-border bg-workspace-inset p-4"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">Proposed revision</h3><span className="rounded-full border border-border px-2 py-1 text-xs capitalize">{approvalStatus?.replace("_", " ")}</span></div><div className="mt-4 space-y-4">{result.draft.bullets.map((bullet, index) => <div className="border-l-2 border-foreground/25 pl-3" key={index}><p className="text-xs font-semibold uppercase text-muted-foreground">Before</p><p className="mt-1 text-sm text-muted-foreground">{bullet.before_text.join(" ") || "New evidence-backed bullet"}</p><p className="mt-3 text-xs font-semibold uppercase text-muted-foreground">After</p><p className="mt-1 text-sm font-medium">{bullet.after_text}</p></div>)}</div>{result.match.unmatched_requirements.length ? <div className="mt-5 border-t border-border pt-4"><p className="text-xs font-semibold uppercase text-muted-foreground">Truthful gaps</p><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{result.match.unmatched_requirements.map((item) => <li key={item.id}>{item.description}</li>)}</ul></div> : null}</div>
    {approvalStatus === "pending" ? <><Textarea aria-label="Revision note" placeholder="Optional: explain what you want changed" value={revisionNote} onChange={(event) => setRevisionNote(event.target.value)} /><div className="flex flex-wrap gap-2"><Button disabled={Boolean(busy)} onClick={() => decideApproval("approve")}><Check className="mr-2 h-4 w-4" />Approve</Button><Button disabled={Boolean(busy)} onClick={() => decideApproval("revise")} variant="outline">Request changes</Button><Button disabled={Boolean(busy)} onClick={() => decideApproval("reject")} variant="ghost">Abort</Button></div></> : null}
    {approvalStatus === "approved" && !published ? <Button disabled={Boolean(busy)} onClick={publish}>{busy === "publish" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}Publish approved draft</Button> : null}
    {published ? <p className="flex items-center gap-2 rounded-lg border border-border bg-workspace-inset p-3 text-sm font-medium"><Check className="h-4 w-4" />Approved draft published.</p> : null}
  </div>;
}
