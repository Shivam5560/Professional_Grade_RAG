import Link from "next/link";

const focusRing =
  "rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";

export function PublicFooter() {
  return (
    <footer className="border-t border-border px-4 py-8 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 text-sm text-muted-foreground sm:flex-row sm:items-center">
        <p>Designed and engineered by Shivam Sourav.</p>
        <nav aria-label="Footer" className="flex gap-5 sm:ml-auto">
          <Link className={focusRing} href="/developer">
            Developer
          </Link>
          <Link className={focusRing} href="/?auth=login">
            Workspace access
          </Link>
          <Link className={focusRing} href="/apps">
            Apps
          </Link>
        </nav>
      </div>
    </footer>
  );
}
