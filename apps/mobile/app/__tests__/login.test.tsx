import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import * as SecureStore from "expo-secure-store";

import Login from "../login";

const mockReplace = jest.fn();

jest.mock("expo-router", () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
}));

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe("Mobile login screen", () => {
  const originalFetch = global.fetch;
  let fetchMock: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    fetchMock = jest.fn();
    (global as { fetch: typeof fetch }).fetch = fetchMock as unknown as typeof fetch;
  });

  afterAll(() => {
    (global as { fetch: typeof fetch }).fetch = originalFetch;
  });

  it("stores the token on a successful login and redirects home", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "a.b.c",
        refresh_token: "r.r.r",
        token_type: "bearer",
      }),
    });

    render(<Login />);

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "admin@tikko.local");
    fireEvent.changeText(screen.getByPlaceholderText("Password"), "supersecret123");
    fireEvent.press(screen.getByRole("button"));

    await waitFor(() => {
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        "tikko.access_token",
        "a.b.c",
      );
      expect(mockReplace).toHaveBeenCalledWith("/");
    });
  });
});
