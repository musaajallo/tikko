const TOKEN_KEY = "tikko.access_token";
const REFRESH_KEY = "tikko.refresh_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string, refreshToken?: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  if (refreshToken) {
    window.localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}
