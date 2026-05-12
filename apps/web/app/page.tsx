"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { buttonVariants } from "@/components/ui/button";
import { getToken } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (getToken()) router.replace("/devices");
  }, [router]);

  return (
    <main className="grid min-h-screen place-items-center bg-primary px-4">
      <div className="max-w-md text-center text-primary-foreground">
        <span className="mb-4 inline-grid h-12 w-12 place-items-center rounded-xl bg-primary-foreground text-2xl font-bold text-primary">
          t
        </span>
        <h1 className="text-4xl font-bold tracking-tight">tikko</h1>
        <p className="mt-2 opacity-80">
          Time Attendance Management System for teams that own their data.
        </p>
        <nav className="mt-6 flex items-center justify-center gap-3">
          <a href="/login" className={buttonVariants({ variant: "secondary" })}>
            Sign in
          </a>
          <a
            href="/devices"
            className={buttonVariants({
              variant: "outline",
              className: "bg-transparent text-primary-foreground",
            })}
          >
            Devices
          </a>
        </nav>
      </div>
    </main>
  );
}
