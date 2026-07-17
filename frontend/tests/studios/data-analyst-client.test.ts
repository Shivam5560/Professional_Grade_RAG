import { DataAnalystClient } from "@/lib/studios/data-analyst/client";

describe("DataAnalystClient", () => {
  it("uploads an immutable CSV snapshot with the v2 contract", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ snapshot_id: "snapshot-1", profile: { dataset_snapshot_id: "snapshot-1", row_count: 2, column_count: 2, columns: [], warnings: [] } }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new DataAnalystClient({ fetcher, getAccessToken: () => "token-1" });
    const file = new File(["revenue,profit\n10,2\n"], "metrics.csv", { type: "text/csv" });

    await client.createDataset(file);

    expect(fetcher).toHaveBeenCalledWith(
      "http://localhost:8000/api/v2/data-analyst/datasets",
      expect.objectContaining({
        method: "POST",
        body: file,
        headers: expect.objectContaining({
          Authorization: "Bearer token-1",
          "Content-Type": "text/csv",
          "X-Filename": "metrics.csv",
        }),
      }),
    );
  });

  it("starts and cancels a run with idempotency", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify({ run: { id: "run-1", state: "queued", progress: 0 }, run_history: [] }), { status: 201, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ run: { id: "run-1", state: "cancelled", progress: 0 } }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const client = new DataAnalystClient({ fetcher, getAccessToken: () => null });

    await client.createRun({ snapshot_id: "snapshot-1", question: "What drives profit?" }, "request-7");
    await client.cancelRun("run-1");

    expect(fetcher.mock.calls[0][1]).toEqual(expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "Idempotency-Key": "request-7" }),
    }));
    expect(fetcher.mock.calls[1][0]).toBe("http://localhost:8000/api/v2/data-analyst/runs/run-1/cancel");
  });
});
