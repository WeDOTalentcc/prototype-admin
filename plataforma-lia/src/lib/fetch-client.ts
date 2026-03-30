/**
 * Fetch client com correlation ID automático
 * Facilita rastreamento de requests entre frontend e backend
 */

function generateCorrelationId(): string {
  return `fe-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

interface FetchOptions extends RequestInit {
  correlationId?: string
}

export async function fetchWithCorrelation(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const correlationId = options.correlationId || generateCorrelationId()

  const headers = new Headers(options.headers)
  headers.set('x-correlation-id', correlationId)
  headers.set('x-client', 'plataforma-lia-web')

  return fetch(url, {
    ...options,
    headers,
  })
}

export { generateCorrelationId }
