import { notFound, redirect } from "next/navigation";

import { CatalogHttpError, getApp } from "@/lib/apps/client";

export default async function AppLaunch({
  params,
}: {
  params: { appId: string };
}): Promise<never> {
  try {
    const app = await getApp(params.appId);
    redirect(app.frontend_route);
  } catch (error) {
    if (error instanceof CatalogHttpError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
