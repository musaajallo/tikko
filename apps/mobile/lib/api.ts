import { getToken } from "./auth";

const baseUrl =
  process.env.EXPO_PUBLIC_TIKKO_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (token && !("Authorization" in headers)) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`${response.status} ${response.statusText} — ${text}`);
  }
  return (await response.json()) as T;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export const api = {
  login: (input: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
