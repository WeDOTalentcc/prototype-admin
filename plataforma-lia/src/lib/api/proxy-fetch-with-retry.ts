import { NextRequest } from 'next/server'
import { cookies } from 'next/headers'
import { getAuthHeaders } from './auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// Audit 2026-06-03 (#6 FE): bound de duracao do proxy. Sem isto, o fetch ao
// backend ficava pendurado indefinidamente e o gateway da plataforma (na
// frente do Next) estourava com 502 OPACO. Default generoso (100s) para
// acomodar o orquestrador do chat (504 do backend em ~90s chega antes);
// configuravel via env. Em timeout, devolve 504 sintetico (Response !ok) que
// os callers ja tratam, em vez de pendurar.
const DEFAULT_PROXY_TIMEOUT_MS = Number(process.env.PROXY_FETCH_TIMEOUT_MS || 100000)

async function _fetchBounded(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  try {
    return await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) })
  } catch (err) {
    if (err instanceof Error && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
      return new Response(
        JSON.stringify({ error: 'upstream_timeout', detail: 'Backend demorou demais para responder. Tente novamente.' }),
        { status: 504, headers: { 'Content-Type': 'application/json' } },
      )
    }
    throw err
  }
}

async function tryRefreshToken(): Promise<string | null> {
  try {
    const cookieStore = await cookies()
    const refreshTokenCookie = cookieStore.get('lia_refresh_token')
    if (!refreshTokenCookie) return null

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshTokenCookie.value }),
    })

    if (!response.ok) return null

    const data = await response.json()
    const newToken = data.access_token

    if (newToken) {
      cookieStore.set('lia_access_token', newToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax' as const,
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
      })
      if (data.refresh_token) {
        cookieStore.set('lia_refresh_token', data.refresh_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax' as const,
          path: '/',
          maxAge: 60 * 60 * 24 * 7,
        })
      }
    }

    return newToken
  } catch {
    return null
  }
}

export async function proxyFetchWithRetry(
  request: NextRequest,
  backendPath: string,
  options: {
    method?: string
    body?: string
    extraHeaders?: Record<string, string>
    /** Override do teto de duracao (ms). Default DEFAULT_PROXY_TIMEOUT_MS. */
    timeoutMs?: number
  } = {},
): Promise<Response> {
  const method = options.method || 'GET'
  const timeoutMs = options.timeoutMs ?? DEFAULT_PROXY_TIMEOUT_MS
  const headers = getAuthHeaders(request)
  if (options.extraHeaders) {
    Object.assign(headers, options.extraHeaders)
  }

  const fetchOptions: RequestInit = {
    method,
    headers,
  }
  if (options.body) fetchOptions.body = options.body

  const url = `${BACKEND_URL}${backendPath}`
  const response = await _fetchBounded(url, fetchOptions, timeoutMs)

  if (response.status === 401) {
    const newToken = await tryRefreshToken()
    if (newToken) {
      const retryHeaders = {
        ...headers,
        'Authorization': `Bearer ${newToken}`,
      } as HeadersInit
      const retryOptions: RequestInit = {
        method,
        headers: retryHeaders,
      }
      if (options.body) retryOptions.body = options.body
      return _fetchBounded(url, retryOptions, timeoutMs)
    }
  }

  return response
}
