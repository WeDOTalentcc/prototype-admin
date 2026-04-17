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

/**
 * Tipped HTTP error used by lia-api callers to react to specific status codes
 * (e.g. distinguish 429 rate-limit from 5xx outage from generic 4xx).
 */
export class HttpError extends Error {
  readonly status: number
  readonly retryAfterMs?: number
  readonly body?: string

  constructor(
    status: number,
    message: string,
    opts: { retryAfterMs?: number; body?: string } = {},
  ) {
    super(message)
    this.name = 'HttpError'
    this.status = status
    this.retryAfterMs = opts.retryAfterMs
    this.body = opts.body
  }
}

/** Parses an HTTP `Retry-After` header (seconds OR HTTP-date) into ms. */
export function parseRetryAfterMs(value: string | null | undefined): number | null {
  if (!value) return null
  const trimmed = value.trim()
  if (!trimmed) return null
  const seconds = Number(trimmed)
  if (Number.isFinite(seconds)) return Math.max(0, Math.floor(seconds * 1000))
  const dateMs = Date.parse(trimmed)
  if (!Number.isNaN(dateMs)) return Math.max(0, dateMs - Date.now())
  return null
}

export interface FetchWithRetryOptions {
  attempts?: number
  timeoutMs?: number
  retryDelaysMs?: number[]
  /** Cap on how long we'll wait for a 429 Retry-After before giving up. */
  maxRetryAfterMs?: number
}

async function sleepCancellable(ms: number, signal?: AbortSignal | null): Promise<void> {
  if (ms <= 0) return
  if (signal?.aborted) {
    throw new DOMException('Aborted', 'AbortError')
  }
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

/**
 * Canonical fetch helper used by the entire `lia-api` surface.
 *
 * Policy (single source of truth — task #345):
 *  - Retries only on 5xx, network errors, and 429.
 *  - On 429, honors `Retry-After` (seconds or HTTP-date), capped by
 *    `maxRetryAfterMs`. Falls back to the configured back-off delay when the
 *    header is missing.
 *  - On 4xx other than 429, returns immediately — caller decides what to do.
 *  - If the caller passed `init.signal`, an `AbortError` from that signal
 *    propagates immediately (no retry) and the caller's signal is forwarded
 *    verbatim so server-side aborts work as expected.
 *  - When no caller signal is provided, each attempt gets its own
 *    `AbortSignal.timeout(timeoutMs)` so a hung request cannot wedge the UI.
 */
export async function fetchWithRetry(
  url: string,
  init: RequestInit = {},
  options: FetchWithRetryOptions = {},
): Promise<Response> {
  const {
    attempts = 3,
    timeoutMs = 20000,
    retryDelaysMs = [0, 1000, 3000],
    maxRetryAfterMs = 30000,
  } = options

  const callerSignal = init.signal ?? null
  let lastError: unknown
  // When a 429 told us to wait `Retry-After`, we already slept exactly that
  // long — skip the next attempt's regular back-off delay so we don't add
  // extra latency on top of the server's own hint.
  let skipNextBaseDelay = false

  for (let attempt = 0; attempt < attempts; attempt++) {
    if (callerSignal?.aborted) {
      throw new DOMException('Aborted', 'AbortError')
    }

    const baseDelay = retryDelaysMs[attempt] ?? retryDelaysMs[retryDelaysMs.length - 1] ?? 0
    if (baseDelay > 0 && !skipNextBaseDelay) {
      await sleepCancellable(baseDelay, callerSignal)
    }
    skipNextBaseDelay = false

    try {
      const signal = callerSignal ?? AbortSignal.timeout(timeoutMs)
      const response = await fetch(url, { ...init, signal })

      if (response.status === 429) {
        const retryAfterMs = parseRetryAfterMs(response.headers.get('Retry-After'))
        if (attempt < attempts - 1) {
          const wait = Math.min(
            retryAfterMs ?? Math.max(baseDelay, 1000),
            maxRetryAfterMs,
          )
          lastError = new HttpError(429, 'Too Many Requests', {
            retryAfterMs: retryAfterMs ?? undefined,
          })
          await sleepCancellable(wait, callerSignal)
          // We honored Retry-After — don't pile the next base delay on top.
          if (retryAfterMs !== null) skipNextBaseDelay = true
          continue
        }
        // Final attempt — return so caller can read body/status.
        return response
      }

      if (response.status >= 500 && attempt < attempts - 1) {
        lastError = new HttpError(response.status, `HTTP ${response.status}`)
        continue
      }

      return response
    } catch (error) {
      lastError = error
      // Caller-initiated abort: bubble up immediately.
      if (
        error instanceof DOMException &&
        error.name === 'AbortError' &&
        callerSignal
      ) {
        throw error
      }
      // TimeoutError (own signal) or TypeError (network) — fall through to retry.
    }
  }

  throw lastError instanceof Error
    ? lastError
    : new Error('Fetch failed after retries')
}
