import { z } from "zod";

/**
 * Single-deployable contract — mirrors `DeployMode` in `apps/api/src/tikko/settings.py`.
 * Only configures bindings/TLS/defaults; never branches business logic.
 */
export const DeployMode = {
  LAN: "lan",
  CLOUD: "cloud",
} as const;

export type DeployMode = (typeof DeployMode)[keyof typeof DeployMode];

export const DeviceSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  host: z.string().min(1),
  port: z.number().int().min(1).max(65535).default(4370),
  location: z.string().nullable().default(null),
  created_at: z.string().datetime(),
});

export type Device = z.infer<typeof DeviceSchema>;

export const DevicePunchSchema = z.object({
  id: z.string().uuid(),
  device_id: z.string().uuid(),
  device_user_id: z.string(),
  punched_at: z.string().datetime(),
  punch_type: z.number().int(),
  verify_mode: z.number().int(),
});

export type DevicePunch = z.infer<typeof DevicePunchSchema>;

export const UserRole = {
  ADMIN: "admin",
  MANAGER: "manager",
  EMPLOYEE: "employee",
} as const;

export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const EmployeeStatus = {
  ACTIVE: "active",
  INACTIVE: "inactive",
  TERMINATED: "terminated",
} as const;

export type EmployeeStatus =
  (typeof EmployeeStatus)[keyof typeof EmployeeStatus];

export const EmployeeSchema = z.object({
  id: z.string().uuid(),
  employee_code: z.string().regex(/^\d+$/),
  full_name: z.string().min(1),
  status: z.enum(["active", "inactive", "terminated"]),
  shift_rule_id: z.string().uuid().nullable().optional(),
  department_id: z.string().uuid().nullable().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export type Employee = z.infer<typeof EmployeeSchema>;

export const EmployeeSyncEntrySchema = z.object({
  device_id: z.string().uuid(),
  status: z.enum(["synced", "failed"]),
  error: z.string().nullable().default(null),
});

export type EmployeeSyncEntry = z.infer<typeof EmployeeSyncEntrySchema>;
