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
        <span className="text-sm font-medium text-slate-300">Confidence</span>
        <Badge className={colorClass} variant="outline">
          {level.toUpperCase()} ({Math.round(score)}%)
        </Badge>
      </div>
      
      {showDetails && (
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800/60 border border-slate-700">
          <div 
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-300 shadow-lg shadow-cyan-500/30"
            style={{ width: `${score}%` }}
          />
        </div>
      )}
    </div>
  );
}
