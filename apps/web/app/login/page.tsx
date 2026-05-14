"use client";

import { Zap } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

const REMEMBER_EMAIL_KEY = "tikko.remembered_email";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prefill the email + tick "Remember me" if the user opted in last time.
  // Lives in localStorage on purpose — survives tab restarts. Never stores
  // the password.
  useEffect(() => {
    const stored = window.localStorage.getItem(REMEMBER_EMAIL_KEY);
    if (stored) {
      setEmail(stored);
      setRemember(true);
    }
  }, []);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const tokens = await api.login({ email, password });
      setToken(tokens.access_token, tokens.refresh_token);
      if (remember) {
        window.localStorage.setItem(REMEMBER_EMAIL_KEY, email);
      } else {
        window.localStorage.removeItem(REMEMBER_EMAIL_KEY);
      }
      router.push("/devices");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(/401/.test(message) ? "Invalid credentials." : message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-gradient-to-br from-background via-background to-emerald-50 px-4 py-12 dark:to-emerald-950/20">
      <div className="flex w-full max-w-md flex-col items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground">
            <Zap className="h-5 w-5" />
          </span>
          <span className="text-2xl font-bold tracking-tight">tikko</span>
        </div>

        <Card className="w-full shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Welcome back</CardTitle>
            <CardDescription>Sign in to your account to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <Checkbox
                    id="remember"
                    checked={remember}
                    onCheckedChange={(checked) => setRemember(checked === true)}
                  />
                  <span>Remember me</span>
                </label>
                <span className="text-sm font-medium text-primary opacity-60">
                  Forgot password?
                </span>
              </div>
              {error && (
                <p className="text-sm text-destructive" role="alert">
                  {error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={submitting} size="lg">
                {submitting ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Contact your admin
          </Link>
        </p>
      </div>
    </main>
  );
}
