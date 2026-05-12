import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { clearToken, getToken, setToken } from "../auth";

describe("auth token storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });
  afterEach(() => {
    window.localStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(getToken()).toBeNull();
  });

  it("round-trips a token through localStorage", () => {
    setToken("abc.def.ghi");
    expect(getToken()).toBe("abc.def.ghi");
  });

  it("clears the stored token", () => {
    setToken("xyz");
    clearToken();
    expect(getToken()).toBeNull();
  });
});
