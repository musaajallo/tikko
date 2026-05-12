import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Home from "../page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

describe("Home page", () => {
  it("renders the tikko heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /tikko/i })).toBeInTheDocument();
  });

  it("links to the devices page", () => {
    render(<Home />);
    const link = screen.getByRole("link", { name: /devices/i });
    expect(link).toHaveAttribute("href", "/devices");
  });
});
