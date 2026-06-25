'use client';

import { useEffect, useState, useMemo } from 'react';
import { Header } from '@/components/layout/Header';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { AuraSqlHistoryItem } from '@/lib/types';
import AuthPage from '@/app/auth/page';

import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ColDef } from 'ag-grid-community';

export default function AuraSqlHistoryDataPage() {
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    apiClient.listAuraSqlHistory().then((data) => {
      setHistory(data);
      setLoading(false);
    });
  }, [isAuthenticated]);

  const historyColDefs = useMemo<ColDef[]>(() => [
    { field: 'natural_language_query', headerName: 'Natural Language Query', flex: 2, filter: true },
    { field: 'generated_sql', headerName: 'Generated SQL', flex: 2, filter: true },
    { field: 'status', headerName: 'Status', width: 120, filter: true },
    { field: 'connection_id', headerName: 'Connection', width: 150, filter: true },
    { 
      field: 'created_at', 
      headerName: 'Date', 
      width: 200,
      valueFormatter: (p) => p.value ? new Date(p.value).toLocaleString() : '—'
    }
  ], []);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />
      <main className="flex-1 p-8 flex flex-col max-w-7xl mx-auto w-full">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Generation Feed</h1>
          <p className="text-muted-foreground">Full history of generated SQL intents.</p>
        </div>
        <div className="flex-1 w-full ag-theme-quartz-dark" style={{ minHeight: '600px' }}>
          <AgGridReact
            rowData={history}
            columnDefs={historyColDefs}
            rowHeight={50}
            animateRows={true}
            pagination={true}
            paginationPageSize={20}
            overlayLoadingTemplate={loading ? '<span class="ag-overlay-loading-center">Loading...</span>' : undefined}
          />
        </div>
      </main>
    </div>
  );
}
