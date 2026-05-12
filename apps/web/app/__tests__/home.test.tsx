import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../page";

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
