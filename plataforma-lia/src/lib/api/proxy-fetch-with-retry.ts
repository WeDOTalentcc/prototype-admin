import { NextRequest } from 'next/server'
import { cookies } from 'next/headers'
import { getAuthHeaders } from './auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8001'

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
  } = {},
): Promise<Response> {
  const method = options.method || 'GET'
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
  const response = await fetch(url, fetchOptions)

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
      return fetch(url, retryOptions)
    }
  }

  return response
}
