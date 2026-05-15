import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CurrentUserProvider, useCurrentUser } from "../current-user-context";

// next/navigation's usePathname is the only piece of next we touch here.
let mockPathname = "/devices";
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

const ME_BODY = {
  user: {
    id: "u1",
    email: "ada@example.com",
    role: "admin",
    employee_id: null,
    created_at: "2026-05-14T08:00:00Z",
  },
  employee: null,
};

function Probe() {
  const { me, loading } = useCurrentUser();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="email">{me?.user.email ?? "—"}</span>
    </div>
  );
}

describe("CurrentUserProvider redirect guard", () => {
  let hrefSetter: ReturnType<typeof vi.fn>;
  let originalHref: string;

  beforeEach(() => {
    mockPathname = "/devices";
    window.localStorage.clear();
    vi.restoreAllMocks();

    originalHref = window.location.href;
    hrefSetter = vi.fn();
    // jsdom's location is normally read-only at the property level. Replace
    // it with a proxy so we can intercept assignments without a real navigation.
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        get href() {
          return originalHref;
        },
        set href(v: string) {
          hrefSetter(v);
        },
        get pathname() {
          return new URL(originalHref).pathname;
        },
      },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: new URL(originalHref),
    });
  });

  it("redirects to /login when there's no token on a protected page", async () => {
    mockPathname = "/devices";
    render(
      <CurrentUserProvider>
        <Probe />
      </CurrentUserProvider>,
    );

    await waitFor(() => {
      expect(hrefSetter).toHaveBeenCalledWith("/login");
    });
  });

  it("does not redirect when there's no token on the public landing page (/)", async () => {
    mockPathname = "/";
    render(
      <CurrentUserProvider>
        <Probe />
      </CurrentUserProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(hrefSetter).not.toHaveBeenCalled();
  });

  it("does not redirect when there's no token on /login itself", async () => {
    mockPathname = "/login";
    render(
      <CurrentUserProvider>
        <Probe />
      </CurrentUserProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(hrefSetter).not.toHaveBeenCalled();
  });

  it("populates `me` and skips the redirect when a token + /auth/me succeed", async () => {
    window.localStorage.setItem("tikko.access_token", "a.b.c");
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ME_BODY,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <CurrentUserProvider>
        <Probe />
      </CurrentUserProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("email")).toHaveTextContent("ada@example.com");
    });
    expect(hrefSetter).not.toHaveBeenCalled();
  });
});
