import * as SecureStore from "expo-secure-store";

import { clearToken, getToken, setToken } from "../auth";

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe("auth token storage (SecureStore)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("reads the token from SecureStore", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce("a.b.c");
    expect(await getToken()).toBe("a.b.c");
    expect(SecureStore.getItemAsync).toHaveBeenCalledWith("tikko.access_token");
  });

  it("writes the access and refresh tokens", async () => {
    await setToken("a.b.c", "r.r.r");
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith("tikko.access_token", "a.b.c");
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith("tikko.refresh_token", "r.r.r");
  });

  it("clears both keys", async () => {
    await clearToken();
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith("tikko.access_token");
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith("tikko.refresh_token");
  });
});
