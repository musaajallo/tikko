import type { Device, DevicePunch } from "@tikko/shared-types";

import { clearToken, getToken } from "./auth";

const baseUrl =
  process.env.NEXT_PUBLIC_TIKKO_API_BASE_URL ?? "http://localhost:8000";

const AUTH_PATHS = new Set(["/auth/login", "/auth/register"]);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (token && !("Authorization" in headers)) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    // Expired or rejected session: drop the token and bounce to /login. We
    // do this for any 401 that isn't an actual auth call (so the login form
    // can still surface "invalid credentials" inline).
    if (response.status === 401 && !AUTH_PATHS.has(path) && typeof window !== "undefined") {
      clearToken();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    const text = await response.text().catch(() => "");
    throw new Error(`${response.status} ${response.statusText} — ${text}`);
  }
  return response.json() as Promise<T>;
}

export interface DeviceList {
  items: Device[];
  total: number;
}

export interface PollResult {
  polled: number;
  new: number;
}

export interface DeviceInfo {
  serial_number: string;
  firmware_version: string;
  platform: string;
  device_name: string;
}

export interface AttendanceList {
  items: DevicePunch[];
  total: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface Stats {
  devices: number;
  devices_enabled: number;
  devices_online: number;
  punches_today: number;
  punches_24h: number;
}

export const api = {
  login: (input: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  getStats: () => request<Stats>("/stats"),

  listDevices: () => request<DeviceList>("/devices"),

  createDevice: (input: { name: string; host: string; port?: number; location?: string | null }) =>
    request<Device>("/devices", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  testConnection: (deviceId: string) =>
    request<DeviceInfo>(`/devices/${deviceId}/test-connection`, { method: "POST" }),

  pollDevice: (deviceId: string) =>
    request<PollResult>(`/devices/${deviceId}/poll`, { method: "POST" }),

  listAttendance: (deviceId: string, page = 1, pageSize = 50) =>
    request<AttendanceList>(
      `/devices/${deviceId}/attendance?page=${page}&page_size=${pageSize}`,
    ),
};
