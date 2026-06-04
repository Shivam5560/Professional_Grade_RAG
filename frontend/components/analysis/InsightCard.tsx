'use client';
import { Insight } from '@/lib/analysis/types';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb, Target } from 'lucide-react';

interface Props {
  insight: Insight;
}

export function InsightCard({ insight }: Props) {
  const score = Number(insight.significance_score || 0);
  const scoreColor = score > 0.8 ? 'bg-emerald-100 text-emerald-800' : score > 0.5 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-800';
  const title = insight.title || insight.headline || 'Key Insight';
  const recommendation = insight.recommendation || insight.action;

  return (
    <Card className="h-full overflow-hidden border-border/80 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-sm leading-5">
            <span className="rounded-md bg-primary/10 p-1.5 text-primary">
              <Lightbulb className="h-3.5 w-3.5" />
            </span>
            {title}
          </CardTitle>
          <Badge variant="secondary" className={scoreColor}>
            {score.toFixed(2)}
          </Badge>
        </div>
        {(insight.subtitle || insight.narrative_role) && (
          <p className="pt-1 text-xs text-muted-foreground">{insight.subtitle || insight.narrative_role}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-6 text-muted-foreground">{insight.content}</p>
        {recommendation && (
          <div className="rounded-md border bg-muted/30 p-3">
            <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-foreground">
              <Target className="h-3.5 w-3.5 text-primary" />
              Recommended action
            </div>
            <p className="text-xs leading-5 text-muted-foreground">{recommendation}</p>
          </div>
        )}
        <div className="flex flex-wrap gap-1.5">
          {(insight.source_agents || []).map((agent) => (
            <Badge key={agent} variant="outline" className="text-xs">{agent}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
