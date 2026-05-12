import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DevicesPage from "../page";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

describe("Devices page", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders devices fetched from the api in a table", async () => {
    fetchMock.mockResolvedValueOnce({
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
    });

    render(<DevicesPage />);

    await waitFor(() => {
      expect(screen.getByText("Front gate")).toBeInTheDocument();
      expect(screen.getByText("192.168.1.50:4370")).toBeInTheDocument();
    });
  });

  it("opens the add-device dialog and posts a new device", async () => {
    // initial GET /devices — empty
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [], total: 0 }),
    });
    // POST /devices
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: "id-2",
        name: "Lobby",
        host: "10.0.0.5",
        port: 4370,
        location: null,
        created_at: "2026-05-12T08:01:00Z",
      }),
    });
    // refetch after POST
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "id-2",
            name: "Lobby",
            host: "10.0.0.5",
            port: 4370,
            location: null,
            created_at: "2026-05-12T08:01:00Z",
          },
        ],
        total: 1,
      }),
    });

    render(<DevicesPage />);

    // Wait for the empty state then click the header trigger (first of two
    // "Add device" buttons; the second is the empty-state CTA).
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

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const postCall = fetchMock.mock.calls[1];
    expect(postCall[0]).toMatch(/\/devices$/);
    expect(postCall[1]?.method).toBe("POST");
  });
});
