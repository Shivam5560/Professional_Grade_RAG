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
      const Plotly = await import('react-plotly.js');
      if (!isMounted || !containerRef.current) return;
      try {
        const res = await fetch(chartJsonUrl);
        const chartJson = await res.json();
        // Plotly.newPlot(containerRef.current, chartJson.data, chartJson.layout);
      } catch {
        // fallback
      }
    }
    render();
    return () => { isMounted = false; };
  }, [chartJsonUrl]);

  return <div ref={containerRef} className="w-full h-64" />;
}
