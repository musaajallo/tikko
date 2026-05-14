"use client";

import { Bell, Plus, Search, Zap } from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";

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
  // `soon` items still navigate (to a placeholder page) but render a SOON badge
  // to signal that the underlying feature isn't fully built.
  soon?: boolean;
};

const primary: NavItem[] = [
  { href: "/devices" as Route, label: "Devices" },
  { href: "/employees" as Route, label: "Employees" },
  { href: "/reports" as Route, label: "Reports", soon: true },
  { href: "/settings" as Route, label: "Settings", soon: true },
];

const secondary: NavItem[] = [
  { href: "/documentation" as Route, label: "Docs", soon: true },
];

export function TopBar() {
  const router = useRouter();
  const pathname = usePathname();

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
        {primary.map((item) => (
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
          {secondary.map((item) => (
            <NavLink key={item.href} item={item} pathname={pathname} />
          ))}
        </nav>

        <Button size="sm" className="hidden sm:inline-flex">
          <Plus className="mr-1 h-4 w-4" />
          New device
        </Button>

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
              AD
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>Signed in</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={signOut}>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
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
