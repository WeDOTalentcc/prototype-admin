const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001';

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  output: 'standalone',
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
  experimental: {
    // Otimiza tree-shaking de pacotes com muitos exports (lucide-react tem ~1500 icones)
    optimizePackageImports: [
      'lucide-react',
      '@radix-ui/react-accordion',
      '@radix-ui/react-alert-dialog',
      '@radix-ui/react-avatar',
      '@radix-ui/react-checkbox',
      '@radix-ui/react-collapsible',
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-popover',
      '@radix-ui/react-select',
      '@radix-ui/react-tabs',
      '@radix-ui/react-toast',
      '@radix-ui/react-tooltip',
      'recharts',
    ],
  },
  images: {
    unoptimized: false,
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 3600,
    domains: [
      "source.unsplash.com",
      "images.unsplash.com",
      "ext.same-assets.com",
      "ugc.same-assets.com",
      "ui-avatars.com",
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
      {
        protocol: "https",
        hostname: "**.linkedin.com",
      },
      {
        protocol: "https",
        hostname: "**.gravatar.com",
      },
      {
        protocol: "https",
        hostname: "**.googleusercontent.com",
      },
      {
        protocol: "https",
        hostname: "**.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "media.licdn.com",
      },
      {
        protocol: "https",
        hostname: "ui-avatars.com",
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
          ...(process.env.NODE_ENV === 'production' ? [
            {
              key: 'X-Frame-Options',
              value: 'DENY',
            },
          ] : []),
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https://source.unsplash.com https://images.unsplash.com https://ext.same-assets.com https://ugc.same-assets.com https://upload.wikimedia.org https://cdn.prod.website-files.com https://ui-avatars.com https://media.licdn.com https://*.gravatar.com https://*.googleusercontent.com https://*.amazonaws.com",
              "media-src 'self' blob: data:",
              "worker-src 'self' blob:",
              "connect-src 'self' https://*.sentry.io https://*.ingest.sentry.io wss: ws:",
              process.env.NODE_ENV === 'production' ? "frame-ancestors 'none'" : "frame-ancestors *",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; '),
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(self), geolocation=()',
          },
          ...(process.env.NODE_ENV === 'production' ? [
            {
              key: 'Strict-Transport-Security',
              value: 'max-age=63072000; includeSubDomains; preload',
            },
          ] : []),
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ].filter(Boolean),
      },
    ]
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
      {
        source: '/api/backend-proxy/wizard/:path*',
        destination: `${BACKEND_URL}/api/v1/wizard/:path*`,
      },
      {
        source: '/api/lia/chat/stream',
        destination: `${BACKEND_URL}/api/v1/chat/stream`,
      },
      {
        source: '/ws/:path*',
        destination: `${BACKEND_URL}/ws/:path*`,
      },
    ];
  },
};

module.exports = withBundleAnalyzer(nextConfig);
