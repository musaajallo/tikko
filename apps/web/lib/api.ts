import type {
  Device,
  DevicePunch,
  Employee,
  EmployeeStatus,
  EmployeeSyncEntry,
} from "@tikko/shared-types";

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

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  } catch {
    throw new Error(
      `Can't reach the API at ${baseUrl}. Is the server running?`,
    );
  }
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
  if (response.status === 204) {
    return undefined as T;
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

export interface EmployeeList {
  items: Employee[];
  total: number;
}

export interface EmployeeSyncResult {
  results: EmployeeSyncEntry[];
}

export interface AttendanceReportDay {
  date: string; // YYYY-MM-DD
  is_workday: boolean;
  is_absent: boolean;
  first_in: string | null;
  last_out: string | null;
  worked_minutes: number;
  late_minutes: number;
  early_out_minutes: number;
  overtime_minutes: number;
}

export interface AttendanceReportTotals {
  days_worked: number;
  days_absent: number;
  worked_minutes: number;
  late_minutes: number;
  early_out_minutes: number;
  overtime_minutes: number;
}

export interface AttendanceReport {
  month: string;
  employee: { id: string; employee_code: string; full_name: string };
  days: AttendanceReportDay[];
  totals: AttendanceReportTotals;
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

  listEmployees: (page = 1, pageSize = 50) =>
    request<EmployeeList>(`/employees?page=${page}&page_size=${pageSize}`),

  createEmployee: (input: {
    employee_code: string;
    full_name: string;
    status?: EmployeeStatus;
  }) =>
    request<Employee>("/employees", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  deleteEmployee: (employeeId: string) =>
    request<void>(`/employees/${employeeId}`, { method: "DELETE" }),

  syncEmployee: (employeeId: string, deviceIds: string[]) =>
    request<EmployeeSyncResult>(`/employees/${employeeId}/sync`, {
      method: "POST",
      body: JSON.stringify({ device_ids: deviceIds }),
    }),

  attendanceReport: (employeeId: string, month: string) =>
    request<AttendanceReport>(
      `/reports/attendance?employee_id=${employeeId}&month=${month}`,
    ),

  // CSV download needs the bearer token, so a plain <a href> doesn't work.
  // We fetch as Blob and let the caller trigger a browser download.
  async downloadAttendanceCsv(
    employeeId: string,
    month: string,
  ): Promise<{ blob: Blob; filename: string }> {
    const token = getToken();
    const url = `${baseUrl}/reports/attendance.csv?employee_id=${employeeId}&month=${month}`;
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`${response.status} ${response.statusText} — ${text}`);
    }
    const blob = await response.blob();
    const cd = response.headers.get("content-disposition") ?? "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const filename = match?.[1] ?? `attendance-${month}.csv`;
    return { blob, filename };
  },
};
