/**
 * DrawioDiagram - Renders draw.io XML in an embedded viewer.
 */

'use client';

import { useMemo } from 'react';

interface DrawioDiagramProps {
  xml: string;
  title?: string;
}

export function DrawioDiagram({ xml, title = 'Diagram' }: DrawioDiagramProps) {
  const viewerUrl = useMemo(() => {
    const encoded = encodeURIComponent(xml);
    return `https://viewer.diagrams.net/?embed=1&ui=min&spin=1&nav=1&fit=1&zoom=1&lightbox=1#R${encoded}`;
  }, [xml]);

  const editorUrl = useMemo(() => {
    const encoded = encodeURIComponent(xml);
    return `https://app.diagrams.net/?embed=1&ui=min&spin=1&nav=1&fit=1&zoom=1&lightbox=1#R${encoded}`;
  }, [xml]);

  return (
    <div className="mt-4 rounded-2xl border border-border/70 bg-card/80 backdrop-blur-sm shadow-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/60 text-xs text-muted-foreground">
        <span className="font-semibold uppercase tracking-wider">{title}</span>
        <a
          href={editorUrl}
          target="_blank"
          rel="noreferrer"
          className="text-foreground hover:text-foreground/80 transition-colors"
        >
          Open in draw.io
        </a>
      </div>
      <iframe
        title={title}
        src={viewerUrl}
        className="w-full h-[320px] md:h-[420px] bg-background"
      />
    </div>
  );
}
