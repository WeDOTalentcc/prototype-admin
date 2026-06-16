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
  /**
   * Task #728: when true, the failure is a transient client-side network
   * error (cold-start, DNS hiccup, dropped connection) — NOT a real 4xx/5xx
   * from the backend. Consumers may render a soft "trying to reconnect"
   * state without alarming the user, and the Next.js dev overlay can be
   * filtered against this discriminator instead of matching on the raw
   * `TypeError: Failed to fetch` message.
   */
  readonly transientNetworkError?: boolean

  constructor(
    status: number,
    message: string,
    opts: { retryAfterMs?: number; body?: string; transientNetworkError?: boolean } = {},
  ) {
    super(message)
    this.name = 'HttpError'
    this.status = status
    this.retryAfterMs = opts.retryAfterMs
    this.body = opts.body
    this.transientNetworkError = opts.transientNetworkError
  }
}

/**
 * Task #728: detects browser network-layer failures that are *not* HTTP
 * responses — typically thrown by `fetch()` as `TypeError("Failed to fetch")`
 * during cold-start, DNS resolution failures, or aborted connections.
 *
 * NOT considered transient: real `HttpError` (we got a response), explicit
 * AbortError from the caller, server 5xx (those are real failures).
 */
export function isTransientNetworkError(err: unknown): boolean {
  if (err instanceof HttpError) return err.transientNetworkError === true
  if (err instanceof TypeError) {
    // The exact message varies by browser (Chrome: "Failed to fetch",
    // Firefox: "NetworkError when attempting to fetch resource", Safari:
    // "Load failed"). Match conservatively.
    const msg = (err.message || '').toLowerCase()
    return (
      msg.includes('failed to fetch') ||
      msg.includes('networkerror') ||
      msg.includes('load failed')
    )
  }
  return false
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
  /** Called before each retry with 1-based attempt number, total attempts, and reason. */
  onRetry?: (attempt: number, maxAttempts: number, reason: string) => void
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
    onRetry,
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
          onRetry?.(attempt + 1, attempts, 'rate-limited')
          continue
        }
        // Final attempt — return so caller can read body/status.
        return response
      }

      if (response.status >= 500 && attempt < attempts - 1) {
        lastError = new HttpError(response.status, `HTTP ${response.status}`)
        onRetry?.(attempt + 1, attempts, `server-${response.status}`)
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
      if (attempt < attempts - 1) {
        onRetry?.(attempt + 1, attempts, 'network')
      }
    }
  }

  // Task #728: convert raw network TypeError into a typed HttpError so
  // (a) consumers can discriminate transient failures with a single check
  // and (b) the Next.js dev overlay no longer matches the bare
  // `TypeError: Failed to fetch` string and pops up during cold-start.
  // Real HTTP errors (5xx etc.) and AbortError are preserved verbatim.
  if (isTransientNetworkError(lastError)) {
    // Task #801 (C2): NUNCA propagar a string crua "Failed to fetch" — o
    // dev-overlay do Next.js (e logs do console) reanexam à mensagem,
    // ressuscitando o sintoma que a Task #728 quis suprimir. Usamos uma
    // mensagem fixa, identificável por testes, e preservamos o original em
    // `cause` para diagnóstico.
    const err = new HttpError(0, 'Network unavailable (transient)', {
      transientNetworkError: true,
    })
    if (lastError instanceof Error) {
      ;(err as Error & { cause?: unknown }).cause = lastError
    }
    throw err
  }

  throw lastError instanceof Error
    ? lastError
    : new Error('Fetch failed after retries')
}
