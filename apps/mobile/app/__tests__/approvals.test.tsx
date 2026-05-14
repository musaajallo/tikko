import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import Approvals from "../approvals";

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue("a.b.c"),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock("expo-router", () => ({
  router: { replace: jest.fn(), push: jest.fn() },
}));

interface MockResp {
  ok: boolean;
  json: () => Promise<unknown>;
}

const PENDING_ONE = {
  id: "lr-1",
  employee_id: "emp-1",
  employee_code: "1042",
  employee_full_name: "Ada Lovelace",
  start_date: "2026-06-01",
  end_date: "2026-06-05",
  reason: "Family visit",
  status: "pending",
  created_at: "2026-05-14T08:00:00Z",
  decided_at: null,
  decided_by_user_id: null,
};

describe("Mobile approvals", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    (global as { fetch: typeof fetch }).fetch = originalFetch;
  });

  it("renders pending requests with the employee name and date range", async () => {
    const fetchMock = jest.fn(
      (url: string): Promise<MockResp> =>
        Promise.resolve({
          ok: true,
          json: async () =>
            /leave-requests/.test(url)
              ? { items: [PENDING_ONE], total: 1 }
              : {},
        }),
    );
    (global as { fetch: unknown }).fetch = fetchMock;

    render(<Approvals />);

    expect(await screen.findByText("Ada Lovelace")).toBeTruthy();
    expect(screen.getByText("#1042")).toBeTruthy();
    expect(screen.getByText("Family visit")).toBeTruthy();
  });

  it("renders an empty state when there are no pending requests", async () => {
    const fetchMock = jest.fn(
      (): Promise<MockResp> =>
        Promise.resolve({
          ok: true,
          json: async () => ({ items: [], total: 0 }),
        }),
    );
    (global as { fetch: unknown }).fetch = fetchMock;

    render(<Approvals />);
    expect(await screen.findByText(/no pending requests/i)).toBeTruthy();
  });

  it("PATCHes the decision and refetches when Approve is tapped", async () => {
    let listCallCount = 0;
    const fetchMock = jest.fn((url: string, init?: RequestInit) => {
      if (/\/leave-requests\/lr-1\/decision/.test(url) && init?.method === "PATCH") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...PENDING_ONE, status: "approved" }),
        });
      }
      if (/leave-requests/.test(url)) {
        listCallCount += 1;
        // First call: one pending. Second call (after decide): empty.
        if (listCallCount === 1) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [PENDING_ONE], total: 1 }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [], total: 0 }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    (global as { fetch: unknown }).fetch = fetchMock;

    render(<Approvals />);

    await screen.findByText("Ada Lovelace");
    fireEvent.press(screen.getByText("Approve"));

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(
        (c) =>
          /\/leave-requests\/lr-1\/decision/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "PATCH",
      );
      expect(patchCall).toBeDefined();
      expect(JSON.parse((patchCall![1] as RequestInit).body as string)).toEqual({
        decision: "approved",
      });
    });

    // The list refetches and now shows the empty state.
    await screen.findByText(/no pending requests/i);
  });

  it("PATCHes with decision=rejected when Reject is tapped", async () => {
    const fetchMock = jest.fn((url: string, init?: RequestInit) => {
      if (/\/leave-requests\/lr-1\/decision/.test(url) && init?.method === "PATCH") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...PENDING_ONE, status: "rejected" }),
        });
      }
      if (/leave-requests/.test(url)) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [PENDING_ONE], total: 1 }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    (global as { fetch: unknown }).fetch = fetchMock;

    render(<Approvals />);

    await screen.findByText("Ada Lovelace");
    fireEvent.press(screen.getByText("Reject"));

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(
        (c) =>
          /\/leave-requests\/lr-1\/decision/.test(c[0] as string) &&
          (c[1] as RequestInit | undefined)?.method === "PATCH",
      );
      expect(patchCall).toBeDefined();
      expect(JSON.parse((patchCall![1] as RequestInit).body as string)).toEqual({
        decision: "rejected",
      });
    });
  });
});
