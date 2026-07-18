'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { AuraSqlContext } from '@/lib/types';

export default function AuraSqlContextsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [contexts, setContexts] = useState<AuraSqlContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    apiClient.listAuraSqlContexts().then(setContexts).catch((reason) => setError(reason instanceof Error ? reason.message : 'Failed to load contexts')).finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (!isAuthenticated) return <AuthPage />;

  return (
    <AuraSqlPage title="Schema contexts" description="Keep reusable table selections close to the questions they ground." actions={<Button onClick={() => router.push('/aurasql/contexts/new')}><Plus className="mr-2 h-4 w-4" />New context</Button>}>
      {error ? <p role="alert" className="mb-4 border-y border-rose-500/30 bg-rose-500/10 px-3 py-3 text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      {loading ? <p className="border-y border-border/60 py-12 text-center text-sm text-muted-foreground">Loading schema contexts…</p> : (
        <div className="divide-y divide-border/60 border-y border-border/60 bg-background/70 px-4 backdrop-blur-xl">
          {contexts.length === 0 ? <p className="py-16 text-center text-sm text-muted-foreground">No saved contexts yet.</p> : contexts.map((context) => (
            <article key={context.id} className="grid gap-4 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="min-w-0"><h2 className="font-medium">{context.name}</h2><p className="mt-1 truncate font-mono text-xs text-muted-foreground">{context.table_names.join(' · ')}</p></div>
              <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => router.push(`/aurasql/query?context=${context.id}`)}>Use context</Button><Button size="icon" variant="ghost" aria-label={`Delete ${context.name}`} onClick={async () => { if (!window.confirm(`Delete ${context.name}?`)) return; await apiClient.deleteAuraSqlContext(context.id); setContexts((current) => current.filter((item) => item.id !== context.id)); }}><Trash2 className="h-4 w-4" /></Button></div>
            </article>
          ))}
        </div>
      )}
    </AuraSqlPage>
  );
}
