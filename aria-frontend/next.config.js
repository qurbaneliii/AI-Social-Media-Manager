const repoName = "AI-Social-Media-Manager";
const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true
  },
  ...(isStatic
    ? {
        output: "export",
        basePath: `/${repoName}`,
        assetPrefix: `/${repoName}/`,
        trailingSlash: true
      }
    : {})
};

module.exports = nextConfig;
