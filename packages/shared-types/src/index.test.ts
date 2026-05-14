import { describe, expect, it } from "vitest";

import {
  DeployMode,
  DevicePunchSchema,
  DeviceSchema,
  EmployeeSchema,
  EmployeeStatus,
  EmployeeSyncEntrySchema,
  UserRole,
} from "./index";

describe("DeviceSchema", () => {
  it("accepts a valid device", () => {
    const parsed = DeviceSchema.parse({
      id: "550e8400-e29b-41d4-a716-446655440000",
      name: "Front gate",
      host: "192.168.1.50",
      port: 4370,
      location: "HQ entrance",
      created_at: "2026-01-01T00:00:00Z",
    });
    expect(parsed.name).toBe("Front gate");
  });

  it("defaults port to 4370", () => {
    const parsed = DeviceSchema.parse({
      id: "550e8400-e29b-41d4-a716-446655440000",
      name: "Front gate",
      host: "192.168.1.50",
      created_at: "2026-01-01T00:00:00Z",
    });
    expect(parsed.port).toBe(4370);
    expect(parsed.location).toBeNull();
  });

  it("rejects an out-of-range port", () => {
    expect(() =>
      DeviceSchema.parse({
        id: "550e8400-e29b-41d4-a716-446655440000",
        name: "Front gate",
        host: "192.168.1.50",
        port: 99999,
        created_at: "2026-01-01T00:00:00Z",
      }),
    ).toThrow();
  });
});

describe("DevicePunchSchema", () => {
  it("parses a punch from the ZK protocol shape", () => {
    const parsed = DevicePunchSchema.parse({
      id: "550e8400-e29b-41d4-a716-446655440001",
      device_id: "550e8400-e29b-41d4-a716-446655440000",
      device_user_id: "1042",
      punched_at: "2026-05-12T08:15:00Z",
      punch_type: 0,
      verify_mode: 1,
    });
    expect(parsed.device_user_id).toBe("1042");
  });
});

describe("enums", () => {
  it("exposes DeployMode values", () => {
    expect(DeployMode.LAN).toBe("lan");
    expect(DeployMode.CLOUD).toBe("cloud");
  });

  it("exposes UserRole values", () => {
    expect(UserRole.ADMIN).toBe("admin");
    expect(UserRole.MANAGER).toBe("manager");
    expect(UserRole.EMPLOYEE).toBe("employee");
  });

  it("exposes EmployeeStatus values", () => {
    expect(EmployeeStatus.ACTIVE).toBe("active");
    expect(EmployeeStatus.INACTIVE).toBe("inactive");
    expect(EmployeeStatus.TERMINATED).toBe("terminated");
  });
});

describe("EmployeeSchema", () => {
  it("parses a valid employee", () => {
    const parsed = EmployeeSchema.parse({
      id: "550e8400-e29b-41d4-a716-446655440000",
      employee_code: "1042",
      full_name: "Ada Lovelace",
      status: "active",
      created_at: "2026-05-14T08:00:00Z",
      updated_at: "2026-05-14T08:00:00Z",
    });
    expect(parsed.employee_code).toBe("1042");
  });

  it("rejects a non-numeric employee_code", () => {
    expect(() =>
      EmployeeSchema.parse({
        id: "550e8400-e29b-41d4-a716-446655440000",
        employee_code: "ABC-1",
        full_name: "x",
        status: "active",
        created_at: "2026-05-14T08:00:00Z",
        updated_at: "2026-05-14T08:00:00Z",
      }),
    ).toThrow();
  });
});

describe("EmployeeSyncEntrySchema", () => {
  it("parses a synced entry", () => {
    const parsed = EmployeeSyncEntrySchema.parse({
      device_id: "550e8400-e29b-41d4-a716-446655440000",
      status: "synced",
      error: null,
    });
    expect(parsed.status).toBe("synced");
  });

  it("parses a failed entry with an error string", () => {
    const parsed = EmployeeSyncEntrySchema.parse({
      device_id: "550e8400-e29b-41d4-a716-446655440000",
      status: "failed",
      error: "connect timeout",
    });
    expect(parsed.error).toBe("connect timeout");
  });
});
