import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AttendanceClient from "../AttendanceClient";

describe("AttendanceClient", () => {
  const fetchMock = vi.fn();
  const deviceId = "device-1";

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders punches fetched from the api", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "p-1",
            device_id: deviceId,
            device_user_id: "1042",
            punched_at: "2026-05-12T08:15:00Z",
            punch_type: 0,
            verify_mode: 1,
          },
        ],
        total: 1,
      }),
    });

    render(<AttendanceClient deviceId={deviceId} />);

    await waitFor(() => {
      expect(screen.getByText("1042")).toBeInTheDocument();
    });
  });

  it("polls the device and refetches when 'Poll now' is clicked", async () => {
    // initial list — empty
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [], total: 0 }),
    });
    // POST /devices/:id/poll
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ polled: 2, new: 2 }),
    });
    // refetch list
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "p-1",
            device_id: deviceId,
            device_user_id: "1099",
            punched_at: "2026-05-12T08:30:00Z",
            punch_type: 0,
            verify_mode: 1,
          },
        ],
        total: 1,
      }),
    });

    render(<AttendanceClient deviceId={deviceId} />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /poll now/i })).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: /poll now/i }));

    await waitFor(() => {
      expect(screen.getByText("1099")).toBeInTheDocument();
      expect(screen.getByText(/2 new/i)).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const pollCall = fetchMock.mock.calls[1];
    expect(pollCall[0]).toMatch(/\/devices\/device-1\/poll$/);
    expect(pollCall[1]?.method).toBe("POST");
  });
});
