"use client";

import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  AuthOverlay,
} from "@/components/auth/AuthOverlay";
import type {
  LoginValues,
  RegisterValues,
} from "@/components/auth/AuthPanel";
import { useToast } from "@/hooks/useToast";
import { apiClient } from "@/lib/api";

export function AuthController({
  initialMode,
}: {
  initialMode?: "login" | "register";
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { toast } = useToast();
  const triggerRef = useRef<HTMLElement | null>(null);
  const [localMode, setLocalMode] = useState<"login" | "register" | null>(
    initialMode ?? null,
  );
  const mode = localMode ?? "login";
  const open = localMode !== null;

  const setOpen = useCallback(
    (nextOpen: boolean) => {
      if (nextOpen) {
        triggerRef.current = document.activeElement as HTMLElement | null;
        setLocalMode(mode);
        router.push(`${pathname}?auth=${mode}`, { scroll: false });
        return;
      }
      setLocalMode(null);
      router.push(pathname, { scroll: false });
      window.requestAnimationFrame(() => triggerRef.current?.focus());
    },
    [mode, pathname, router],
  );

  useEffect(() => {
    const openAuth = (event: Event) => {
      const requestedMode =
        event instanceof CustomEvent && event.detail === "register"
          ? "register"
          : "login";
      triggerRef.current = document.activeElement as HTMLElement | null;
      setLocalMode(requestedMode);
      router.push(`${pathname}?auth=${requestedMode}`, { scroll: false });
    };
    window.addEventListener("nexusmind:auth", openAuth);
    return () => window.removeEventListener("nexusmind:auth", openAuth);
  }, [pathname, router]);

  const login = async ({ email, password }: LoginValues) => {
    try {
      await apiClient.login(email, password);
      toast({ title: "Welcome back", description: "Opening your workspace." });
      router.push("/apps");
    } catch (reason) {
      const error = reason instanceof Error ? reason : new Error("Unable to sign in.");
      toast({ title: "Login failed", description: error.message, variant: "destructive" });
      throw error;
    }
  };

  const register = async ({ fullName, email, password }: RegisterValues) => {
    try {
      await apiClient.register(email, password, fullName);
      await apiClient.login(email, password);
      toast({ title: "Workspace created", description: "Opening NexusMind." });
      router.push("/apps");
    } catch (reason) {
      const error = reason instanceof Error ? reason : new Error("Unable to create the workspace.");
      toast({ title: "Registration failed", description: error.message, variant: "destructive" });
      throw error;
    }
  };

  return (
    <AuthOverlay
      open={open}
      mode={mode}
      onOpenChange={setOpen}
      onLogin={login}
      onRegister={register}
    />
  );
}
