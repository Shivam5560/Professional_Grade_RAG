'use client';

import AuthPage from '@/app/auth/page';
import { AuraSqlPage } from '@/components/aurasql/AuraSqlPage';
import { useAuthStore } from '@/lib/store';

export default function AuraSqlSettingsPage() {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <AuthPage />;

  return (
    <AuraSqlPage title="Query settings" description="Defaults for AuraSQL generation and result exploration.">
      <form className="mx-auto w-full max-w-2xl divide-y divide-border/60 rounded-xl border border-border bg-workspace-raised px-4 shadow-sm sm:px-6">
        <label className="flex items-center justify-between gap-5 py-5"><span><span className="block text-sm font-medium">Confirm before execution</span><span className="mt-1 block text-xs text-muted-foreground">Keep generated SQL in review until you explicitly run it.</span></span><input type="checkbox" defaultChecked className="h-4 w-4" /></label>
        <label className="flex items-center justify-between gap-5 py-5"><span><span className="block text-sm font-medium">Open results as table</span><span className="mt-1 block text-xs text-muted-foreground">Table remains the default while graph view stays one click away.</span></span><input type="checkbox" defaultChecked className="h-4 w-4" /></label>
        <label className="grid gap-2 py-5 text-sm font-medium">Default result limit<select defaultValue="100" className="h-10 rounded-md border border-border/70 bg-background px-3 text-sm font-normal"><option value="50">50 rows</option><option value="100">100 rows</option><option value="500">500 rows</option></select></label>
      </form>
    </AuraSqlPage>
  );
}
