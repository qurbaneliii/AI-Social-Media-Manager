/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/AI-Social-Media-Manager",
  assetPrefix: "/AI-Social-Media-Manager/",
  images: {
    unoptimized: true
  },
  trailingSlash: true
};

module.exports = nextConfig;
