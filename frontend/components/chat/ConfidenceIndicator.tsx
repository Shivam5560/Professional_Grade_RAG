/**
 * ConfidenceIndicator - Visual display of confidence score
 */

'use client';

import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { getConfidenceColor } from '@/lib/utils';
import type { ConfidenceLevel } from '@/lib/types';

interface ConfidenceIndicatorProps {
  score: number;
  level: ConfidenceLevel;
  showDetails?: boolean;
}

export function ConfidenceIndicator({
  score,
  level,
  showDetails = true,
}: ConfidenceIndicatorProps) {
  const colorClass = getConfidenceColor(level);
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-muted-foreground">Confidence</span>
        <Badge className={colorClass} variant="outline">
          {level.toUpperCase()} ({Math.round(score)}%)
        </Badge>
      </div>
      
      {showDetails && (
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted/70 border border-border">
          <div 
            className="h-full bg-foreground transition-all duration-300 shadow-lg"
            style={{ width: `${score}%` }}
          />
        </div>
      )}
    </div>
  );
}
