// frontend/lib/analysis/useAnalysisSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useAnalysisStore } from './store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export function useAnalysisSocket(jobId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const maxReconnects = 5;
  const { appendEvent, setReportData, setSocketConnected, reset } = useAnalysisStore();

  const connect = useCallback(() => {
    if (!jobId) return;
    const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/api/v1/analysis/${jobId}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectCount.current = 0;
      setSocketConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'event') {
        appendEvent(data.payload);
      }
      if (data.type === 'complete') {
        setReportData(data.payload);
        ws.close();
      }
      if (data.type === 'error') {
        setReportData(null);
      }
    };

    ws.onclose = () => {
      setSocketConnected(false);
      if (reconnectCount.current < maxReconnects) {
        reconnectCount.current += 1;
        setTimeout(connect, 1000 * Math.min(reconnectCount.current, 10));
      }
    };

    ws.onerror = () => {
      setSocketConnected(false);
      ws.close();
    };
  }, [jobId, appendEvent, setReportData, setSocketConnected, reset]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);
}
