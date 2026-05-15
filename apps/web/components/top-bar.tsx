"use client";

import { Bell, Moon, Plus, Search, Sun, Zap } from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useCurrentUser } from "@/components/current-user-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { clearToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

type NavItem = {
  href: Route;
  label: string;
  // The capability needed to see this item. The api enforces the same gate
  // server-side; this just stops users from clicking into a guaranteed-403.
  // `null` means "visible to anyone signed in".
  requires: string | null;
  // `soon` items still navigate (to a placeholder page) but render a SOON badge
  // to signal that the underlying feature isn't fully built.
  soon?: boolean;
};

const primary: NavItem[] = [
  { href: "/devices" as Route, label: "Devices", requires: "view_devices" },
  { href: "/employees" as Route, label: "Employees", requires: "view_employees" },
  { href: "/leave-requests" as Route, label: "Leave", requires: "view_team_leave" },
  { href: "/reports" as Route, label: "Reports", requires: "view_reports" },
  { href: "/settings" as Route, label: "Settings", requires: "manage_permissions" },
];

const secondary: NavItem[] = [
  { href: "/documentation" as Route, label: "Docs", requires: null },
];

function avatarInitials(email?: string | null): string {
  if (!email) return "??";
  const local = email.split("@")[0] ?? "";
  return (local.slice(0, 2) || "??").toUpperCase();
}

export function TopBar() {
  const router = useRouter();
  const pathname = usePathname();
  const { me, hasCapability } = useCurrentUser();
  const role = me?.user.role ?? null;

  const visible = (item: NavItem) =>
    me !== null && (item.requires === null || hasCapability(item.requires));

  const signOut = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <Link href="/devices" className="flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-md bg-primary text-primary-foreground">
          <Zap className="h-4 w-4" />
        </span>
        <span className="text-sm font-semibold tracking-tight">tikko</span>
      </Link>

      <nav className="ml-3 hidden items-center gap-1 text-sm md:flex">
        {primary.filter(visible).map((item) => (
          <NavLink key={item.href} item={item} pathname={pathname} />
        ))}
      </nav>

      <div className="relative ml-3 hidden flex-1 max-w-md md:block">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search anything…"
          className="h-9 pl-8 pr-12"
          aria-label="Search"
        />
        <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
          ⌘K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <nav className="hidden items-center gap-1 text-sm md:flex">
          {secondary.filter(visible).map((item) => (
            <NavLink key={item.href} item={item} pathname={pathname} />
          ))}
        </nav>

        {hasCapability("manage_devices") && (
          <Button size="sm" className="hidden sm:inline-flex" asChild>
            <Link href="/devices">
              <Plus className="mr-1 h-4 w-4" />
              New device
            </Link>
          </Button>
        )}

        <ThemeToggle />

        <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="grid h-8 w-8 place-items-center rounded-full bg-muted text-xs font-semibold uppercase ring-2 ring-transparent transition hover:ring-ring/40"
              aria-label="Account menu"
            >
              {avatarInitials(me?.user.email)}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col gap-1">
                <span className="truncate text-sm font-medium">
                  {me?.user.email ?? "Signed in"}
                </span>
                {role && (
                  <Badge variant="secondary" className="w-fit text-[10px]">
                    {role}
                  </Badge>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile">Profile</Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={signOut}>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // `next-themes` only knows the real value after hydration, so we render an
  // attribute-stable placeholder. `next-themes` only resolves dark/light on
  // the client (localStorage + prefers-color-scheme), so SSR sees `undefined`
  // and would emit a different `aria-label` and `onClick` from what the
  // client renders. Both must wait for hydration, not just the icon.
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="Toggle theme">
        <span className="h-4 w-4" />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const active = pathname.startsWith(item.href);
  return (
    <Link
      href={item.href}
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 transition-colors",
        active
          ? "bg-muted font-medium text-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {item.label}
      {item.soon && (
        <span className="rounded-sm bg-muted px-1 text-[10px] font-medium uppercase tracking-wide">
          soon
        </span>
      )}
    </Link>
  );
}
