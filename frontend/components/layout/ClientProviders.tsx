"use client";

import { AppearanceProvider } from "@/components/theme/AppearanceProvider";
import { Toaster } from "@/hooks/useToast";

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return <AppearanceProvider>{children}<Toaster /></AppearanceProvider>;
}
