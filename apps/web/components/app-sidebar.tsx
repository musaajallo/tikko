"use client";

import { BarChart3, Cpu, LogOut, Settings as SettingsIcon } from "lucide-react";
import Link from "next/link";
import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { clearToken } from "@/lib/auth";

type NavItem = {
  href: Route;
  label: string;
  icon: typeof Cpu;
  disabled?: boolean;
};

const navItems: NavItem[] = [
  { href: "/devices" as Route, label: "Devices", icon: Cpu },
  { href: "/reports" as Route, label: "Reports", icon: BarChart3, disabled: true },
  { href: "/settings" as Route, label: "Settings", icon: SettingsIcon, disabled: true },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const signOut = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <Sidebar>
      <SidebarHeader>
        <Link
          href="/devices"
          className="flex items-center gap-2 px-2 py-2 text-lg font-semibold"
        >
          <span className="grid h-7 w-7 place-items-center rounded-md bg-primary text-primary-foreground">
            t
          </span>
          tikko
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = pathname.startsWith(item.href);
                if (item.disabled) {
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton disabled className="opacity-60">
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                        <span className="ml-auto text-xs">soon</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                }
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={active}>
                      <Link href={item.href}>
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={signOut}>
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
