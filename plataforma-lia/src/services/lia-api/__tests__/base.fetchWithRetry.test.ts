/**
 * Tests — `fetchWithRetry` canonical helper (Task #345)
 *
 * Covers the unified resilience policy used by every lia-api caller:
 *   - 429 honors `Retry-After` (seconds and HTTP-date) before retrying.
 *   - 5xx is retried up to `attempts`.
 *   - 4xx (other than 429) is returned immediately — no retry storm.
 *   - Network errors retry; final failure re-throws.
 *   - A caller-supplied `signal` aborts immediately (no further retries).
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  fetchWithRetry,
  HttpError,
  isTransientNetworkError,
  parseRetryAfterMs,
} from '../base'

describe('parseRetryAfterMs', () => {
  it('parses seconds as a number', () => {
    expect(parseRetryAfterMs('3')).toBe(3000)
    expect(parseRetryAfterMs('0')).toBe(0)
  })

  it('parses HTTP-date as ms-from-now', () => {
    const future = new Date(Date.now() + 5000).toUTCString()
    const ms = parseRetryAfterMs(future) ?? 0
    expect(ms).toBeGreaterThan(3500)
    expect(ms).toBeLessThanOrEqual(5500)
  })

  it('returns null for missing/invalid input', () => {
    expect(parseRetryAfterMs(null)).toBeNull()
    expect(parseRetryAfterMs('')).toBeNull()
    expect(parseRetryAfterMs('not a date')).toBeNull()
  })
})

describe('fetchWithRetry', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  function jsonResponse(status: number, headers: Record<string, string> = {}) {
    return new Response(JSON.stringify({ ok: status < 400 }), {
      status,
      headers: { 'content-type': 'application/json', ...headers },
    })
  }

  it('returns immediately on 2xx (single fetch call)', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200))
    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 0, 0] })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('retries on 5xx and resolves once a 2xx arrives', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(500))
      .mockResolvedValueOnce(jsonResponse(200))
    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 10, 10] })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does NOT retry on 400 — returns the response on first try', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(400))
    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 0, 0] })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(400)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('on 429, honors Retry-After (seconds) before retrying', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(429, { 'Retry-After': '2' }))
      .mockResolvedValueOnce(jsonResponse(200))

    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 0, 0] })

    // Drain microtasks for the first fetch resolution
    await vi.advanceTimersByTimeAsync(0)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    // Just before the 2s Retry-After fires — still no second call
    await vi.advanceTimersByTimeAsync(1900)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    // After the full Retry-After window, the second call goes out
    await vi.advanceTimersByTimeAsync(200)
    const res = await promise
    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('after honoring Retry-After, does NOT add the next base back-off on top', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(429, { 'Retry-After': '2' }))
      .mockResolvedValueOnce(jsonResponse(200))

    // Configure a non-trivial base delay for attempt #2 to make the
    // double-wait bug observable if it ever regresses.
    const promise = fetchWithRetry(
      '/x',
      {},
      { retryDelaysMs: [0, 5000, 5000] },
    )

    // First fetch returns 429 immediately.
    await vi.advanceTimersByTimeAsync(0)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    // After the 2s Retry-After (and NOTHING extra), the second call must fire.
    await vi.advanceTimersByTimeAsync(2000)
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const res = await promise
    expect(res.status).toBe(200)
  })

  it('on 429 with no Retry-After, falls back to retry-delay back-off', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(429))
      .mockResolvedValueOnce(jsonResponse(200))

    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 0, 0] })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('returns the 429 response on the FINAL attempt (no infinite loop)', async () => {
    fetchMock
      .mockResolvedValue(jsonResponse(429, { 'Retry-After': '1' }))

    const promise = fetchWithRetry(
      '/x',
      {},
      { attempts: 2, retryDelaysMs: [0, 0] },
    )
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(429)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('retries on network failure (TypeError) and eventually resolves', async () => {
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(jsonResponse(200))

    const promise = fetchWithRetry('/x', {}, { retryDelaysMs: [0, 0, 0] })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('throws after exhausting attempts on persistent network failure', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const promise = fetchWithRetry(
      '/x',
      {},
      { attempts: 2, retryDelaysMs: [0, 0] },
    )
    promise.catch(() => {}) // avoid unhandled-rejection from fake timers
    await vi.runAllTimersAsync()
    // Task #801 (C2): mensagem é fixa, original preservado em `cause`.
    await expect(promise).rejects.toThrow(/network unavailable \(transient\)/i)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('aborts immediately when caller-provided signal fires (no further retries)', async () => {
    const controller = new AbortController()
    fetchMock.mockImplementation((_url, init) => {
      return new Promise((_resolve, reject) => {
        ;(init as RequestInit).signal?.addEventListener('abort', () => {
          const e = new DOMException('Aborted', 'AbortError')
          reject(e)
        })
      })
    })

    const promise = fetchWithRetry(
      '/x',
      { signal: controller.signal },
      { attempts: 3, retryDelaysMs: [0, 0, 0] },
    )
    promise.catch(() => {})

    // Let the first fetch start, then abort
    await vi.advanceTimersByTimeAsync(0)
    controller.abort()
    await vi.runAllTimersAsync()

    await expect(promise).rejects.toMatchObject({ name: 'AbortError' })
    // Caller signal aborted the in-flight request — no second retry attempt.
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})

describe('HttpError', () => {
  it('carries status and optional retryAfterMs', () => {
    const err = new HttpError(429, 'Too Many Requests', { retryAfterMs: 5000 })
    expect(err.status).toBe(429)
    expect(err.retryAfterMs).toBe(5000)
    expect(err.name).toBe('HttpError')
    expect(err).toBeInstanceOf(Error)
  })

  it('carries transientNetworkError flag (Task #728)', () => {
    const err = new HttpError(0, 'Failed to fetch', { transientNetworkError: true })
    expect(err.status).toBe(0)
    expect(err.transientNetworkError).toBe(true)
  })
})

describe('isTransientNetworkError (Task #728)', () => {
  it('detects HttpError with transientNetworkError flag', () => {
    const err = new HttpError(0, 'x', { transientNetworkError: true })
    expect(isTransientNetworkError(err)).toBe(true)
  })

  it('rejects HttpError without the flag (real 4xx/5xx)', () => {
    expect(isTransientNetworkError(new HttpError(503, 'down'))).toBe(false)
    expect(isTransientNetworkError(new HttpError(404, 'nope'))).toBe(false)
  })

  it('detects browser network TypeError variants', () => {
    expect(isTransientNetworkError(new TypeError('Failed to fetch'))).toBe(true)
    expect(
      isTransientNetworkError(
        new TypeError('NetworkError when attempting to fetch resource.'),
      ),
    ).toBe(true)
    expect(isTransientNetworkError(new TypeError('Load failed'))).toBe(true)
  })

  it('rejects unrelated errors', () => {
    expect(isTransientNetworkError(new TypeError('foo is undefined'))).toBe(false)
    expect(isTransientNetworkError(new Error('boom'))).toBe(false)
    expect(isTransientNetworkError(null)).toBe(false)
    expect(isTransientNetworkError('string')).toBe(false)
  })
})

describe('fetchWithRetry — transient network failures (Task #728)', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('wraps final TypeError("Failed to fetch") into HttpError(0, transientNetworkError)', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const promise = fetchWithRetry('https://example.com', {}, { attempts: 2 })
    promise.catch(() => {})
    await vi.runAllTimersAsync()

    await expect(promise).rejects.toBeInstanceOf(HttpError)
    await expect(promise).rejects.toMatchObject({
      status: 0,
      transientNetworkError: true,
    })
    // The raw TypeError must NOT escape — it triggered the dev overlay.
    await expect(promise).rejects.not.toBeInstanceOf(TypeError)
  })

  it('Task #801 (C2): wrapped HttpError uses fixed message, not raw "Failed to fetch"', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const promise = fetchWithRetry('https://example.com', {}, { attempts: 1 })
    promise.catch(() => {})
    await vi.runAllTimersAsync()

    let caught: unknown
    try { await promise } catch (e) { caught = e }
    expect(caught).toBeInstanceOf(HttpError)
    expect((caught as Error).message).toBe('Network unavailable (transient)')
    // Original is preserved in `cause` for diagnóstico, but never in message.
    expect((caught as Error).message).not.toMatch(/failed to fetch/i)
    expect((caught as Error & { cause?: Error }).cause).toBeInstanceOf(TypeError)
  })

  it('still retries on transient network errors before wrapping the final one', async () => {
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response('ok', { status: 200 }))

    const promise = fetchWithRetry('https://example.com', {}, { attempts: 3 })
    await vi.runAllTimersAsync()
    const res = await promise
    expect(res.ok).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('preserves non-transient errors verbatim', async () => {
    const realError = new Error('something else broke')
    fetchMock.mockRejectedValue(realError)

    const promise = fetchWithRetry('https://example.com', {}, { attempts: 1 })
    promise.catch(() => {})
    await vi.runAllTimersAsync()

    await expect(promise).rejects.toBe(realError)
  })

  it('does NOT reclassify caller AbortError as transient', async () => {
    // Lock semantics long-term: an AbortError from the caller's signal must
    // remain an AbortError, not be wrapped into a transient HttpError.
    const controller = new AbortController()
    fetchMock.mockImplementation((_url: string, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          const err = new DOMException('Aborted', 'AbortError')
          reject(err)
        })
      })
    })

    const promise = fetchWithRetry(
      'https://example.com',
      { signal: controller.signal },
      { attempts: 3 },
    )
    promise.catch(() => {})

    await vi.advanceTimersByTimeAsync(0)
    controller.abort()
    await vi.runAllTimersAsync()

    await expect(promise).rejects.toMatchObject({ name: 'AbortError' })
    await expect(promise).rejects.not.toBeInstanceOf(HttpError)
  })
})
