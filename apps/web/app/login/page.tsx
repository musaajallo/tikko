"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const tokens = await api.login({ email, password });
      setToken(tokens.access_token, tokens.refresh_token);
      router.push("/devices");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (/401/.test(message)) {
        setError("Invalid credentials.");
      } else {
        setError(message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main style={styles.page}>
      <h1>Sign in</h1>
      <form onSubmit={onSubmit} style={styles.form}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
      {error && <p style={styles.error}>{error}</p>}
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 24, maxWidth: 360, margin: "60px auto", fontFamily: "system-ui" },
  form: { display: "flex", flexDirection: "column", gap: 8 },
  error: { color: "crimson", marginTop: 12 },
};
