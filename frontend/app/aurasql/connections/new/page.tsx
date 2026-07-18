'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';

export default function NewAuraSqlConnectionPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  if (!isAuthenticated) return <AuthPage />;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const connection = await apiClient.createAuraSqlConnection({
        ...form,
        port: Number(form.port),
      });
      router.push(`/aurasql/contexts/new?connection=${connection.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save connection');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuraSqlPage title="Connect a database" description="Add the credentials AuraSQL needs, then continue directly into choosing the schema tables that ground your questions.">
      {isSubmitting ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-overlay">
          <div className="rounded-xl border border-border bg-workspace-raised px-6 py-4 text-center shadow-xl">
            <p className="text-sm font-semibold">Saving connection</p>
            <p className="text-xs text-muted-foreground mt-1">Validating credentials and schema.</p>
            <div className="mt-4 grid gap-2 text-left text-[11px] text-muted-foreground">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/60 animate-pulse" />
                Verifying credentials
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/40" />
                Checking schema access
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-foreground/40" />
                Saving connection profile
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mx-auto w-full max-w-3xl py-3">
          <Card className="border-border bg-workspace-raised shadow-sm">
            <CardHeader>
              <CardTitle>New Database Connection</CardTitle>
              <CardDescription>Save a connection for AuraSQL query generation.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Analytics DB"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Database Type</Label>
                    <select
                      value={form.db_type}
                      onChange={(event) => setForm({ ...form, db_type: event.target.value })}
                      className="w-full rounded-lg border border-border bg-workspace-inset px-3 py-2 text-sm"
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
                    <Input
                      value={form.host}
                      onChange={(e) => setForm({ ...form, host: e.target.value })}
                      placeholder="db.company.com"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Port</Label>
                    <Input
                      type="number"
                      value={form.port}
                      onChange={(e) => setForm({ ...form, port: Number(e.target.value) })}
                      required
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Username</Label>
                    <Input
                      value={form.username}
                      onChange={(e) => setForm({ ...form, username: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Password</Label>
                    <Input
                      type="password"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Database</Label>
                    <Input
                      value={form.database}
                      onChange={(e) => setForm({ ...form, database: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Schema</Label>
                    <Input
                      value={form.schema_name}
                      onChange={(e) => setForm({ ...form, schema_name: e.target.value })}
                      placeholder="public"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-xl border border-border bg-workspace-inset px-4 py-3">
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
                  <Button type="button" variant="ghost" data-destination="/aurasql/connections" onClick={() => router.push('/aurasql/connections')}>
                    Back
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => router.push('/aurasql')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save Connection'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
      </div>
    </AuraSqlPage>
  );
}
