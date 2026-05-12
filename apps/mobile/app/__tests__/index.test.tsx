import { render, screen } from "@testing-library/react-native";

import Index from "../index";

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
