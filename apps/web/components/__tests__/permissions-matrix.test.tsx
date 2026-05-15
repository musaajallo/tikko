import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PermissionsMatrix } from "../permissions-matrix";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

interface MockResp {
  ok: boolean;
  status?: number;
  json: () => Promise<unknown>;
  text?: () => Promise<string>;
}

const MATRIX_BODY = {
  matrix: {
    admin: ["manage_devices", "view_devices", "manage_permissions"],
    manager: ["view_devices"],
    employee: [],
  },
  all_roles: ["admin", "manager", "employee"],
  all_capabilities: ["view_devices", "manage_devices", "manage_permissions"],
};

describe("PermissionsMatrix (dynamic)", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders a row per capability and a column per role", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({ ok: true, json: async () => MATRIX_BODY } as MockResp),
      ),
    );

    render(<PermissionsMatrix />);

    await screen.findByText(/View devices/i);
    expect(screen.getByText(/Add \/ edit \/ delete devices/i)).toBeInTheDocument();
    // 3 capabilities × 3 roles = 9 checkboxes.
    const boxes = await screen.findAllByRole("checkbox");
    expect(boxes.length).toBe(9);
  });

  it("PATCHes /permissions when a cell toggles", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (/\/permissions/.test(url) && init?.method === "PATCH") {
        return Promise.resolve({
          ok: true,
          status: 204,
          json: async () => ({}),
          text: async () => "",
        } as MockResp);
      }
      return Promise.resolve({ ok: true, json: async () => MATRIX_BODY } as MockResp);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<PermissionsMatrix />);

    // Wait until checkboxes exist, then toggle manage_devices for manager.
    const box = await screen.findByLabelText(/manage_devices for manager/i);
    fireEvent.click(box);

    await waitFor(() => {
      const patch = fetchMock.mock.calls.find(
        (c) =>
          /\/permissions/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "PATCH",
      );
      expect(patch).toBeDefined();
      expect(JSON.parse((patch![1] as RequestInit).body as string)).toEqual({
        role: "manager",
        capability: "manage_devices",
        granted: true,
      });
    });
  });
});
