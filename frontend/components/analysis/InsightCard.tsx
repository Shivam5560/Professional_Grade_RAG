'use client';
import { Insight } from '@/lib/analysis/types';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  insight: Insight;
}

export function InsightCard({ insight }: Props) {
  const scoreColor = insight.significance_score > 0.8 ? 'bg-green-100 text-green-800' : insight.significance_score > 0.5 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800';

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Insight</CardTitle>
          <Badge variant="secondary" className={scoreColor}>
            {insight.significance_score.toFixed(2)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{insight.content}</p>
        <div className="mt-2 flex gap-1">
          {insight.source_agents.map((agent) => (
            <Badge key={agent} variant="outline" className="text-xs">{agent}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
