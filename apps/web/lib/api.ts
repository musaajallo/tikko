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

export type UserRole = "admin" | "manager" | "employee";

export interface UserMe {
  id: string;
  email: string;
  role: UserRole;
  employee_id: string | null;
  created_at: string;
}

export interface AuthMeResponse {
  user: UserMe;
  employee: Employee | null;
  // Flat list of capability names granted to this user's role. Source of
  // truth for UI gating; the api enforces the same list server-side.
  capabilities: string[];
}

export interface PermissionsMatrixResponse {
  matrix: Record<UserRole, string[]>;
  all_roles: UserRole[];
  all_capabilities: string[];
}

export interface TOTPEnrollResponse {
  secret: string;
  otpauth_uri: string;
  enabled: boolean;
}

export interface UserListItem {
  id: string;
  email: string;
  role: UserRole;
  employee_id: string | null;
  created_at: string;
}

export interface UserListResponse {
  items: UserListItem[];
  total: number;
}

export interface ShiftRule {
  id: string;
  name: string;
  start_time: string; // HH:MM:SS
  end_time: string;
  late_grace_minutes: number;
  early_out_grace_minutes: number;
  overtime_threshold_minutes: number;
  work_days: string; // 7-char binary, Mon..Sun
  created_at: string;
  updated_at: string;
}

export interface ShiftRuleList {
  items: ShiftRule[];
  total: number;
}

export type ShiftRuleCreate = Omit<ShiftRule, "id" | "created_at" | "updated_at">;
export type ShiftRuleUpdate = Partial<ShiftRuleCreate>;

export interface Department {
  id: string;
  name: string;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DepartmentList {
  items: Department[];
  total: number;
}

export interface DepartmentCreate {
  name: string;
  parent_id?: string | null;
}

export type DepartmentUpdate = Partial<DepartmentCreate>;

export interface AuditEvent {
  id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  before: unknown | null;
  after: unknown | null;
  created_at: string;
}

export interface AuditEventList {
  items: AuditEvent[];
  total: number;
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
    department_id?: string | null;
  }) =>
    request<Employee>("/employees", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  updateEmployee: (
    employeeId: string,
    input: {
      full_name?: string;
      status?: EmployeeStatus;
      shift_rule_id?: string | null;
      department_id?: string | null;
    },
  ) =>
    request<Employee>(`/employees/${employeeId}`, {
      method: "PATCH",
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

  getMe: () => request<AuthMeResponse>("/auth/me"),

  changePassword: (input: { current_password: string; new_password: string }) =>
    request<void>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  totpEnroll: () =>
    request<TOTPEnrollResponse>("/auth/totp/enroll", { method: "POST" }),

  totpVerify: (code: string) =>
    request<{ enabled: boolean }>("/auth/totp/verify", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),

  totpDisable: (password: string) =>
    request<void>("/auth/totp/disable", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  listUsers: (page = 1, pageSize = 50) =>
    request<UserListResponse>(`/users?page=${page}&page_size=${pageSize}`),

  updateUserRole: (userId: string, role: UserRole) =>
    request<UserListItem>(`/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),

  listAuditLog: (params?: {
    page?: number;
    pageSize?: number;
    actorUserId?: string;
    resourceType?: string;
    action?: string;
  }) => {
    const sp = new URLSearchParams();
    if (params?.page) sp.set("page", String(params.page));
    if (params?.pageSize) sp.set("page_size", String(params.pageSize));
    if (params?.actorUserId) sp.set("actor_user_id", params.actorUserId);
    if (params?.resourceType) sp.set("resource_type", params.resourceType);
    if (params?.action) sp.set("action", params.action);
    const qs = sp.toString();
    return request<AuditEventList>(`/audit-log${qs ? `?${qs}` : ""}`);
  },

  listDepartments: () => request<DepartmentList>("/departments"),

  createDepartment: (input: DepartmentCreate) =>
    request<Department>("/departments", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  updateDepartment: (id: string, input: DepartmentUpdate) =>
    request<Department>(`/departments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),

  deleteDepartment: (id: string) =>
    request<void>(`/departments/${id}`, { method: "DELETE" }),

  listShiftRules: () => request<ShiftRuleList>("/shift-rules"),

  createShiftRule: (input: ShiftRuleCreate) =>
    request<ShiftRule>("/shift-rules", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  updateShiftRule: (id: string, input: ShiftRuleUpdate) =>
    request<ShiftRule>(`/shift-rules/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),

  deleteShiftRule: (id: string) =>
    request<void>(`/shift-rules/${id}`, { method: "DELETE" }),

  listTemplates: (employeeId: string) =>
    request<{
      items: {
        id: string;
        employee_id: string;
        source_device_id: string;
        finger_id: number;
        captured_at: string;
      }[];
      total: number;
    }>(`/employees/${employeeId}/templates`),

  pullTemplates: (employeeId: string, fromDeviceId: string) =>
    request<{ stored: number; fingers: number[] }>(
      `/employees/${employeeId}/templates/pull?from_device_id=${fromDeviceId}`,
      { method: "POST" },
    ),

  pushTemplates: (employeeId: string, deviceIds: string[]) =>
    request<{
      results: {
        device_id: string;
        status: "pushed" | "failed";
        fingers_pushed: number;
        error: string | null;
      }[];
    }>(`/employees/${employeeId}/templates/push`, {
      method: "POST",
      body: JSON.stringify({ device_ids: deviceIds }),
    }),

  getEmployee: (id: string) =>
    request<Employee>(`/employees/${id}`),

  listLeaveRequests: (
    status?: "pending" | "approved" | "rejected",
    page = 1,
    pageSize = 50,
  ) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (status) params.set("status", status);
    return request<{
      items: {
        id: string;
        employee_id: string;
        employee_code: string | null;
        employee_full_name: string | null;
        start_date: string;
        end_date: string;
        reason: string;
        status: "pending" | "approved" | "rejected";
        created_at: string;
        decided_at: string | null;
        decided_by_user_id: string | null;
      }[];
      total: number;
    }>(`/leave-requests?${params.toString()}`);
  },

  decideLeaveRequest: (id: string, decision: "approved" | "rejected") =>
    request<{ id: string; status: "approved" | "rejected" }>(
      `/leave-requests/${id}/decision`,
      {
        method: "PATCH",
        body: JSON.stringify({ decision }),
      },
    ),

  getPermissions: () => request<PermissionsMatrixResponse>("/permissions"),

  patchPermission: (role: UserRole, capability: string, granted: boolean) =>
    request<void>("/permissions", {
      method: "PATCH",
      body: JSON.stringify({ role, capability, granted }),
    }),

  // CSV download needs the bearer token, so a plain <a href> doesn't work.
  // We fetch as Blob and let the caller trigger a browser download.
  async downloadAttendanceCsv(
    employeeId: string,
    month: string,
  ): Promise<{ blob: Blob; filename: string }> {
    return downloadAttendanceBlob(employeeId, month, "csv");
  },

  async downloadAttendanceXlsx(
    employeeId: string,
    month: string,
  ): Promise<{ blob: Blob; filename: string }> {
    return downloadAttendanceBlob(employeeId, month, "xlsx");
  },
};

async function downloadAttendanceBlob(
  employeeId: string,
  month: string,
  format: "csv" | "xlsx",
): Promise<{ blob: Blob; filename: string }> {
  const token = getToken();
  const url = `${baseUrl}/reports/attendance.${format}?employee_id=${employeeId}&month=${month}`;
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
  const filename = match?.[1] ?? `attendance-${month}.${format}`;
  return { blob, filename };
}
