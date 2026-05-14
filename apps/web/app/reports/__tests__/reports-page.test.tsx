import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ReportsPage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

interface MockResponse {
  ok: boolean;
  status?: number;
  json: () => Promise<unknown>;
  text?: () => Promise<string>;
  blob?: () => Promise<Blob>;
  headers?: Headers | { get(name: string): string | null };
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

const EMPLOYEES_RESPONSE: MockResponse = {
  ok: true,
  json: async () => ({
    items: [
      {
        id: "emp-1",
        employee_code: "1042",
        full_name: "Ada Lovelace",
        status: "active",
        created_at: "2026-05-01T00:00:00Z",
        updated_at: "2026-05-01T00:00:00Z",
      },
    ],
    total: 1,
  }),
};

const REPORT_RESPONSE: MockResponse = {
  ok: true,
  json: async () => ({
    month: "2026-05",
    employee: { id: "emp-1", employee_code: "1042", full_name: "Ada Lovelace" },
    days: [
      {
        date: "2026-05-14",
        is_workday: true,
        is_absent: false,
        first_in: "2026-05-14T09:00:00+00:00",
        last_out: "2026-05-14T17:00:00+00:00",
        worked_minutes: 480,
        late_minutes: 0,
        early_out_minutes: 0,
        overtime_minutes: 0,
      },
      {
        date: "2026-05-15",
        is_workday: true,
        is_absent: true,
        first_in: null,
        last_out: null,
        worked_minutes: 0,
        late_minutes: 0,
        early_out_minutes: 0,
        overtime_minutes: 0,
      },
    ],
    totals: {
      days_worked: 1,
      days_absent: 1,
      worked_minutes: 480,
      late_minutes: 0,
      early_out_minutes: 0,
      overtime_minutes: 0,
    },
  }),
};

describe("Reports page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the filter form with employees loaded into the select", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/employees/.test(url)) return Promise.resolve(EMPLOYEES_RESPONSE);
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Ada Lovelace/)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/month/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^run report$/i })).toBeInTheDocument();
  });

  it("submits and renders daily rows + totals", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/employees/.test(url) && !/\/sync/.test(url)) return Promise.resolve(EMPLOYEES_RESPONSE);
      if (/\/reports\/attendance/.test(url)) return Promise.resolve(REPORT_RESPONSE);
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<ReportsPage />);

    await screen.findByText(/Ada Lovelace/);
    fireEvent.change(screen.getByLabelText(/month/i), {
      target: { value: "2026-05" },
    });
    await user.click(screen.getByRole("button", { name: /^run report$/i }));

    await waitFor(() => {
      expect(screen.getByText("2026-05-14")).toBeInTheDocument();
      expect(screen.getByText("2026-05-15")).toBeInTheDocument();
    });

    // Totals card renders KPI labels (Days worked + Days absent + per-row table cells).
    expect(await screen.findByText(/days worked/i)).toBeInTheDocument();
    expect(screen.getByText(/days absent/i)).toBeInTheDocument();
  });

  it("renders a friendly message when the employee has no shift rule (422)", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/employees/.test(url)) return Promise.resolve(EMPLOYEES_RESPONSE);
      if (/\/reports\/attendance/.test(url)) {
        return Promise.resolve({
          ok: false,
          status: 422,
          json: async () => ({ detail: "employee has no assigned shift rule" }),
          text: async () => "employee has no assigned shift rule",
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<ReportsPage />);

    await screen.findByText(/Ada Lovelace/);
    fireEvent.change(screen.getByLabelText(/month/i), {
      target: { value: "2026-05" },
    });
    await user.click(screen.getByRole("button", { name: /^run report$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/no assigned shift rule|assign a shift rule|422/i),
      ).toBeInTheDocument();
    });
  });

  it("clicking Download CSV fetches the .csv endpoint", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/employees/.test(url)) return Promise.resolve(EMPLOYEES_RESPONSE);
      if (/\/reports\/attendance\.csv/.test(url)) {
        return Promise.resolve({
          ok: true,
          status: 200,
          blob: async () => new Blob(["a,b\n1,2"], { type: "text/csv" }),
          json: async () => ({}),
          text: async () => "",
          headers: {
            get: (n: string) =>
              n.toLowerCase() === "content-disposition"
                ? 'attachment; filename="attendance-1042-2026-05.csv"'
                : null,
          },
        });
      }
      if (/\/reports\/attendance/.test(url)) return Promise.resolve(REPORT_RESPONSE);
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    // Block the actual download attempt — jsdom can't drive it and we just want
    // to confirm the network call.
    const createObjectURL = vi.fn(() => "blob:test");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });

    const user = userEvent.setup();
    render(<ReportsPage />);

    await screen.findByText(/Ada Lovelace/);
    fireEvent.change(screen.getByLabelText(/month/i), {
      target: { value: "2026-05" },
    });
    await user.click(screen.getByRole("button", { name: /download csv/i }));

    await waitFor(() => {
      const csvCall = fetchMock.mock.calls.find((c) =>
        /\/reports\/attendance\.csv\?employee_id=emp-1&month=2026-05/.test(c[0] as string),
      );
      expect(csvCall).toBeDefined();
    });
  });
});
