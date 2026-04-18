/** @type {import('next').NextConfig} */
const isStaticExport = process.env.NEXT_PUBLIC_IS_STATIC === "true";

const nextConfig = {
  images: {
    unoptimized: true
  },
  async redirects() {
    if (isStaticExport) {
      return [];
    }

    return [
      {
        source: "/AI-Social-Media-Manager",
        destination: "/",
        permanent: false
      },
      {
        source: "/AI-Social-Media-Manager/:path*",
        destination: "/:path*",
        permanent: false
      }
    ];
  }
};

if (isStaticExport) {
  nextConfig.output = "export";
  nextConfig.basePath = "/AI-Social-Media-Manager";
  nextConfig.assetPrefix = "/AI-Social-Media-Manager/";
  nextConfig.trailingSlash = true;
}

module.exports = nextConfig;
