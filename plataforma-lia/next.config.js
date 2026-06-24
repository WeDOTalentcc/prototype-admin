const createNextIntlPlugin = require('next-intl/plugin')
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Audit 2026-05-24 P1: tree-shake automatico de packages com barrel imports
  // (565 imports `from "lucide-react"` no codebase). Next 16 transforma em
  // `lucide-react/dist/esm/icons/X` em build/dev — zero edits em call sites.
  experimental: {
    optimizePackageImports: ['lucide-react', 'date-fns', '@radix-ui/react-icons'],
  },
  typescript: {
    ignoreBuildErrors: false,  // R-020: TS errors fixed, gate now active
  },
  eslint: {
    // Lint roda no CI (frontend-ci.yml). Build de producao nao deve ser
    // bloqueado por regras de estilo nem por arquivos de teste.
    ignoreDuringBuilds: true,
  },
  productionBrowserSourceMaps: false,
  logging: process.env.NODE_ENV === 'production'
    ? { fetches: { fullUrl: true, hmrRefreshes: true }, incomingRequests: true }
    : { fetches: { fullUrl: false, hmrRefreshes: false }, incomingRequests: false },
  webpack: (config, { dev }) => {
    if (!dev) {
      config.parallelism = 4;
    }
    return config;
  },
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 4,
  },
  output: 'standalone',
  outputFileTracingRoot: __dirname,
  allowedDevOrigins: [
    'localhost:5000',
    '127.0.0.1:5000',
    'localhost:3000',
    '127.0.0.1:3000',
    'localhost',
    '127.0.0.1',
    '*.worf.replit.dev',
    '*.picard.replit.dev',
    '*.riker.replit.dev',
    '*.janeway.replit.dev',
    '*.kirk.replit.dev',
    '*.spock.replit.dev',
    '*.replit.dev',
    '*.repl.co'
  ],
  reactStrictMode: true,
  images: {
    unoptimized: false,
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 3600,
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
      {
        protocol: "https",
        hostname: "api.dicebear.com",
        pathname: "/**",
      },
    ],
  },
  async headers() {
    const isProd = process.env.NODE_ENV === 'production';

    if (!isProd) {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'Cache-Control',
              value: 'no-store, no-cache, must-revalidate, proxy-revalidate',
            },
          ],
        },
      ];
    }

    const staticHeaders = [
      {
        source: '/_next/static/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: '/fonts/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400, stale-while-revalidate=604800' },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          { key: 'Cache-Control', value: 'no-store, no-cache' },
        ],
      },
    ];

    return [
      ...staticHeaders,
      {
        source: '/:path*',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https://source.unsplash.com https://images.unsplash.com https://ext.same-assets.com https://ugc.same-assets.com https://upload.wikimedia.org https://cdn.prod.website-files.com https://ui-avatars.com https://media.licdn.com https://*.gravatar.com https://*.googleusercontent.com https://*.amazonaws.com https://*.pinimg.com",
              "media-src 'self' blob: data:",
              "worker-src 'self' blob:",
              "connect-src 'self' https://*.sentry.io https://*.ingest.sentry.io wss: ws:",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; '),
          },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(self), geolocation=()' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
        ],
      },
    ];
  },
  async redirects() {
    return [
      // Rails serializer retorna `url: "/user/jobs/:id"` (legado do Nuxt ats_front).
      // Redireciona pra rota nova do Next.js `/jobs/:id`.
      {
        source: '/:locale(pt|en|es)/user/jobs/:id(\\d+)',
        destination: '/:locale/jobs/:id',
        permanent: false,
      },
      {
        source: '/:locale(pt|en|es)/user/jobs/:id(\\d+)/applies/:apply_id(\\d+)',
        destination: '/:locale/jobs/:id/applies/:apply_id',
        permanent: false,
      },
    ]
  },
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/__mockup/:path*',
          destination: 'http://localhost:23636/__mockup/:path*',
        },
      ],
      afterFiles: [
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
      ],
      fallback: [
        {
          source: '/api/backend-proxy/chat',
          destination: `${BACKEND_URL}/api/v1/chat`,
        },
        {
          source: '/api/backend-proxy/chat/:path*',
          destination: `${BACKEND_URL}/api/v1/chat/:path*`,
        },
      ],
    };
  },
};

module.exports = withNextIntl(withBundleAnalyzer(nextConfig));
