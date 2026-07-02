/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["three"],
  // Prevent ESLint errors from failing the Vercel build
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Prevent TypeScript errors from failing the Vercel build
  typescript: {
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
