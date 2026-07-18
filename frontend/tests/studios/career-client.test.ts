import { CareerStudioClient } from "@/lib/studios/career/client";

describe("CareerStudioClient", () => {
  it("uses claim-level verification and approval endpoints", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify({ claim: { id: "claim-1", status: "verified" } }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ approval: { id: "approval-1", status: "approved" } }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const client = new CareerStudioClient({ fetcher, getAccessToken: () => "career-token" });

    await client.verifyClaim("claim-1");
    await client.decideApproval("approval-1", "approve", "Checked against source");

    expect(fetcher.mock.calls[0][0]).toBe("http://localhost:8000/api/v2/career/claims/claim-1/decisions");
    expect(fetcher.mock.calls[1][0]).toBe("http://localhost:8000/api/v2/career/approvals/approval-1/decisions");
    expect(fetcher.mock.calls[1][1]).toEqual(expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ decision: "approve", comment: "Checked against source" }),
      headers: expect.objectContaining({ Authorization: "Bearer career-token" }),
    }));
  });

  it("uses the owner-scoped Career facade for upload and scoring", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify({ source: {}, claims: [], resume: { resume_id: "resume-1" } }), { status: 201, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ analysis_id: "analysis-1", resume_id: "resume-1", overall_score: 82, analysis: {}, created_at: "" }), { status: 201, headers: { "Content-Type": "application/json" } }));
    const client = new CareerStudioClient({ fetcher, getAccessToken: () => "career-token" });

    const uploaded = await client.uploadResume(new File(["resume"], "resume.txt", { type: "text/plain" }));
    await client.scoreResume(uploaded.resume!.resume_id, "A detailed data engineering job description");

    expect(fetcher.mock.calls[0][0]).toBe("http://localhost:8000/api/v2/career/sources/upload");
    expect(fetcher.mock.calls[1][0]).toBe("http://localhost:8000/api/v2/career/scores");
    expect(fetcher.mock.calls[1][1]).toEqual(expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ resume_id: "resume-1", job_description: "A detailed data engineering job description" }),
    }));
  });

  it("prepares tailoring through the reviewed Career workflow", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify({ source: { id: "source-1" }, claims: [] }), { status: 201, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ draft: { id: "draft-1" }, approval: { id: "approval-1" } }), { status: 201, headers: { "Content-Type": "application/json" } }));
    const client = new CareerStudioClient({ fetcher });

    await client.ingestStoredResume("resume-1");
    await client.prepareTailoring("source-1", "A detailed platform engineering role");

    expect(fetcher.mock.calls[0][0]).toBe("http://localhost:8000/api/v2/career/sources/resumes/resume-1");
    expect(fetcher.mock.calls[1][0]).toBe("http://localhost:8000/api/v2/career/tailoring/prepare");
    expect(fetcher.mock.calls[1][1]).toEqual(expect.objectContaining({ body: JSON.stringify({ source_id: "source-1", job_description: "A detailed platform engineering role" }) }));
  });
});
