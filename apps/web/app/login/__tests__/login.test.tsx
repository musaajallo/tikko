import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getToken } from "@/lib/auth";

import LoginPage from "../page";

const REMEMBER_EMAIL_KEY = "tikko.remembered_email";

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

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "admin@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "supersecret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(getToken()).toBe("a.b.c");
      expect(pushMock).toHaveBeenCalledWith("/devices");
    });
  });

  it("persists the email when Remember me is checked", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "a.b.c",
        refresh_token: "r.r.r",
        token_type: "bearer",
      }),
    });

    const user = userEvent.setup();
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "remember@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "supersecret123" },
    });
    await user.click(screen.getByLabelText(/remember me/i));
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(window.localStorage.getItem(REMEMBER_EMAIL_KEY)).toBe(
        "remember@example.com",
      );
    });
  });

  it("prefills the email and ticks Remember me on mount when a previous session opted in", async () => {
    window.localStorage.setItem(REMEMBER_EMAIL_KEY, "ada@example.com");

    render(<LoginPage />);

    const emailField = screen.getByLabelText<HTMLInputElement>(/email/i);
    expect(emailField.value).toBe("ada@example.com");
    expect(screen.getByLabelText(/remember me/i)).toBeChecked();
  });

  it("clears the stored email when Remember me is unchecked on a successful login", async () => {
    window.localStorage.setItem(REMEMBER_EMAIL_KEY, "ada@example.com");
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: "a.b.c",
        refresh_token: "r.r.r",
        token_type: "bearer",
      }),
    });

    const user = userEvent.setup();
    render(<LoginPage />);
    // Prefilled and checked → uncheck it.
    await user.click(screen.getByLabelText(/remember me/i));
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "supersecret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(window.localStorage.getItem(REMEMBER_EMAIL_KEY)).toBeNull();
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

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "wrong@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
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
