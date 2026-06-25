'use client';

import { useCallback, useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection } from '@/lib/types';
import AuthPage from '@/app/auth/page';
import { Plus, Trash2 } from 'lucide-react';

import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ColDef, ICellRendererParams } from 'ag-grid-community';

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

  const ActionRenderer = useCallback((params: ICellRendererParams) => {
    const conn = params.data;
    return (
      <div className="flex gap-2 items-center h-full">
        <Button size="sm" variant="outline" onClick={() => router.push(`/aurasql/query?connection=${conn.id}`)}>Query</Button>
        <Button size="sm" variant="ghost" onClick={() => router.push(`/aurasql/connections/${conn.id}`)}>Edit</Button>
        <Button size="sm" variant="ghost" onClick={() => handleDeleteConnection(conn.id)}><Trash2 className="h-4 w-4" /></Button>
      </div>
    );
  }, [handleDeleteConnection, router]);

  const connectionColDefs = useMemo<ColDef[]>(() => [
    { field: 'name', headerName: 'Name', flex: 1, filter: true },
    { field: 'db_type', headerName: 'Type', width: 120, filter: true },
    { field: 'host', headerName: 'Host', flex: 1 },
    { field: 'database', headerName: 'Database', flex: 1 },
    { 
      headerName: 'Actions',
      width: 250,
      cellRenderer: ActionRenderer
    }
  ], [ActionRenderer]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />
      <main className="flex-1 p-8 flex flex-col max-w-7xl mx-auto w-full">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Connections Data Grid</h1>
            <p className="text-muted-foreground">Manage your database connections in a premium data grid.</p>
          </div>
          <Button onClick={() => router.push('/aurasql/connections/new')}>
            <Plus className="h-4 w-4 mr-2" />
            New Connection
          </Button>
        </div>
        <div className="flex-1 w-full ag-theme-quartz-dark" style={{ minHeight: '600px' }}>
          <AgGridReact
            rowData={connections}
            columnDefs={connectionColDefs}
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
