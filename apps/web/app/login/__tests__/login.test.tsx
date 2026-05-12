import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getToken } from "@/lib/auth";

import LoginPage from "../page";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("Login page", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    pushMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("stores the access token and redirects to /devices on success", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "a.b.c",
        refresh_token: "r.r.r",
        token_type: "bearer",
      }),
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: "admin@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText(/password/i), {
      target: { value: "supersecret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(getToken()).toBe("a.b.c");
      expect(pushMock).toHaveBeenCalledWith("/devices");
    });
  });

  it("shows an error message on 401 and does not redirect", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      text: async () => "{}",
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/email/i), {
      target: { value: "wrong@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText(/password/i), {
      target: { value: "nope" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials|401/i)).toBeInTheDocument();
    });
    expect(getToken()).toBeNull();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
