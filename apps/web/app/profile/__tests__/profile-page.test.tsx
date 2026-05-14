import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ProfilePage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

// QRCode is dynamically imported by ProfilePage but its only public surface
// here is `.toDataURL` which we stub. Avoids hitting Canvas in jsdom.
vi.mock("qrcode", () => ({
  default: {
    toDataURL: vi.fn().mockResolvedValue("data:image/png;base64,stub"),
  },
}));

interface MockResponse {
  ok: boolean;
  status?: number;
  json: () => Promise<unknown>;
  text?: () => Promise<string>;
}

const STATS_RESPONSE: MockResponse = {
  ok: true,
  json: async () => ({
    devices: 0,
    devices_enabled: 0,
    devices_online: 0,
    punches_today: 0,
    punches_24h: 0,
  }),
};

const ME_RESPONSE: MockResponse = {
  ok: true,
  json: async () => ({
    user: {
      id: "u-1",
      email: "ada@example.com",
      role: "admin",
      employee_id: "emp-1",
      created_at: "2026-05-14T08:00:00Z",
    },
    employee: {
      id: "emp-1",
      employee_code: "1042",
      full_name: "Ada Lovelace",
      status: "active",
      created_at: "2026-05-14T08:00:00Z",
      updated_at: "2026-05-14T08:00:00Z",
    },
  }),
};

describe("Profile page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders account info from /auth/me", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
        if (/\/auth\/me/.test(url)) return Promise.resolve(ME_RESPONSE);
        return Promise.resolve(STATS_RESPONSE);
      }),
    );

    render(<ProfilePage />);

    expect(await screen.findByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText(/Ada Lovelace/)).toBeInTheDocument();
  });

  it("submits the change-password form", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/auth\/me/.test(url)) return Promise.resolve(ME_RESPONSE);
      if (/\/auth\/change-password/.test(url) && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => ({}),
          text: async () => "",
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ProfilePage />);
    await screen.findByText("ada@example.com");

    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "supersecret123" },
    });
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "evenbetterpassword456" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update password/i }));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        (c) =>
          /\/auth\/change-password/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      );
      expect(call).toBeDefined();
      expect(JSON.parse((call![1] as RequestInit).body as string)).toEqual({
        current_password: "supersecret123",
        new_password: "evenbetterpassword456",
      });
    });
  });

  it("opens the enroll dialog and fetches /auth/totp/enroll", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/auth\/me/.test(url)) return Promise.resolve(ME_RESPONSE);
      if (/\/auth\/totp\/enroll/.test(url) && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            secret: "SECRET-B32",
            otpauth_uri: "otpauth://totp/tikko:ada@example.com?secret=SECRET-B32",
            enabled: false,
          }),
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<ProfilePage />);
    await screen.findByText("ada@example.com");

    await user.click(screen.getByRole("button", { name: /enable two-factor/i }));

    expect(await screen.findByText(/scan the qr/i)).toBeInTheDocument();
    expect(screen.getByText("SECRET-B32")).toBeInTheDocument();
  });

  it("opens the disable dialog and requires a password", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/auth\/me/.test(url)) return Promise.resolve(ME_RESPONSE);
      if (/\/auth\/totp\/enroll/.test(url)) {
        // Simulate "already enabled" 409 so the page flips to Disabled-CTA state.
        return Promise.resolve({
          ok: false,
          status: 409,
          json: async () => ({ detail: "TOTP already enabled" }),
          text: async () => "TOTP already enabled",
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<ProfilePage />);
    await screen.findByText("ada@example.com");

    // First click hits enroll → server says 409 → page learns TOTP is on.
    await user.click(screen.getByRole("button", { name: /enable two-factor/i }));

    // Disable button now appears.
    const disableBtn = await screen.findByRole("button", { name: /^disable$/i });
    await user.click(disableBtn);

    expect(await screen.findByText(/confirm your password/i)).toBeInTheDocument();
  });
});
