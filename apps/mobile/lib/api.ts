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

export interface UserMe {
  id: string;
  email: string;
  role: "admin" | "manager" | "employee";
  employee_id: string | null;
  created_at: string;
}

export interface EmployeeMe {
  id: string;
  employee_code: string;
  full_name: string;
  status: "active" | "inactive" | "terminated";
  created_at: string;
  updated_at: string;
}

export interface AuthMeResponse {
  user: UserMe;
  employee: EmployeeMe | null;
}

export interface AttendanceLog {
  id: string;
  device_id: string;
  device_user_id: string;
  punched_at: string;
  punch_type: number;
  verify_mode: number;
}

export interface AttendanceList {
  items: AttendanceLog[];
  total: number;
}

export interface AttendanceSummary {
  month: string;
  total_punches: number;
  days_present: number;
}

export type LeaveStatus = "pending" | "approved" | "rejected";

export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_code: string | null;
  employee_full_name: string | null;
  start_date: string; // YYYY-MM-DD
  end_date: string;
  reason: string;
  status: LeaveStatus;
  created_at: string;
  decided_at: string | null;
  decided_by_user_id: string | null;
}

export interface LeaveRequestList {
  items: LeaveRequest[];
  total: number;
}

export const api = {
  login: (input: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  getMe: () => request<AuthMeResponse>("/auth/me"),

  listMyAttendance: (page = 1, pageSize = 50) =>
    request<AttendanceList>(
      `/me/attendance?page=${page}&page_size=${pageSize}`,
    ),

  myMonthlySummary: (month: string) =>
    request<AttendanceSummary>(`/me/attendance/summary?month=${month}`),

  listLeaveRequests: (status?: LeaveStatus, page = 1, pageSize = 50) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (status) params.set("status", status);
    return request<LeaveRequestList>(`/leave-requests?${params.toString()}`);
  },

  decideLeaveRequest: (id: string, decision: "approved" | "rejected") =>
    request<LeaveRequest>(`/leave-requests/${id}/decision`, {
      method: "PATCH",
      body: JSON.stringify({ decision }),
    }),

  listMyLeaveRequests: (page = 1, pageSize = 20) =>
    request<LeaveRequestList>(
      `/me/leave-requests?page=${page}&page_size=${pageSize}`,
    ),
};
