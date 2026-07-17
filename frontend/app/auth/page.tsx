"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AuthPanel,
  type LoginValues,
  type RegisterValues,
} from "@/components/auth/AuthPanel";
import { NexusAperture } from "@/components/brand/NexusAperture";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const { toast } = useToast();

  const fail = (reason: unknown, title: string) => {
    const error =
      reason instanceof Error
        ? reason
        : new Error("The request could not be completed.");
    toast({
      title,
      description: error.message,
      variant: "destructive",
    });
    throw error;
  };

  const login = async ({ email, password }: LoginValues) => {
    try {
      await apiClient.login(email, password);
      toast({
        title: "Welcome back",
        description: "Opening your workspace…",
      });
      router.push("/apps");
    } catch (reason) {
      fail(reason, "Login failed");
    }
  };

  const register = async ({ fullName, email, password }: RegisterValues) => {
    try {
      await apiClient.register(email, password, fullName);
      await apiClient.login(email, password);
      toast({
        title: "Workspace created",
        description: "Opening NexusMind…",
      });
      router.push("/apps");
    } catch (reason) {
      fail(reason, "Registration failed");
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href="/" className="font-black tracking-[.16em]">
          NEXUSMIND
        </Link>
        <AppearanceControl />
      </div>
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl items-center gap-12 py-12 lg:grid-cols-[1.05fr_.95fr]">
        <section>
          <NexusAperture className="mb-10 w-36" />
          <p className="font-mono text-xs uppercase tracking-[.24em] text-primary">
            Live workspace
          </p>
          <h1 className="mt-4 max-w-2xl text-5xl font-black leading-[.95] tracking-[-.055em] sm:text-6xl">
            Your live NexusMind workspace.
          </h1>
          <ul className="mt-8 space-y-3 text-muted-foreground">
            <li>Grounded answers with evidence</li>
            <li>Schema-aware data intelligence</li>
            <li>Persistent, observable workflows</li>
          </ul>
          <Link
            href="/showcase"
            className="mt-8 inline-flex font-semibold text-[hsl(var(--copper))]"
          >
            Explore the showcase first →
          </Link>
        </section>
        <section className="rounded-[2rem] border border-border bg-card p-6 shadow-2xl sm:p-9">
          <h2 className="text-2xl font-bold">Enter the system</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Authenticate to use live data and saved work.
          </p>
          <div className="mt-7">
            <AuthPanel onLogin={login} onRegister={register} />
          </div>
        </section>
      </div>
    </main>
  );
}
