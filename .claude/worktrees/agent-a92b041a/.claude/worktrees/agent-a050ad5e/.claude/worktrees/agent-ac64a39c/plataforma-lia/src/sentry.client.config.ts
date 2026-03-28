/**
 * Sentry client-side configuration.
 * Loaded automatically by Next.js via instrumentation.ts or next.config.js sentry integration.
 *
 * To enable: add NEXT_PUBLIC_SENTRY_DSN to environment variables.
 * To install: npm install @sentry/nextjs
 */
import * as Sentry from "@sentry/nextjs"

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE ?? "0.1"
    ),
    environment: process.env.NODE_ENV,
    debug: false,
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
  })
}
