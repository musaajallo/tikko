import { describe, expect, it } from "vitest";

import { createTikkoClient, DeployMode } from "./index";

describe("createTikkoClient", () => {
  it("returns a client object", () => {
    const client = createTikkoClient({ baseUrl: "http://localhost:8000" });
    expect(client).toBeTruthy();
    expect(typeof client.GET).toBe("function");
  });

  it("re-exports shared-types enums", () => {
    expect(DeployMode.LAN).toBe("lan");
  });
});
