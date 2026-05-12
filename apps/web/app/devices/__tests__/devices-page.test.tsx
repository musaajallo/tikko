import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DevicesPage from "../page";

describe("Devices page", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists devices fetched from the api", async () => {
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

  it("submits a new device through the form", async () => {
    // initial GET /devices
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ items: [], total: 0 }) });
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

    await waitFor(() =>
      expect(screen.getByPlaceholderText(/name/i)).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByPlaceholderText(/name/i), { target: { value: "Lobby" } });
    fireEvent.change(screen.getByPlaceholderText(/host/i), { target: { value: "10.0.0.5" } });
    fireEvent.click(screen.getByRole("button", { name: /add device/i }));

    await waitFor(() => {
      expect(screen.getByText("Lobby")).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const postCall = fetchMock.mock.calls[1];
    expect(postCall[0]).toMatch(/\/devices$/);
    expect(postCall[1]?.method).toBe("POST");
  });
});
