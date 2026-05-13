import { render, screen, waitFor } from "@testing-library/react-native";
import { act } from "react";

import Feed from "../feed";

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue("a.b.c"),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const mockReplace = jest.fn();
jest.mock("expo-router", () => ({
  router: { replace: (...args: unknown[]) => mockReplace(...args) },
}));

interface FakeSocket {
  url: string;
  onopen: ((e: Event) => void) | null;
  onmessage: ((e: MessageEvent) => void) | null;
  onclose: ((e: CloseEvent) => void) | null;
  onerror: ((e: Event) => void) | null;
  close: jest.Mock;
}

describe("Mobile feed", () => {
  let lastSocket: FakeSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    class FakeWebSocket implements FakeSocket {
      onopen: ((e: Event) => void) | null = null;
      onmessage: ((e: MessageEvent) => void) | null = null;
      onclose: ((e: CloseEvent) => void) | null = null;
      onerror: ((e: Event) => void) | null = null;
      close = jest.fn();
      constructor(public url: string) {
        lastSocket = this;
      }
    }
    (global as { WebSocket: unknown }).WebSocket = FakeWebSocket;
  });

  it("connects to /ws/attendance with the stored access token", async () => {
    render(<Feed />);
    await waitFor(() => expect(lastSocket).toBeDefined());
    expect(lastSocket.url).toMatch(/\/ws\/attendance\?token=a\.b\.c$/);
  });

  it("renders incoming attendance events", async () => {
    render(<Feed />);
    await waitFor(() => expect(lastSocket).toBeDefined());

    act(() => {
      lastSocket.onmessage?.(
        new MessageEvent("message", {
          data: JSON.stringify({
            type: "attendance.created",
            device_id: "d-1",
            device_user_id: "1042",
            punched_at: "2026-05-13T08:00:00+00:00",
            punch_type: 0,
            verify_mode: 1,
          }),
        }),
      );
    });

    expect(await screen.findByText("1042")).toBeTruthy();
  });
});
