// filename: next.config.ts
// purpose: Next.js runtime configuration.
// dependencies: next

import type { NextConfig } from "next";

const repoName = "AI-Social-Media-Manager";

const nextConfig: NextConfig = {
  output: "export",
  reactStrictMode: true,
  basePath: `/${repoName}`,
  assetPrefix: `/${repoName}/`,
  images: {
    unoptimized: true
  },
  trailingSlash: true
};

export default nextConfig;
