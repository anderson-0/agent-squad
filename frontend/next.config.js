/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  },

  // Image optimization (updated for Next.js 16)
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // Turbopack configuration (required for Next.js 16)
  turbopack: {
    // Empty config to enable Turbopack with default settings
  },

  // Server actions are now stable in Next.js 16 (no experimental flag needed)
};

module.exports = nextConfig;
