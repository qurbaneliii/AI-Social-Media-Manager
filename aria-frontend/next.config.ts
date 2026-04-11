// filename: next.config.ts
// purpose: Next.js runtime configuration.
// dependencies: next

import type { NextConfig } from "next";

const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] ?? "";
const githubPagesBasePath = repoName ? `/${repoName}` : "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  basePath: githubPagesBasePath,
  assetPrefix: githubPagesBasePath || undefined
};

export default nextConfig;
