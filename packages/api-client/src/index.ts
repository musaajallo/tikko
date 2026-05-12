import createOpenapiClient from "openapi-fetch";

export { DeployMode, UserRole } from "@tikko/shared-types";
export type { Device, DevicePunch } from "@tikko/shared-types";
export { DeviceSchema, DevicePunchSchema } from "@tikko/shared-types";

export interface TikkoClientConfig {
  baseUrl: string;
  /** Bearer token; omit for unauthenticated calls (e.g. /health, /auth/login). */
  token?: string;
}

/**
 * Returns an openapi-fetch client. Until codegen runs (after F07's first
 * endpoint lands), the client is loosely typed; the script `pnpm codegen`
 * regenerates `src/generated/schema.d.ts` from the live API.
 */
export function createTikkoClient(config: TikkoClientConfig) {
  return createOpenapiClient({
    baseUrl: config.baseUrl,
    headers: config.token ? { Authorization: `Bearer ${config.token}` } : undefined,
  });
}
