import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DevicesPage from "../page";

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

function routedFetch(routes: { url: RegExp; response: MockResponse }[]) {
  // Returns a fetch mock that picks a response based on URL match. Each route
  // can be consumed once; subsequent matching calls return the last response.
  const remaining = routes.map((r) => ({ ...r, used: false }));
  return vi.fn((url: string) => {
    const next =
      remaining.find((r) => !r.used && r.url.test(url)) ??
      remaining.findLast?.((r) => r.url.test(url)) ??
      remaining.find((r) => r.url.test(url));
    if (next) next.used = true;
    return Promise.resolve(next?.response ?? STATS_RESPONSE);
  });
}

describe("Devices page", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders devices fetched from the api in a table", async () => {
    const fetchMock = routedFetch([
      { url: /\/stats/, response: STATS_RESPONSE },
      {
        url: /\/devices$/,
        response: {
          ok: true,
          json: async () => ({
            items: [
              {
                id: "id-1",
                name: "Front gate",
                host: "192.168.1.50",
                port: 4370,
                location: "HQ",
                created_at: "2026-05-12T08:00:00Z",
              },
            ],
            total: 1,
          }),
        },
      },
    ]);
    vi.stubGlobal("fetch", fetchMock);

    render(<DevicesPage />);

    await waitFor(() => {
      expect(screen.getByText("Front gate")).toBeInTheDocument();
      expect(screen.getByText("192.168.1.50:4370")).toBeInTheDocument();
    });
  });

  it("opens the add-device dialog and posts a new device", async () => {
    const created = {
      id: "id-2",
      name: "Lobby",
      host: "10.0.0.5",
      port: 4370,
      location: null,
      created_at: "2026-05-12T08:01:00Z",
    };
    const fetchMock = vi.fn();
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (/\/stats/.test(url)) return Promise.resolve(STATS_RESPONSE);
      if (/\/devices$/.test(url) && init?.method === "POST") {
        return Promise.resolve({ ok: true, json: async () => created });
      }
      // GET /devices — empty until after POST
      if (fetchMock.mock.calls.filter((c) => /\/devices$/.test(c[0]) && !c[1]?.method).length > 1) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [created], total: 1 }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [], total: 0 }) });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DevicesPage />);

    await screen.findByText(/no devices yet/i);
    const [triggerButton] = screen.getAllByRole("button", { name: /add device/i });
    fireEvent.click(triggerButton);

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText(/name/i), {
      target: { value: "Lobby" },
    });
    fireEvent.change(within(dialog).getByLabelText(/host/i), {
      target: { value: "10.0.0.5" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: /add device/i }));

    await waitFor(() => {
      expect(screen.getByText("Lobby")).toBeInTheDocument();
    });

    const postCall = fetchMock.mock.calls.find(
      (c) => /\/devices$/.test(c[0]) && c[1]?.method === "POST",
    );
    expect(postCall).toBeDefined();
  });
});
