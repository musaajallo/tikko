import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import EmployeesPage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
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

const EMPTY_DEVICES: MockResponse = {
  ok: true,
  json: async () => ({ items: [], total: 0 }),
};

describe("Employees page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders employees fetched from the api in a table", async () => {
    const employees = [
      {
        id: "emp-1",
        employee_code: "1042",
        full_name: "Ada Lovelace",
        status: "active",
        created_at: "2026-05-14T08:00:00Z",
        updated_at: "2026-05-14T08:00:00Z",
      },
      {
        id: "emp-2",
        employee_code: "2001",
        full_name: "Hal 9000",
        status: "terminated",
        created_at: "2026-05-14T08:01:00Z",
        updated_at: "2026-05-14T08:01:00Z",
      },
    ];
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices/.test(url)) return Promise.resolve(EMPTY_DEVICES);
      if (/\/employees/.test(url)) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: employees, total: employees.length }),
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<EmployeesPage />);

    await waitFor(() => {
      expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
      expect(screen.getByText("Hal 9000")).toBeInTheDocument();
      expect(screen.getByText("1042")).toBeInTheDocument();
    });
  });

  it("shows an empty state when there are no employees", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices/.test(url)) return Promise.resolve(EMPTY_DEVICES);
      return Promise.resolve({
        ok: true,
        json: async () => ({ items: [], total: 0 }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<EmployeesPage />);

    await screen.findByText(/no employees yet/i);
  });

  it("opens the add-employee dialog and posts a new employee", async () => {
    const created = {
      id: "emp-3",
      employee_code: "3007",
      full_name: "Grace Hopper",
      status: "active",
      created_at: "2026-05-14T08:02:00Z",
      updated_at: "2026-05-14T08:02:00Z",
    };
    const fetchMock = vi.fn();
    let employeeGets = 0;
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices/.test(url)) return Promise.resolve(EMPTY_DEVICES);
      if (/\/employees$/.test(url) && init?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => created });
      }
      if (/\/employees/.test(url)) {
        employeeGets += 1;
        // First GET empty, refetch after POST returns the created row.
        if (employeeGets === 1) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [], total: 0 }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [created], total: 1 }),
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<EmployeesPage />);

    await screen.findByText(/no employees yet/i);
    const [trigger] = screen.getAllByRole("button", { name: /add employee/i });
    fireEvent.click(trigger);

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText(/employee code/i), {
      target: { value: "3007" },
    });
    fireEvent.change(within(dialog).getByLabelText(/full name/i), {
      target: { value: "Grace Hopper" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: /add employee/i }));

    await waitFor(() => {
      expect(screen.getByText("Grace Hopper")).toBeInTheDocument();
    });

    const postCall = fetchMock.mock.calls.find(
      (c) => /\/employees$/.test(c[0]) && c[1]?.method === "POST",
    );
    expect(postCall).toBeDefined();
    expect(JSON.parse(postCall![1]!.body as string)).toMatchObject({
      employee_code: "3007",
      full_name: "Grace Hopper",
    });
  });

  it("opens the sync dialog and posts to /employees/:id/sync", async () => {
    const employee = {
      id: "emp-1",
      employee_code: "1042",
      full_name: "Ada Lovelace",
      status: "active",
      created_at: "2026-05-14T08:00:00Z",
      updated_at: "2026-05-14T08:00:00Z",
    };
    const device = {
      id: "dev-1",
      name: "Front gate",
      host: "10.0.0.1",
      port: 4370,
      location: null,
      created_at: "2026-05-14T07:00:00Z",
    };
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices/.test(url)) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [device], total: 1 }),
        });
      }
      if (/\/employees\/emp-1\/sync/.test(url) && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            results: [
              { device_id: device.id, status: "synced", error: null },
            ],
          }),
        });
      }
      if (/\/employees/.test(url)) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [employee], total: 1 }),
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<EmployeesPage />);

    await screen.findByText("Ada Lovelace");
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    await user.click(await screen.findByText(/sync to devices/i));

    // The dialog defaults to all devices selected, so just hit Sync.
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: /^sync$/i }));

    await waitFor(() => {
      const syncCall = fetchMock.mock.calls.find(
        (c) => /\/employees\/emp-1\/sync/.test(c[0]) && c[1]?.method === "POST",
      );
      expect(syncCall).toBeDefined();
      expect(JSON.parse(syncCall![1]!.body as string)).toEqual({
        device_ids: ["dev-1"],
      });
    });
  });

  it("deletes an employee via the row dropdown", async () => {
    const employee = {
      id: "emp-1",
      employee_code: "1042",
      full_name: "Ada Lovelace",
      status: "active",
      created_at: "2026-05-14T08:00:00Z",
      updated_at: "2026-05-14T08:00:00Z",
    };
    let employeeGets = 0;
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices/.test(url)) return Promise.resolve(EMPTY_DEVICES);
      if (/\/employees\/emp-1$/.test(url) && init?.method === "DELETE") {
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => ({}),
          text: async () => "",
        });
      }
      if (/\/employees/.test(url)) {
        employeeGets += 1;
        if (employeeGets === 1) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [employee], total: 1 }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [], total: 0 }),
        });
      }
      return Promise.resolve(STATS_RESPONSE);
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(<EmployeesPage />);

    await screen.findByText("Ada Lovelace");
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    await user.click(await screen.findByText(/delete/i));

    await waitFor(() => {
      const deleteCall = fetchMock.mock.calls.find(
        (c) => /\/employees\/emp-1$/.test(c[0]) && c[1]?.method === "DELETE",
      );
      expect(deleteCall).toBeDefined();
    });
  });
});
