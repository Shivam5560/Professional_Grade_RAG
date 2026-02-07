/**
 * DrawioDiagram - Renders draw.io XML in a viewer iframe.
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Check, Copy, Maximize2, Minimize2 } from 'lucide-react';

interface DrawioDiagramProps {
  xml: string;
  title?: string;
}

export function DrawioDiagram({ xml, title = 'Diagram' }: DrawioDiagramProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [copiedXml, setCopiedXml] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const normalized = useMemo(() => {
    const raw = xml?.trim();
    if (!raw) {
      return { xml: null, error: 'Empty diagram payload.', compressed: false };
    }

    // Check if XML is compressed (marked with COMPRESSED: prefix)
    const isCompressed = raw.startsWith('COMPRESSED:');
    let xmlData = raw;
    
    if (isCompressed) {
      // Remove prefix and use compressed format
      xmlData = raw.substring('COMPRESSED:'.length);
      // Compressed format can be used directly in draw.io URLs
      return { xml: xmlData, error: null, compressed: true };
    }

    // Handle uncompressed XML
    const sanitizeXml = (value: string) => {
      let cleaned = value.trim();
      cleaned = cleaned.replace(/^```(?:xml)?\s*/i, '').replace(/```$/i, '').trim();

      const mxfileMatch = cleaned.match(/<mxfile[\s\S]*?<\/mxfile>/);
      if (mxfileMatch) {
        cleaned = mxfileMatch[0];
      }

      // Fix unescaped ampersands which often break XML parsing.
      cleaned = cleaned.replace(/&(?![a-zA-Z]+;|#\d+;|#x[0-9a-fA-F]+;)/g, '&amp;');
      return cleaned;
    };

    let wrapped = sanitizeXml(raw);
    const hasMxfile = /<mxfile[\s>]/.test(raw);
    const hasDiagram = /<diagram[\s>]/.test(raw);
    const hasGraphModel = /<mxGraphModel[\s>]/.test(raw);

    if (!hasMxfile) {
      if (hasDiagram) {
        wrapped = `<mxfile host="app.diagrams.net">${raw}</mxfile>`;
      } else if (hasGraphModel) {
        wrapped = `<mxfile host="app.diagrams.net"><diagram id="diagram-1" name="Page-1">${raw}</diagram></mxfile>`;
      }
    }

    const parser = new DOMParser();
    const document = parser.parseFromString(wrapped, 'text/xml');
    const parseErrors = document.getElementsByTagName('parsererror');
    if (parseErrors.length > 0) {
      return { xml: null, error: 'Invalid XML format.', compressed: false };
    }

    const mxfile = document.getElementsByTagName('mxfile')[0];
    const diagram = document.getElementsByTagName('diagram')[0];
    if (!mxfile || !diagram) {
      return { xml: null, error: 'Missing draw.io mxfile or diagram nodes.', compressed: false };
    }

    const hasContent =
      diagram.getElementsByTagName('mxGraphModel').length > 0 ||
      Boolean(diagram.textContent && diagram.textContent.trim().length > 0);
    if (!hasContent) {
      return { xml: null, error: 'Diagram is missing content.', compressed: false };
    }

    const serializer = new XMLSerializer();
    return { xml: serializer.serializeToString(document), error: null, compressed: false };
  }, [xml]);

  const viewerUrl = useMemo(() => {
    if (!normalized.xml) return null;
    
    // For compressed format, use the compressed data directly (draw.io can decompress it)
    // For uncompressed, URL encode it
    const encoded = normalized.compressed 
      ? normalized.xml 
      : encodeURIComponent(normalized.xml);
    
    // Use viewer.diagrams.net which works better for embedding
    return `https://viewer.diagrams.net/?lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1#R${encoded}`;
  }, [normalized]);

  const handleCopyXml = useCallback(async () => {
    if (!normalized.xml || normalized.compressed) return;
    try {
      await navigator.clipboard.writeText(normalized.xml);
      setCopiedXml(true);
      setTimeout(() => setCopiedXml(false), 2000);
    } catch (err) {
      console.error('Failed to copy XML:', err);
    }
  }, [normalized]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const handleToggleFullscreen = useCallback(async () => {
    const container = containerRef.current;
    if (!container) return;
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await container.requestFullscreen();
      }
    } catch (err) {
      console.error('Failed to toggle fullscreen:', err);
    }
  }, []);

  const editorUrl = useMemo(() => {
    if (!normalized.xml) return null;
    
    const encoded = normalized.compressed 
      ? normalized.xml 
      : encodeURIComponent(normalized.xml);
    
    return `https://app.diagrams.net/#R${encoded}`;
  }, [normalized]);

  const iframeClassName = isFullscreen
    ? 'w-full h-full bg-background'
    : 'w-full h-[240px] md:h-[320px] bg-background';

  return (
    <div
      ref={containerRef}
      className="mt-4 rounded-2xl border border-border/70 bg-card/80 backdrop-blur-sm shadow-lg overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/60 text-xs text-muted-foreground">
        <span className="font-semibold uppercase tracking-wider">{title}</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleToggleFullscreen}
            disabled={!viewerUrl}
            className="inline-flex items-center gap-1.5 rounded-md border border-border/70 bg-muted/60 px-2.5 py-1 text-[11px] font-semibold text-foreground/90 transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
            title={isFullscreen ? 'Exit fullscreen' : 'View fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
            {isFullscreen ? 'Exit' : 'Fullscreen'}
          </button>
          <button
            type="button"
            onClick={handleCopyXml}
            disabled={!normalized.xml || normalized.compressed}
            className="inline-flex items-center gap-1.5 rounded-md border border-border/70 bg-muted/60 px-2.5 py-1 text-[11px] font-semibold text-foreground/90 transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
            title={normalized.compressed ? 'XML copy unavailable for compressed diagrams' : 'Copy XML'}
          >
            {copiedXml ? (
              <Check className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            {copiedXml ? 'Copied' : 'Copy XML'}
          </button>
          {editorUrl ? (
            <a
              href={editorUrl}
              target="_blank"
              rel="noreferrer"
              className="text-foreground hover:text-foreground/80 transition-colors"
            >
              Open in draw.io
            </a>
          ) : (
            <span className="text-muted-foreground">Invalid diagram</span>
          )}
        </div>
      </div>
      {viewerUrl ? (
        <iframe
          title={title}
          src={viewerUrl}
          className={iframeClassName}
        />
      ) : (
        <div className="px-4 py-6 text-sm text-muted-foreground">
          Diagram data could not be rendered. {normalized.error}
        </div>
      )}
    </div>
  );
}
