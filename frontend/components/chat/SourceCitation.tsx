/**
 * SourceCitation - Display source references for answers
 * Sources are collapsed by default and can be expanded
 */

'use client';

import { useState } from 'react';
import { FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { SourceReference } from '@/lib/types';

interface SourceCitationProps {
  sources: SourceReference[];
}

export function SourceCitation({ sources }: SourceCitationProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      {/* Collapsible Header */}
      <Button
        onClick={() => setIsExpanded(!isExpanded)}
        variant="ghost"
        className="w-full justify-between px-4 py-2 h-auto hover:bg-muted/60 rounded-xl transition-all"
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-foreground" />
          <span className="text-sm font-medium text-foreground">
            Sources ({sources.length})
          </span>
          <Badge variant="secondary" className="text-xs bg-muted/70 text-muted-foreground border-border">
            {isExpanded ? 'Expanded' : 'Collapsed'}
          </Badge>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </Button>

      {/* Expandable Content */}
      {isExpanded && (
        <Card className="mt-2 border-l-2 border-foreground/20 animate-in fade-in slide-in-from-top-2 duration-200 backdrop-blur-xl bg-card/80 border border-border/70 shadow-lg">
          <CardContent className="pt-4 space-y-3">
            {sources.map((source, index) => (
              <div
                key={index}
                className={cn(
                  "pb-3 border-b last:border-b-0 border-border/60",
                  "hover:bg-muted/60 -mx-4 px-4 py-2 rounded-xl transition-colors"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-foreground" />
                        <span className="font-semibold text-sm text-foreground">
                          {source.document}
                        </span>
                      </div>
                      {source.page && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-muted/70 text-muted-foreground border-border">
                          Page {source.page}
                        </Badge>
                      )}
                    </div>
                    {source.text_snippet && (
                      <div className="text-xs text-muted-foreground mt-2 pl-3 border-l-2 border-foreground/20 italic leading-relaxed">
                        &quot;{source.text_snippet}&quot;
                      </div>
                    )}
                  </div>
                  <Badge variant="secondary" className="text-xs shrink-0 bg-muted/70 text-foreground border-border">
                    {Math.round(source.relevance_score * 100)}%
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
