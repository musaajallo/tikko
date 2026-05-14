"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

type NavItem = {
  href: Route;
  label: string;
  disabled?: boolean;
};

const left: NavItem[] = [
  { href: "/devices" as Route, label: "Devices" },
  { href: "/employees" as Route, label: "Employees" },
  { href: "/reports" as Route, label: "Reports", disabled: true },
  { href: "/settings" as Route, label: "Settings", disabled: true },
];

const right: NavItem[] = [
  { href: "/docs" as Route, label: "Documentation", disabled: true },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <nav className="flex h-11 items-center border-b bg-background/80 px-4 text-sm">
      <div className="flex items-center gap-1">
        {left.map((item) => (
          <NavLink key={item.href} item={item} active={pathname.startsWith(item.href)} />
        ))}
      </div>
      <div className="ml-auto flex items-center gap-1">
        {right.map((item) => (
          <NavLink key={item.href} item={item} active={pathname.startsWith(item.href)} />
        ))}
      </div>
    </nav>
  );
}

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  if (item.disabled) {
    return (
      <span className="inline-flex cursor-default items-center gap-1 rounded-md px-3 py-1.5 text-muted-foreground/60">
        {item.label}
        <span className="rounded-sm bg-muted px-1 text-[10px] font-medium uppercase tracking-wide">
          soon
        </span>
      </span>
    );
  }
  return (
    <Link
      href={item.href}
      className={cn(
        "rounded-md px-3 py-1.5 transition-colors",
        active
          ? "bg-muted font-medium text-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {item.label}
    </Link>
  );
}
