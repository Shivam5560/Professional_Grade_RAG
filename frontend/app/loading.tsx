import { LoadingState } from '@/components/ui/loading-state';

export default function Loading() {
  return (
    <main className="min-h-screen bg-background p-6 text-foreground">
      <div className="mx-auto flex min-h-[70vh] max-w-3xl items-center">
        <LoadingState
          title="Loading page"
          description="Preparing the workspace and latest data."
          className="w-full"
        />
      </div>
    </main>
  );
}
