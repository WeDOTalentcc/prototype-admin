import { checkPaymentRequired } from '@/lib/api/handle-payment-required'

export const BACKEND_URL = '/api/backend-proxy'

export { checkPaymentRequired }

export function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
  }
}

export function getAuthHeadersForFormData(): HeadersInit {
  return {}
}

export interface FetchWithRetryOptions {
  attempts?: number
  timeoutMs?: number
  retryDelaysMs?: number[]
}

export async function fetchWithRetry(
  url: string,
  init: RequestInit = {},
  options: FetchWithRetryOptions = {}
): Promise<Response> {
  const {
    attempts = 3,
    timeoutMs = 20000,
    retryDelaysMs = [0, 1000, 3000],
  } = options

  let lastError: unknown
  for (let attempt = 0; attempt < attempts; attempt++) {
    const delay = retryDelaysMs[attempt] ?? retryDelaysMs[retryDelaysMs.length - 1] ?? 0
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
    try {
      const signal = init.signal ?? AbortSignal.timeout(timeoutMs)
      const response = await fetch(url, { ...init, signal })
      if (response.status >= 500 && attempt < attempts - 1) {
        lastError = new Error(`HTTP ${response.status}`)
        continue
      }
      return response
    } catch (error) {
      lastError = error
      if (error instanceof Error && error.name === 'AbortError' && init.signal) {
        throw error
      }
    }
  }
  throw lastError instanceof Error
    ? lastError
    : new Error('Fetch failed after retries')
}
