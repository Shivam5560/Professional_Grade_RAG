'use client';

import { useEffect, useMemo, useState } from 'react';

import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';
import { DataTable, type DataTableColumn } from '@/components/ui/data-table';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { AuraSqlHistoryItem } from '@/lib/types';

export default function AuraSqlHistoryDataPage() {
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [history, setHistory] = useState<AuraSqlHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setIsMounted(true), []);
  useEffect(() => {
    if (!isAuthenticated) return;
    setLoading(true);
    apiClient.listAuraSqlHistory()
      .then(setHistory)
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Failed to load AuraSQL history'))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const columns = useMemo<DataTableColumn<AuraSqlHistoryItem>[]>(() => [
    { id: 'natural_language_query', header: 'Question', accessor: 'natural_language_query', className: 'min-w-64 max-w-md whitespace-normal font-medium' },
    { id: 'generated_sql', header: 'Generated SQL', accessor: 'generated_sql', className: 'min-w-80 max-w-xl whitespace-normal font-mono text-xs' },
    { id: 'status', header: 'Status', accessor: 'status', className: 'w-28' },
    { id: 'created_at', header: 'Created', accessor: (item) => item.created_at ? new Date(item.created_at).toLocaleString() : '—', className: 'w-48 whitespace-nowrap' },
  ], []);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <AuraSqlPage title="Query history" description="AuraSQL questions and generated statements stay separate from every other application history.">
      {error ? <p role="alert" className="mb-4 border-y border-rose-500/30 bg-rose-500/10 px-3 py-3 text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      <DataTable data={history} columns={columns} getRowId={(item) => item.id} loading={loading} searchPlaceholder="Search AuraSQL history" emptyTitle="No query history" emptyDescription="Your first generated statement will appear here." pageSize={20} className="bg-workspace-raised" />
    </AuraSqlPage>
  );
}
