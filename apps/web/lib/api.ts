import type { Device, DevicePunch } from "@tikko/shared-types";

const baseUrl =
  process.env.NEXT_PUBLIC_TIKKO_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
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

export const api = {
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
