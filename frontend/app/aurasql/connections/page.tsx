'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Database, Plus, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';
import { DeleteAuraSqlResourceDialog } from '@/components/aurasql/DeleteAuraSqlResourceDialog';
import { Button } from '@/components/ui/button';
import { DataTable, type DataTableColumn } from '@/components/ui/data-table';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { AuraSqlConnection } from '@/lib/types';

export default function AuraSqlConnectionsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<AuraSqlConnection | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => setIsMounted(true), []);
  useEffect(() => {
    if (!isAuthenticated) return;
    setLoading(true);
    apiClient.listAuraSqlConnections().then(setConnections).catch((reason) => setError(reason instanceof Error ? reason.message : 'Failed to load connections')).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const remove = useCallback(async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiClient.deleteAuraSqlConnection(pendingDelete.id);
      setConnections((current) => current.filter((item) => item.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch (reason) {
      setDeleteError(reason instanceof Error ? reason.message : 'Failed to delete connection');
    } finally {
      setDeleting(false);
    }
  }, [pendingDelete]);

  const columns = useMemo<DataTableColumn<AuraSqlConnection>[]>(() => [
    { id: 'name', header: 'Connection', cell: (connection) => <div><p className="font-medium">{connection.name}</p><p className="mt-1 font-mono text-xs text-muted-foreground">{connection.host}:{connection.port}</p></div> },
    { id: 'database', header: 'Database', cell: (connection) => <div><p>{connection.database}</p><p className="mt-1 text-xs text-muted-foreground">{connection.schema_name || 'default schema'}</p></div> },
    { id: 'db_type', header: 'Engine', accessor: 'db_type', className: 'w-32 capitalize' },
    { id: 'actions', header: <span className="sr-only">Actions</span>, searchable: false, className: 'w-44', cell: (connection) => <div className="flex justify-end gap-1"><Button size="sm" variant="outline" onClick={() => router.push(`/aurasql/query?connection=${connection.id}`)}>Query</Button><Button size="sm" variant="ghost" onClick={() => router.push(`/aurasql/connections/${connection.id}`)}>Edit</Button><Button size="icon" variant="ghost" aria-label={`Delete ${connection.name}`} onClick={() => { setDeleteError(null); setPendingDelete(connection); }}><Trash2 className="h-4 w-4" /></Button></div> },
  ], [router]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <AuraSqlPage title="Connections" description="Manage database access profiles used only by AuraSQL." actions={<Button onClick={() => router.push('/aurasql/connections/new')}><Plus className="mr-2 h-4 w-4" />New connection</Button>}>
      {error ? <p role="alert" className="mb-4 border-y border-rose-500/30 bg-rose-500/10 px-3 py-3 text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      {connections.length === 0 && !loading ? <div className="grid min-h-64 place-items-center border-y border-border/60 bg-workspace-raised text-center"><div><Database className="mx-auto h-6 w-6 text-muted-foreground" /><p className="mt-3 text-sm font-medium">Connect your first database</p><p className="mt-1 text-xs text-muted-foreground">The next step will help you choose the tables AuraSQL should understand.</p><Button className="mt-4" onClick={() => router.push('/aurasql/connections/new')}>Create connection</Button></div></div> : <DataTable data={connections} columns={columns} getRowId={(connection) => connection.id} loading={loading} searchPlaceholder="Search connections" pageSize={20} className="bg-workspace-raised" />}
      <DeleteAuraSqlResourceDialog deleting={deleting} error={deleteError} onCancel={() => setPendingDelete(null)} onConfirm={remove} open={Boolean(pendingDelete)} resourceName={pendingDelete?.name ?? ''} resourceType="connection" />
    </AuraSqlPage>
  );
}
