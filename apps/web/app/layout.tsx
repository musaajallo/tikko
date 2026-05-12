import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "tikko",
  description: "ZKTeco terminal management.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      <body>{children as any}</body>
    </html>
  );
}
