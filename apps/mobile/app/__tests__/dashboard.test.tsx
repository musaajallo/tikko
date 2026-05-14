import { render, screen, waitFor } from "@testing-library/react-native";

import Dashboard from "../dashboard";

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue("a.b.c"),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
}));

interface MockResp {
  ok: boolean;
  json: () => Promise<unknown>;
}

function routeFetch(handlers: { url: RegExp; resp: MockResp }[]) {
  return jest.fn((url: string) => {
    const match = handlers.find((h) => h.url.test(url));
    return Promise.resolve(match?.resp ?? { ok: false, json: async () => ({}) });
  });
}

const ME_LINKED: MockResp = {
  ok: true,
  json: async () => ({
    user: {
      id: "u1",
      email: "ada@example.com",
      role: "employee",
      employee_id: "e1",
      created_at: "2026-05-01T00:00:00Z",
    },
    employee: {
      id: "e1",
      employee_code: "1042",
      full_name: "Ada Lovelace",
      status: "active",
      created_at: "2026-05-01T00:00:00Z",
      updated_at: "2026-05-01T00:00:00Z",
    },
  }),
};

describe("Mobile dashboard", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    (global as { fetch: typeof fetch }).fetch = originalFetch;
  });

  it("renders the linked employee name, monthly KPIs, and recent punches", async () => {
    (global as { fetch: unknown }).fetch = routeFetch([
      { url: /\/auth\/me/, resp: ME_LINKED },
      {
        url: /\/me\/attendance\/summary/,
        resp: {
          ok: true,
          json: async () => ({
            month: "2026-05",
            total_punches: 23,
            days_present: 12,
          }),
        },
      },
      {
        url: /\/me\/attendance/,
        resp: {
          ok: true,
          json: async () => ({
            items: [
              {
                id: "p1",
                device_id: "d1",
                device_user_id: "1042",
                punched_at: "2026-05-14T08:00:00Z",
                punch_type: 0,
                verify_mode: 1,
              },
              {
                id: "p2",
                device_id: "d1",
                device_user_id: "1042",
                punched_at: "2026-05-14T17:00:00Z",
                punch_type: 1,
                verify_mode: 1,
              },
            ],
            total: 2,
          }),
        },
      },
    ]);

    render(<Dashboard />);

    expect(await screen.findByText(/Ada Lovelace/i)).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByText("23")).toBeTruthy(); // total_punches
      expect(screen.getByText("12")).toBeTruthy(); // days_present
    });
    // Two recent punches rendered.
    expect(screen.getAllByText("1042")).toHaveLength(2);
  });

  it("redirects to /feed when the user has no linked employee", async () => {
    (global as { fetch: unknown }).fetch = routeFetch([
      {
        url: /\/auth\/me/,
        resp: {
          ok: true,
          json: async () => ({
            user: {
              id: "u2",
              email: "admin@example.com",
              role: "admin",
              employee_id: null,
              created_at: "2026-05-01T00:00:00Z",
            },
            employee: null,
          }),
        },
      },
    ]);

    render(<Dashboard />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/feed");
    });
  });
});
