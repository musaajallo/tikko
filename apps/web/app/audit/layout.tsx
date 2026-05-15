import * as React from "react";

import { ProtectedShell } from "@/components/protected-shell";

export default function AuditLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <ProtectedShell>{children}</ProtectedShell>;
}
