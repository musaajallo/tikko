import { resolve } from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: resolve(__dirname, "../.."),
  typedRoutes: true,
};

export default nextConfig;
