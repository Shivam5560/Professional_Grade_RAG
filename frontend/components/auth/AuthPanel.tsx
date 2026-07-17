"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export interface LoginValues {
  email: string;
  password: string;
}

export interface RegisterValues extends LoginValues {
  fullName: string;
}

interface AuthPanelProps {
  onLogin(values: LoginValues): Promise<void>;
  onRegister(values: RegisterValues): Promise<void>;
}

export function AuthPanel({ onLogin, onRegister }: AuthPanelProps) {
  const [tab, setTab] = useState("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);

    try {
      await onLogin({
        email: String(data.get("email")),
        password: String(data.get("password")),
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  async function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const fullName = String(data.get("fullName")).trim();
    const email = String(data.get("email"));
    const password = String(data.get("password"));

    if (!fullName) {
      setError("Full name is required.");
      return;
    }

    if (password !== String(data.get("confirmation"))) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      await onRegister({ fullName, email, password });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to create the workspace.",
      );
    } finally {
      setBusy(false);
    }
  }

  const field = "mt-2";

  return (
    <Tabs
      value={tab}
      onValueChange={(value) => {
        setTab(value);
        setError("");
      }}
    >
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="login">Sign in</TabsTrigger>
        <TabsTrigger value="register">Create account</TabsTrigger>
      </TabsList>
      {error ? (
        <p
          id="auth-error"
          role="alert"
          className="mt-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive"
        >
          {error}
        </p>
      ) : null}
      <TabsContent value="login">
        <form onSubmit={submitLogin} className="mt-6 space-y-5">
          <div>
            <Label htmlFor="login-email">Email</Label>
            <Input
              className={field}
              id="login-email"
              name="email"
              type="email"
              required
              aria-describedby={error ? "auth-error" : undefined}
            />
          </div>
          <div>
            <Label htmlFor="login-password">Password</Label>
            <Input
              className={field}
              id="login-password"
              name="password"
              type="password"
              required
              minLength={8}
            />
          </div>
          <Button className="w-full" disabled={busy} type="submit">
            {busy ? "Authenticating…" : "Enter NexusMind"}
          </Button>
        </form>
      </TabsContent>
      <TabsContent value="register">
        <form onSubmit={submitRegistration} className="mt-6 space-y-5">
          <div>
            <Label htmlFor="register-name">Full name</Label>
            <Input
              className={field}
              id="register-name"
              name="fullName"
              required
            />
          </div>
          <div>
            <Label htmlFor="register-email">Email</Label>
            <Input
              className={field}
              id="register-email"
              name="email"
              type="email"
              required
            />
          </div>
          <div>
            <Label htmlFor="register-password">Password</Label>
            <Input
              className={field}
              id="register-password"
              name="password"
              type="password"
              required
              minLength={8}
            />
          </div>
          <div>
            <Label htmlFor="register-confirmation">Confirm password</Label>
            <Input
              className={field}
              id="register-confirmation"
              name="confirmation"
              type="password"
              required
              minLength={8}
            />
          </div>
          <Button className="w-full" disabled={busy} type="submit">
            {busy ? "Creating…" : "Create workspace"}
          </Button>
        </form>
      </TabsContent>
      <p aria-live="polite" className="sr-only">
        {busy ? "Authentication request in progress" : ""}
      </p>
    </Tabs>
  );
}
