'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useMemo, useState } from 'react';
import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { AuraSqlConnection } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';

function NewAuraSqlContextPageContent() {
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
        if (fromQuery && list.some((connection) => connection.id === fromQuery)) {
          setSelectedConnection(fromQuery);
        } else if (list.length > 0) {
          setSelectedConnection(list[0].id);
          if (fromQuery) setError('The requested connection is unavailable. Choose one of your saved connections.');
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
    if (!selectedConnection || selectedTables.size === 0 || !contextName.trim()) return;

    setError(null);
    try {
      const context = await apiClient.createAuraSqlContext({
        connection_id: selectedConnection,
        name: contextName.trim(),
        table_names: selectedTableList,
      });
      router.push(`/aurasql/query?context=${context.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create context');
    }
  };

  return (
    <AuraSqlPage title="Choose the data context" description="Name this reusable context, select the relevant tables, and AuraSQL will carry that scope into the query workspace.">
      <div className="mx-auto w-full max-w-4xl py-3">
          <Card className="border-border bg-workspace-raised shadow-sm">
            <CardHeader>
              <CardTitle>New Schema Context</CardTitle>
              <CardDescription>Select tables and save a reusable context.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSubmit}>
                {(loading || loadingTables) ? <p aria-live="polite" className="rounded-lg border border-border bg-workspace-inset p-3 text-sm text-muted-foreground">{loading ? 'Loading your saved connections…' : 'Loading available tables…'}</p> : null}
                <div className="space-y-2">
                  <Label htmlFor="context-name">Context Name</Label>
                  <Input id="context-name" value={contextName} onChange={(e) => setContextName(e.target.value)} placeholder="Sales analytics" required />
                </div>

                <div className="space-y-2">
                  <Label>Connection</Label>
                  {loading ? (
                    <p className="text-sm text-muted-foreground">Loading connections...</p>
                  ) : (
                    <select
                      value={selectedConnection}
                      onChange={(event) => setSelectedConnection(event.target.value)}
                      className="w-full rounded-lg border border-border bg-workspace-inset px-3 py-2 text-sm"
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
                        <label key={table} className="flex items-center gap-2 rounded-lg border border-border bg-workspace-inset px-3 py-2">
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
                  <Button type="button" variant="ghost" data-destination="/aurasql/contexts" onClick={() => router.push('/aurasql/contexts')}>
                    Back
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => router.push('/aurasql/contexts')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={loading || loadingTables || selectedTables.size === 0 || !contextName.trim()}>
                    Save Context
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
      </div>
    </AuraSqlPage>
  );
}

export default function NewAuraSqlContextPage() {
  return (
    <Suspense fallback={null}>
      <NewAuraSqlContextPageContent />
    </Suspense>
  );
}
