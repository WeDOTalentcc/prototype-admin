import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE ?? '0.1'
    ),
    environment: process.env.NODE_ENV,
    enabled: !!SENTRY_DSN,  // Sprint Sentry (2026-05-24): ativa se DSN presente (Replit dev = prod)
  })
}
