import { resolve } from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: resolve(__dirname, "../.."),
  typedRoutes: true,
  // Emit a self-contained server bundle for Docker images. Combined with the
  // tracing root above, `next build` copies only what the server needs into
  // `.next/standalone` — small final image, no node_modules at runtime.
  output: "standalone",
};

export default nextConfig;
