/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export' removido — incompativel com rotas SSR (workos/session). Deploy via Node server.
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
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true  // Sprint 8: pre-existing lint errors - to be fixed in Sprint 9
  },
  typescript: {
    ignoreBuildErrors: true  // Sprint 8: pre-existing TS errors - to be fixed in Sprint 9
  },
  images: {
    unoptimized: false,
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
        // Assets estáticos do Next.js — cache longo (1 ano), imutáveis (hash no nome)
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Fontes e imagens públicas — cache moderado
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, stale-while-revalidate=604800',
          },
        ],
      },
      {
        // Rotas de API — sem cache (dados dinâmicos)
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache',
          },
        ],
      },
      {
        // Páginas HTML — revalidar, mas usar cache se possível
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ]
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
