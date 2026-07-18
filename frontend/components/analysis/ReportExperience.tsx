"use client";

import { motion, useReducedMotion } from "framer-motion";
import { BarChart3, FileText, Lightbulb, Sparkles } from "lucide-react";

import { InsightCard } from "@/components/analysis/InsightCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Report } from "@/lib/analysis/types";

export function ReportExperience({ report }: { jobId: string; report: Report }) {
  const reduceMotion = useReducedMotion();

  return (
    <Tabs className="mx-auto w-full max-w-6xl py-6 sm:py-10" defaultValue="narrative">
      <TabsList className="h-11 w-full justify-start overflow-x-auto bg-transparent p-0 sm:w-auto">
        <TabsTrigger className="h-10 border-b-2 border-transparent bg-transparent px-4 shadow-none data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none" value="narrative">
          <FileText aria-hidden="true" className="mr-2 h-4 w-4" />Narrative
        </TabsTrigger>
        <TabsTrigger className="h-10 border-b-2 border-transparent bg-transparent px-4 shadow-none data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none" value="charts">
          <BarChart3 aria-hidden="true" className="mr-2 h-4 w-4" />Charts
        </TabsTrigger>
        <TabsTrigger className="h-10 border-b-2 border-transparent bg-transparent px-4 shadow-none data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none" value="insights">
          <Lightbulb aria-hidden="true" className="mr-2 h-4 w-4" />Insights
        </TabsTrigger>
      </TabsList>

      <TabsContent className="mt-8" value="narrative">
        <motion.article
          animate={{ opacity: 1, y: 0 }}
          className="border-y border-border/70 bg-background/62 px-5 py-8 backdrop-blur-xl sm:px-10 sm:py-12 lg:px-16"
          initial={{ opacity: 0, y: reduceMotion ? 0 : 14 }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.42 }}
        >
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase text-[hsl(var(--data))]">
            <Sparkles aria-hidden="true" className="h-4 w-4" />Executive narrative
          </div>
          <p className="mt-6 max-w-4xl whitespace-pre-wrap text-pretty text-lg leading-8 text-foreground sm:text-xl sm:leading-9">
            {report.narrative || "No executive narrative was published."}
          </p>
          {report.sections?.length ? (
            <div className="mt-12 divide-y divide-border border-y border-border">
              {report.sections.map((section, index) => (
                <section className="grid gap-3 py-6 md:grid-cols-[12rem_minmax(0,1fr)] md:gap-8" key={`${section.title}-${index}`}>
                  <h2 className="text-sm font-semibold">{section.title || `Section ${index + 1}`}</h2>
                  <p className="whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{section.content}</p>
                </section>
              ))}
            </div>
          ) : null}
        </motion.article>
      </TabsContent>

      <TabsContent className="mt-8" value="charts">
        {report.chart_urls.length ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {report.chart_urls.map((url, index) => (
              <figure className="overflow-hidden border border-border/70 bg-background/70 backdrop-blur-lg" key={url}>
                <figcaption className="flex items-center justify-between border-b border-border/70 px-4 py-3 text-xs font-medium">
                  <span>Visual evidence {index + 1}</span>
                  <span className="text-muted-foreground">Verified output</span>
                </figcaption>
                <div className="aspect-[16/10] bg-white p-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img alt={`Analysis chart ${index + 1}`} className="h-full w-full object-contain" src={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}${url}`} />
                </div>
              </figure>
            ))}
          </div>
        ) : <EmptyReportState label="No charts were produced for this analysis." />}
      </TabsContent>

      <TabsContent className="mt-8" value="insights">
        {report.insights.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {report.insights.map((insight) => <InsightCard insight={insight} key={insight.insight_id} />)}
          </div>
        ) : <EmptyReportState label="No prioritized insights were published." />}
      </TabsContent>
    </Tabs>
  );
}

function EmptyReportState({ label }: { label: string }) {
  return <div className="flex min-h-72 items-center justify-center border-y border-dashed border-border text-center text-sm text-muted-foreground">{label}</div>;
}
