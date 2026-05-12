import { describe, expect, it } from "vitest";

import { DeployMode, DevicePunchSchema, DeviceSchema, UserRole } from "./index";

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
});
