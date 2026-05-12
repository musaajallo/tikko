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
