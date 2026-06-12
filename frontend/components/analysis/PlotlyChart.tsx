'use client';
import { useEffect, useRef } from 'react';

interface Props {
  chartJsonUrl: string;
}

export function PlotlyChart({ chartJsonUrl }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    async function render() {
      const _Plotly = await import('react-plotly.js');
      if (!isMounted || !containerRef.current) return;
      try {
        const res = await fetch(chartJsonUrl, { headers: { 'ngrok-skip-browser-warning': 'true' } });
        const _chartJson = await res.json();
        // _Plotly.newPlot(containerRef.current, _chartJson.data, _chartJson.layout);
      } catch {
        // fallback
      }
    }
    render();
    return () => { isMounted = false; };
  }, [chartJsonUrl]);

  return <div ref={containerRef} className="w-full h-64" />;
}
