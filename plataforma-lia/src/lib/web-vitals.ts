/**
 * Web Vitals — monitora Core Web Vitals e envia para Sentry
 * Métricas: LCP, FID, CLS, FCP, TTFB
 */
export function reportWebVitals(metric: {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  id: string
}) {
  // Enviar para Sentry como medida de performance
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
    import('@sentry/nextjs').then(Sentry => {
      // @ts-ignore TODO: fix type — Property 'set' does not exist on type 'typeof import("/home/runner/workspace/pla
      Sentry.metrics?.set(metric.name, metric.value, {
        tags: { rating: metric.rating },
      })
    }).catch(() => {})
  }

  // Log em desenvolvimento
  if (process.env.NODE_ENV === 'development') {
    const color = metric.rating === 'good' ? '🟢' : metric.rating === 'needs-improvement' ? '🟡' : '🔴'
    console.info(`${color} [Web Vitals] ${metric.name}: ${Math.round(metric.value)}ms (${metric.rating})`)
  }
}
