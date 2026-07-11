"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function AppsError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-3xl items-center px-4 py-10 sm:px-6 lg:px-8">
      <Alert variant="destructive">
        <AlertTitle>Application catalog unavailable</AlertTitle>
        <AlertDescription>
          <p>
            We could not load this application view. Retry the request, or return
            later if the problem continues.
          </p>
          <Button className="mt-4" type="button" onClick={reset}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    </main>
  );
}
