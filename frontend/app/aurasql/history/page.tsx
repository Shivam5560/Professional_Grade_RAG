'use client';

import { useEffect, useState, useMemo } from 'react';
import { Header } from '@/components/layout/Header';
import { DataTable, type DataTableColumn } from '@/components/ui/data-table';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { AuraSqlHistoryItem } from '@/lib/types';
import AuthPage from '@/app/auth/page';

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

  const historyColumns = useMemo<DataTableColumn<AuraSqlHistoryItem>[]>(() => [
    {
      id: 'natural_language_query',
      header: 'Natural Language Query',
      accessor: 'natural_language_query',
      className: 'max-w-xs whitespace-normal',
    },
    {
      id: 'generated_sql',
      header: 'Generated SQL',
      accessor: 'generated_sql',
      className: 'max-w-sm whitespace-normal font-mono text-xs',
    },
    { id: 'status', header: 'Status', accessor: 'status', className: 'w-32' },
    { id: 'connection_id', header: 'Connection', accessor: 'connection_id', className: 'w-40' },
    {
      id: 'created_at',
      header: 'Date',
      accessor: (item) => (item.created_at ? new Date(item.created_at).toLocaleString() : '—'),
      className: 'w-52 whitespace-nowrap',
    },
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
        <DataTable
          data={history}
          columns={historyColumns}
          getRowId={(item) => item.id}
          loading={loading}
          searchPlaceholder="Search history..."
          emptyTitle="No generated SQL history"
          emptyDescription="Generated SQL requests will appear here."
          pageSize={20}
        />
      </main>
    </div>
  );
}
