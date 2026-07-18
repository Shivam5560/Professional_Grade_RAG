"use client";

import { motion, useReducedMotion } from "framer-motion";
import { BarChart3, Download, LineChart, Table2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import type { AuraSqlExecuteResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

type ResultMode = "table" | "graph";
type ChartKind = "bar" | "line";

interface AuraSqlResultViewportProps {
  execution: AuraSqlExecuteResponse;
  onExport(): void;
}

const asNumber = (value: unknown) => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string" || value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

export function AuraSqlResultViewport({
  execution,
  onExport,
}: AuraSqlResultViewportProps) {
  const reduceMotion = useReducedMotion();
  const [mode, setMode] = useState<ResultMode>("table");
  const [chartKind, setChartKind] = useState<ChartKind>("bar");

  const numericColumns = useMemo(
    () =>
      execution.columns.filter((column) =>
        execution.rows.some((row) => asNumber(row[column]) !== null),
      ),
    [execution],
  );
  const labelColumns = execution.columns.filter(
    (column) => !numericColumns.includes(column),
  );
  const [metric, setMetric] = useState(numericColumns[0] ?? "");
  const [dimension, setDimension] = useState(
    labelColumns[0] ?? execution.columns[0] ?? "",
  );
  const activeMetric = numericColumns.includes(metric)
    ? metric
    : numericColumns[0] ?? "";
  const activeDimension = execution.columns.includes(dimension)
    ? dimension
    : execution.columns[0] ?? "";

  const points = execution.rows.slice(0, 16).map((row, index) => ({
    label: String(row[activeDimension] ?? index + 1),
    value: asNumber(row[activeMetric]) ?? 0,
  }));
  const maxValue = Math.max(1, ...points.map((point) => Math.abs(point.value)));
  const linePoints = points
    .map((point, index) => {
      const x = points.length <= 1 ? 50 : (index / (points.length - 1)) * 100;
      const y = 92 - (Math.abs(point.value) / maxValue) * 78;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <section className="overflow-hidden rounded-lg border border-border/70 bg-workspace-raised shadow-[0_24px_80px_-48px_hsl(var(--foreground)/0.45)]">
      <header className="flex min-h-14 flex-wrap items-center justify-between gap-3 border-b border-border/60 px-3 py-2 sm:px-4">
        <div>
          <p className="text-sm font-semibold text-foreground">Explore results</p>
          <p className="text-xs text-muted-foreground">
            {execution.rows.length} rows · {execution.columns.length} columns
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-border/70 bg-muted/45 p-1" aria-label="Result view">
            <ModeButton active={mode === "table"} label="Table view" onClick={() => setMode("table")}>
              <Table2 className="h-4 w-4" />
            </ModeButton>
            <ModeButton active={mode === "graph"} label="Graph view" onClick={() => setMode("graph")}>
              <BarChart3 className="h-4 w-4" />
            </ModeButton>
          </div>
          <Button aria-label="Export results" size="icon" variant="ghost" onClick={onExport} title="Export CSV">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {mode === "table" ? (
          <motion.div
            key="table"
            initial={reduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-h-[32rem] overflow-auto"
          >
            <table aria-label="Query results" className="min-w-full border-collapse text-left text-sm">
              <thead className="sticky top-0 z-10 bg-workspace-raised">
                <tr className="border-b border-border/70">
                  {execution.columns.map((column) => (
                    <th key={column} className="whitespace-nowrap px-4 py-3 text-[11px] font-semibold uppercase text-muted-foreground">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/45">
                {execution.rows.map((row, index) => (
                  <tr key={index} className="transition-colors hover:bg-muted/35">
                    {execution.columns.map((column) => (
                      <td key={column} className="max-w-sm whitespace-nowrap px-4 py-3 font-mono text-xs text-foreground">
                        {String(row[column] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        ) : (
          <motion.div
            key="graph"
            initial={reduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 sm:p-5"
          >
            {numericColumns.length === 0 ? (
              <div className="grid min-h-64 place-items-center text-center">
                <div>
                  <BarChart3 className="mx-auto h-6 w-6 text-muted-foreground" />
                  <p className="mt-3 text-sm font-medium">No numeric series to visualize</p>
                  <p className="mt-1 text-xs text-muted-foreground">The table still contains the complete result.</p>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-5 flex flex-wrap items-end gap-3">
                  <label className="grid gap-1 text-xs text-muted-foreground">
                    Dimension
                    <select aria-label="Dimension" value={activeDimension} onChange={(event) => setDimension(event.target.value)} className="h-9 rounded-md border border-border/70 bg-background px-3 text-sm text-foreground">
                      {execution.columns.map((column) => <option key={column}>{column}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-1 text-xs text-muted-foreground">
                    Metric
                    <select aria-label="Metric" value={activeMetric} onChange={(event) => setMetric(event.target.value)} className="h-9 rounded-md border border-border/70 bg-background px-3 text-sm text-foreground">
                      {numericColumns.map((column) => <option key={column}>{column}</option>)}
                    </select>
                  </label>
                  <div className="flex rounded-md border border-border/70 bg-muted/45 p-1">
                    <ModeButton active={chartKind === "bar"} label="Bar chart" onClick={() => setChartKind("bar")}><BarChart3 className="h-4 w-4" /></ModeButton>
                    <ModeButton active={chartKind === "line"} label="Line chart" onClick={() => setChartKind("line")}><LineChart className="h-4 w-4" /></ModeButton>
                  </div>
                </div>
                <div role="img" aria-label={`${activeMetric} by ${activeDimension}`} className="relative h-72 overflow-hidden border-y border-border/50 py-5">
                  <div className="pointer-events-none absolute inset-0 grid grid-rows-4 divide-y divide-border/35" />
                  {chartKind === "bar" ? (
                    <div className="relative flex h-full items-end gap-2 px-2 sm:gap-3">
                      {points.map((point, index) => (
                        <div key={`${point.label}-${index}`} className="group flex h-full min-w-0 flex-1 flex-col justify-end">
                          <span className="mb-1 text-center font-mono text-[10px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">{point.value}</span>
                          <motion.div initial={reduceMotion ? false : { height: 0 }} animate={{ height: `${Math.max(3, Math.abs(point.value) / maxValue * 82)}%` }} transition={{ duration: 0.55, delay: index * 0.025 }} className="min-h-1 w-full bg-[hsl(var(--chart-2))] opacity-80 group-hover:opacity-100" title={`${point.label}: ${point.value}`} />
                          <span className="mt-2 truncate text-center text-[10px] text-muted-foreground">{point.label}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="relative h-[calc(100%-1.5rem)] w-full overflow-visible" aria-hidden="true">
                      <motion.polyline points={linePoints} fill="none" vectorEffect="non-scaling-stroke" stroke="hsl(var(--chart-2))" strokeWidth="2" initial={reduceMotion ? false : { pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} transition={{ duration: 0.7 }} />
                    </svg>
                  )}
                </div>
                <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
                  {points.slice(0, 8).map((point) => <span key={point.label}><span className="text-foreground">{point.value}</span> {point.label}</span>)}
                </div>
              </>
            )}
          </motion.div>
        )}
    </section>
  );
}

function ModeButton({ active, label, onClick, children }: { active: boolean; label: string; onClick(): void; children: React.ReactNode }) {
  return (
    <button aria-label={label} aria-pressed={active} type="button" onClick={onClick} className={cn("grid h-8 w-9 place-items-center rounded-sm text-muted-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", active && "bg-background text-foreground shadow-sm")}>
      {children}
    </button>
  );
}
