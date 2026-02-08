'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function NewAuraSqlContextPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { isAuthenticated } = useAuthStore();
  const [connections, setConnections] = useState<AuraSqlConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>('');
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());
  const [contextName, setContextName] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingTables, setLoadingTables] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    const loadConnections = async () => {
      setLoading(true);
      try {
        const list = await apiClient.listAuraSqlConnections();
        setConnections(list);
        const fromQuery = params.get('connection');
        if (fromQuery) {
          setSelectedConnection(fromQuery);
        } else if (list.length > 0) {
          setSelectedConnection(list[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load connections');
      } finally {
        setLoading(false);
      }
    };

    loadConnections();
  }, [isAuthenticated, params]);

  useEffect(() => {
    if (!selectedConnection) return;
    const loadTables = async () => {
      setLoadingTables(true);
      setError(null);
      try {
        const list = await apiClient.listAuraSqlTables(selectedConnection);
        setTables(list);
        setSelectedTables(new Set());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tables');
      } finally {
        setLoadingTables(false);
      }
    };

    loadTables();
  }, [selectedConnection]);

  const selectedTableList = useMemo(() => Array.from(selectedTables), [selectedTables]);

  if (!isAuthenticated) return <AuthPage />;

  const toggleTable = (table: string) => {
    setSelectedTables((prev) => {
      const next = new Set(prev);
      if (next.has(table)) {
        next.delete(table);
      } else {
        next.add(table);
      }
      return next;
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedConnection || selectedTables.size === 0) return;

    setError(null);
    try {
      const context = await apiClient.createAuraSqlContext({
        connection_id: selectedConnection,
        name: contextName || 'Untitled context',
        table_names: selectedTableList,
      });
      router.push(`/aurasql/query?context=${context.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create context');
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-4xl mx-auto">
          <Card className="glass-panel border-border/60">
            <CardHeader>
              <CardTitle>New Schema Context</CardTitle>
              <CardDescription>Select tables and save a reusable context.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label>Context Name</Label>
                  <Input value={contextName} onChange={(e) => setContextName(e.target.value)} placeholder="Sales analytics" />
                </div>

                <div className="space-y-2">
                  <Label>Connection</Label>
                  {loading ? (
                    <p className="text-sm text-muted-foreground">Loading connections...</p>
                  ) : (
                    <select
                      value={selectedConnection}
                      onChange={(event) => setSelectedConnection(event.target.value)}
                      className="w-full rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                    >
                      {connections.map((conn) => (
                        <option key={conn.id} value={conn.id}>
                          {conn.name} • {conn.database}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div className="space-y-3">
                  <Label>Tables</Label>
                  {loadingTables ? (
                    <p className="text-sm text-muted-foreground">Loading tables...</p>
                  ) : tables.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No tables found.</p>
                  ) : (
                    <div className="grid gap-2 md:grid-cols-2">
                      {tables.map((table) => (
                        <label key={table} className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3 py-2">
                          <input
                            type="checkbox"
                            checked={selectedTables.has(table)}
                            onChange={() => toggleTable(table)}
                            className="h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/40"
                          />
                          <span className="text-sm">{table}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <div className="flex justify-between gap-3">
                  <Button type="button" variant="ghost" onClick={() => router.back()}>
                    Back
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => router.push('/aurasql')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={selectedTables.size === 0}>
                    Save Context
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
