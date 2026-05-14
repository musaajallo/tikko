import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
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

const USERS_TWO: MockResponse = {
  ok: true,
  json: async () => ({
    items: [
      {
        id: "u-admin",
        email: "admin@example.com",
        role: "admin",
        employee_id: null,
        created_at: "2026-05-01T00:00:00Z",
      },
      {
        id: "u-emp",
        email: "ada@example.com",
        role: "employee",
        employee_id: "emp-1",
        created_at: "2026-05-02T00:00:00Z",
      },
    ],
    total: 2,
  }),
};

const RULES_ONE: MockResponse = {
  ok: true,
  json: async () => ({
    items: [
      {
        id: "r-1",
        name: "Standard 9-5",
        start_time: "09:00:00",
        end_time: "17:00:00",
        late_grace_minutes: 10,
        early_out_grace_minutes: 0,
        overtime_threshold_minutes: 30,
        work_days: "1111100",
        created_at: "2026-05-01T00:00:00Z",
        updated_at: "2026-05-01T00:00:00Z",
      },
    ],
    total: 1,
  }),
};

const RULES_EMPTY: MockResponse = {
  ok: true,
  json: async () => ({ items: [], total: 0 }),
};

describe("Settings page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders users and shift rules tables", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
        if (/\/users/.test(url)) return Promise.resolve(USERS_TWO);
        if (/\/shift-rules/.test(url)) return Promise.resolve(RULES_ONE);
        return Promise.resolve(STATS_RESPONSE);
      }),
    );

    render(<SettingsPage />);

    expect(await screen.findByText("admin@example.com")).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(await screen.findByText("Standard 9-5")).toBeInTheDocument();
    expect(screen.getByText("09:00–17:00")).toBeInTheDocument();
  });

  it("PATCHes /users/:id/role when the role select changes", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/users\/u-emp\/role/.test(url) && init?.method === "PATCH") {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            id: "u-emp",
            email: "ada@example.com",
            role: "manager",
            employee_id: "emp-1",
            created_at: "2026-05-02T00:00:00Z",
          }),
        });
      }
      if (/\/users/.test(url)) return Promise.resolve(USERS_TWO);
      if (/\/shift-rules/.test(url)) return Promise.resolve(RULES_EMPTY);
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);
    await screen.findByText("ada@example.com");

    fireEvent.change(screen.getByLabelText(/role for ada@example.com/i), {
      target: { value: "manager" },
    });

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        (c) =>
          /\/users\/u-emp\/role/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "PATCH",
      );
      expect(call).toBeDefined();
      expect(JSON.parse((call![1] as RequestInit).body as string)).toEqual({
        role: "manager",
      });
    });
  });

  it("opens the Add rule dialog and POSTs a new shift rule", async () => {
    let ruleListCalls = 0;
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/users/.test(url)) return Promise.resolve(USERS_TWO);
      if (/\/shift-rules$/.test(url) && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: "r-new",
            name: "New rule",
            start_time: "09:00:00",
            end_time: "17:00:00",
            late_grace_minutes: 0,
            early_out_grace_minutes: 0,
            overtime_threshold_minutes: 30,
            work_days: "1111100",
            created_at: "2026-05-14T00:00:00Z",
            updated_at: "2026-05-14T00:00:00Z",
          }),
        });
      }
      if (/\/shift-rules/.test(url)) {
        ruleListCalls += 1;
        return Promise.resolve(ruleListCalls === 1 ? RULES_EMPTY : RULES_ONE);
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);
    await screen.findByText(/no shift rules yet/i);

    fireEvent.click(screen.getByRole("button", { name: /add rule/i }));

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(
      dialog.querySelector<HTMLInputElement>("input#rule_name")!,
      { target: { value: "New rule" } },
    );
    fireEvent.click(dialog.querySelector<HTMLButtonElement>('button[type="submit"]')!);

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(
        (c) =>
          /\/shift-rules$/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "POST",
      );
      expect(post).toBeDefined();
      const body = JSON.parse((post![1] as RequestInit).body as string);
      expect(body.name).toBe("New rule");
      expect(body.start_time).toBe("09:00:00");
      expect(body.work_days).toBe("1111100");
    });
  });

  it("DELETEs a shift rule via the row action", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/users/.test(url)) return Promise.resolve(USERS_TWO);
      if (/\/shift-rules\/r-1$/.test(url) && init?.method === "DELETE") {
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => ({}),
          text: async () => "",
        });
      }
      if (/\/shift-rules/.test(url)) return Promise.resolve(RULES_ONE);
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);
    await screen.findByText("Standard 9-5");

    fireEvent.click(screen.getByRole("button", { name: /delete standard 9-5/i }));

    await waitFor(() => {
      const del = fetchMock.mock.calls.find(
        (c) =>
          /\/shift-rules\/r-1$/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "DELETE",
      );
      expect(del).toBeDefined();
    });
  });
});
