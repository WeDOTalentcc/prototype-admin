/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  distDir: 'out',
  trailingSlash: true,
  outputFileTracingRoot: __dirname,
  allowedDevOrigins: [
    'localhost:5000',
    '127.0.0.1:5000',
    'localhost',
    '127.0.0.1',
    '*.worf.replit.dev',
    '*.picard.replit.dev',
    '*.riker.replit.dev',
    '*.replit.dev',
    '*.repl.co'
  ],
  reactStrictMode: false,
  eslint: {
    ignoreDuringBuilds: false
  },
  typescript: {
    ignoreBuildErrors: false
  },
  images: {
    unoptimized: true,
    domains: [
      "source.unsplash.com",
      "images.unsplash.com",
      "ext.same-assets.com",
      "ugc.same-assets.com",
    ],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "source.unsplash.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "ext.same-assets.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "ugc.same-assets.com",
        pathname: "/**",
      },
    ],
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
      {
        source: '/api/backend-proxy/wizard/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/wizard/:path*',
      },
      {
        // SSE streaming — bypass Next.js API route (incompatível com static export)
        source: '/api/lia/chat/stream',
        destination: 'http://127.0.0.1:8000/api/v1/chat/stream',
      },
    ];
  },
};

module.exports = nextConfig;
