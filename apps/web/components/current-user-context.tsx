"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { api, type AuthMeResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";

type Ctx = {
  me: AuthMeResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
};

const CurrentUserContext = createContext<Ctx>({
  me: null,
  loading: true,
  refresh: async () => {},
});

export function CurrentUserProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<AuthMeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    if (!getToken()) {
      setMe(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const result = await api.getMe();
      setMe(result);
    } catch {
      // Most likely 401 → request<T>'s interceptor already redirects to /login.
      // Anything else: leave `me` null and let the page handle it.
      setMe(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <CurrentUserContext.Provider value={{ me, loading, refresh }}>
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
