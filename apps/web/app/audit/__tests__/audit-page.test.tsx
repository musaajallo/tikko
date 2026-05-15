import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AuditPage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

interface MockResponse {
  ok: boolean;
  status?: number;
  json: () => Promise<unknown>;
  text?: () => Promise<string>;
}

const TWO_EVENTS: MockResponse = {
  ok: true,
  json: async () => ({
    items: [
      {
        id: "ev-1",
        actor_user_id: "u-1",
        action: "create_employee",
        resource_type: "employee",
        resource_id: "emp-1",
        before: null,
        after: { employee_code: "1042", full_name: "Ada" },
        created_at: "2026-05-15T08:00:00Z",
      },
      {
        id: "ev-2",
        actor_user_id: "u-1",
        action: "update_user_role",
        resource_type: "user",
        resource_id: "u-2",
        before: { role: "employee" },
        after: { role: "manager" },
        created_at: "2026-05-15T08:05:00Z",
      },
    ],
    total: 2,
  }),
};

describe("Audit page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders events from the api", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(TWO_EVENTS)),
    );

    render(<AuditPage />);

    await waitFor(() => {
      expect(screen.getByText("create_employee")).toBeInTheDocument();
      expect(screen.getByText("update_user_role")).toBeInTheDocument();
    });
  });

  it("sends filter values on the next /audit-log request", async () => {
    const fetchMock = vi.fn((_url: string, _init?: RequestInit) =>
      Promise.resolve(TWO_EVENTS),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<AuditPage />);
    await waitFor(() => {
      expect(screen.getByText("create_employee")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/resource type/i), {
      target: { value: "employee" },
    });
    fireEvent.change(screen.getByLabelText(/^action$/i), {
      target: { value: "create_employee" },
    });
    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      const filtered = fetchMock.mock.calls.find(
        (c) =>
          /resource_type=employee/.test(c[0] as string) &&
          /action=create_employee/.test(c[0] as string),
      );
      expect(filtered).toBeDefined();
    });
  });
});
