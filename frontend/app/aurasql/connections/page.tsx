'use client';

import { useCallback, useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { DataTable, type DataTableColumn } from '@/components/ui/data-table';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection } from '@/lib/types';
import AuthPage from '@/app/auth/page';
import { Plus, Trash2 } from 'lucide-react';

export default function AuraSqlConnectionsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    loadData();
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    try {
      const connData = await apiClient.listAuraSqlConnections();
      setConnections(connData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConnection = useCallback(async (connectionId: string) => {
    if (!confirm('Delete this connection?')) return;
    try {
      await apiClient.deleteAuraSqlConnection(connectionId);
      setConnections((prev) => prev.filter((conn) => conn.id !== connectionId));
    } catch {
      alert('Failed to delete connection');
    }
  }, []);

  const connectionColumns = useMemo<DataTableColumn<AuraSqlConnection>[]>(() => [
    { id: 'name', header: 'Name', accessor: 'name' },
    { id: 'db_type', header: 'Type', accessor: 'db_type', className: 'w-32' },
    { id: 'host', header: 'Host', accessor: 'host' },
    { id: 'database', header: 'Database', accessor: 'database' },
    {
      id: 'actions',
      header: 'Actions',
      searchable: false,
      className: 'w-[250px]',
      cell: (conn) => (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => router.push(`/aurasql/query?connection=${conn.id}`)}>
            Query
          </Button>
          <Button size="sm" variant="ghost" onClick={() => router.push(`/aurasql/connections/${conn.id}`)}>
            Edit
          </Button>
          <Button size="sm" variant="ghost" onClick={() => handleDeleteConnection(conn.id)} aria-label={`Delete ${conn.name}`}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ], [handleDeleteConnection, router]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />
      <main className="flex-1 p-8 flex flex-col max-w-7xl mx-auto w-full">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Connections</h1>
            <p className="text-muted-foreground">Manage your database connections.</p>
          </div>
          <Button onClick={() => router.push('/aurasql/connections/new')}>
            <Plus className="h-4 w-4 mr-2" />
            New Connection
          </Button>
        </div>
        <DataTable
          data={connections}
          columns={connectionColumns}
          getRowId={(connection) => connection.id}
          loading={loading}
          searchPlaceholder="Search connections..."
          emptyTitle="No connections"
          emptyDescription="Create a connection to start querying your databases."
          pageSize={20}
        />
      </main>
    </div>
  );
}
