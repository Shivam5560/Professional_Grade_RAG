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
});
