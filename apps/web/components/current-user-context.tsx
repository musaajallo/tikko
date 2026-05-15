"use client";

import { usePathname } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";

import { api, type AuthMeResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";

type Ctx = {
  me: AuthMeResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
  /** True if the current user's role has been granted `cap`. */
  hasCapability: (cap: string) => boolean;
};

const CurrentUserContext = createContext<Ctx>({
  me: null,
  loading: true,
  refresh: async () => {},
  hasCapability: () => false,
});

// Paths the user can hit without being signed in. Everything else bounces to
// /login when there's no token. Keep this small — the router shouldn't grow a
// sprawling allowlist.
const PUBLIC_PATHS = new Set<string>(["/", "/login"]);

function redirectToLoginIfNeeded(pathname: string | null): void {
  if (typeof window === "undefined") return;
  if (pathname && PUBLIC_PATHS.has(pathname)) return;
  if (window.location.pathname === "/login") return;
  window.location.href = "/login";
}

export function CurrentUserProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<AuthMeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  const refresh = async () => {
    if (!getToken()) {
      setMe(null);
      setLoading(false);
      // Token missing — boot to /login unless we're on a public route.
      // Without this guard a protected page would render a half-empty shell
      // until its own first api call 401s and redirects.
      redirectToLoginIfNeeded(pathname);
      return;
    }
    setLoading(true);
    try {
      const result = await api.getMe();
      setMe(result);
    } catch {
      // request<T> already redirects on 401. For any other error (network,
      // 500, …) leave `me` null — pages can render a logged-out shell or
      // their own error UI.
      setMe(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // Re-evaluate on pathname change so a client-side route to a protected
    // page also triggers the guard. `refresh` intentionally not in deps —
    // would re-fetch /auth/me on every state change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const caps = me?.capabilities ?? [];
  const hasCapability = (cap: string) => caps.includes(cap);

  return (
    <CurrentUserContext.Provider value={{ me, loading, refresh, hasCapability }}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUser(): Ctx {
  return useContext(CurrentUserContext);
}

export function useRole(): "admin" | "manager" | "employee" | null {
  const { me } = useCurrentUser();
  return me?.user.role ?? null;
}

export function useHasCapability(cap: string): boolean {
  const { hasCapability } = useCurrentUser();
  return hasCapability(cap);
}
