'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { Loader2 } from 'lucide-react';

export default function EditAuraSqlConnectionPage() {
  const router = useRouter();
  const params = useParams();
  const { isAuthenticated } = useAuthStore();
  const [form, setForm] = useState({
    name: '',
    db_type: 'postgresql',
    host: '',
    port: 5432,
    username: '',
    password: '',
    database: '',
    schema_name: 'public',
    ssl_required: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const connection = await apiClient.getAuraSqlConnection(String(params.id));
        setForm({
          name: connection.name,
          db_type: connection.db_type,
          host: connection.host,
          port: connection.port,
          username: connection.username,
          password: '',
          database: connection.database,
          schema_name: connection.schema_name || 'public',
          ssl_required: connection.ssl_required,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load connection');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [isAuthenticated, params.id]);

  if (!isAuthenticated) return <AuthPage />;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiClient.updateAuraSqlConnection(String(params.id), {
        ...form,
        port: Number(form.port),
        password: form.password || undefined,
      });
      router.push('/aurasql');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update connection');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-3xl mx-auto">
          <Card className="glass-panel border-border/60">
            <CardHeader>
              <CardTitle>Edit Connection</CardTitle>
              <CardDescription>Update connection details or password.</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading connection...
                </div>
              ) : (
                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Name</Label>
                      <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Database Type</Label>
                      <select
                        value={form.db_type}
                        onChange={(event) => setForm({ ...form, db_type: event.target.value })}
                        className="w-full rounded-lg border border-border/70 bg-card/70 px-3 py-2 text-sm"
                      >
                        <option value="postgresql">PostgreSQL</option>
                        <option value="mysql">MySQL</option>
                        <option value="oracle">Oracle</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Host</Label>
                      <Input value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Port</Label>
                      <Input type="number" value={form.port} onChange={(e) => setForm({ ...form, port: Number(e.target.value) })} required />
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Username</Label>
                      <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Leave blank to keep" />
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Database</Label>
                      <Input value={form.database} onChange={(e) => setForm({ ...form, database: e.target.value })} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Schema</Label>
                      <Input value={form.schema_name} onChange={(e) => setForm({ ...form, schema_name: e.target.value })} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                    <div>
                      <p className="text-sm font-medium">Require SSL</p>
                      <p className="text-xs text-muted-foreground">Enable SSL connections by default.</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={form.ssl_required}
                      onChange={(event) => setForm({ ...form, ssl_required: event.target.checked })}
                      className="h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/40"
                    />
                  </div>

                  {error && <p className="text-sm text-red-500">{error}</p>}

                  <div className="flex justify-between gap-3">
                    <Button type="button" variant="ghost" onClick={() => router.back()}>
                      Back
                    </Button>
                    <Button type="button" variant="ghost" onClick={() => router.push('/aurasql')}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={saving}>
                      {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
