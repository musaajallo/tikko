import { render, screen } from "@testing-library/react-native";

import Index from "../index";

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue(null),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock("expo-router", () => ({
  router: { replace: jest.fn(), push: jest.fn() },
}));

describe("Home screen", () => {
  it("renders the tikko heading", () => {
    render(<Index />);
    expect(screen.getByText("tikko")).toBeTruthy();
  });

  it("shows a tagline", () => {
    render(<Index />);
    expect(screen.getByText(/attendance/i)).toBeTruthy();
  });
});
