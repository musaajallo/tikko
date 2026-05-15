"use client";

import { Loader2 } from "lucide-react";
import * as React from "react";

import { useCurrentUser } from "@/components/current-user-context";
import { TopBar } from "@/components/top-bar";

export function ProtectedShell({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { me, loading } = useCurrentUser();

  // Until we know who the user is, don't render the page contents. This is
  // also true for unauthenticated visitors: the provider triggers a redirect
  // to /login and we'd rather show a one-frame spinner than briefly flash
  // the admin shell before the navigation fires.
  if (loading || me === null) {
    return (
      <div className="grid min-h-screen place-items-center bg-muted/30">
        <Loader2
          className="h-6 w-6 animate-spin text-muted-foreground"
          aria-label="Loading"
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/30">
      <TopBar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
