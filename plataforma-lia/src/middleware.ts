export const runtime = 'nodejs'

import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const DEV_AUTO_LOGIN = process.env.NODE_ENV !== 'production'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const IS_PRODUCTION = process.env.NODE_ENV === 'production'
const COOKIE_SECURE = IS_PRODUCTION
const COOKIE_SAMESITE: 'lax' | 'none' = IS_PRODUCTION ? 'none' : 'lax'

const PUBLIC_PATHS = [
  '/login',
  '/privacidade',
  '/portal',
  '/vagas',
  '/shared',
  '/forgot-password',
  '/acesso-negado',
]

const PUBLIC_API_PATHS = [
  '/api/auth',
  '/api/backend-proxy/auth/login',
  '/api/backend-proxy/auth/register',
  '/api/public-proxy',
  '/api/portal',
]

const STATIC_PATHS = [
  '/_next',
  '/fonts',
  '/logos',
  '/images',
  '/favicon',
]

function isPublicPath(pathname: string): boolean {
  if (STATIC_PATHS.some(p => pathname.startsWith(p))) return true
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) return true
  if (PUBLIC_API_PATHS.some(p => pathname.startsWith(p))) return true
  if (pathname.startsWith('/api/v1')) return true
  if (pathname.endsWith('.ico') || pathname.endsWith('.png') || pathname.endsWith('.jpg') || pathname.endsWith('.svg') || pathname.endsWith('.webp')) return true
  return false
}

function getBaseUrl(request: NextRequest): string {
  const forwardedHost = request.headers.get('x-forwarded-host')
  const forwardedProto = request.headers.get('x-forwarded-proto') || 'https'
  if (forwardedHost) {
    return `${forwardedProto}://${forwardedHost}`
  }
  const host = request.headers.get('host') || 'localhost:5000'
  return `http://${host}`
}

let cachedDevToken: { token: string; expiresAt: number } | null = null

async function getDevToken(): Promise<string | null> {
  if (cachedDevToken && cachedDevToken.expiresAt > Date.now()) {
    return cachedDevToken.token
  }

  const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
  const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      signal: AbortSignal.timeout(15000),
    })
    if (!res.ok) return null
    const data = await res.json()
    const token = data.access_token || data?.data?.access_token
    if (!token) return null

    cachedDevToken = {
      token,
      expiresAt: Date.now() + 25 * 60 * 1000,
    }
    return token
  } catch {
    return null
  }
}

function denyAccess(request: NextRequest, pathname: string): NextResponse {
  if (pathname.startsWith('/api/')) {
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    )
  }

  const base = getBaseUrl(request)
  const loginUrl = new URL('/login', base)
  loginUrl.searchParams.set('next', pathname)
  return NextResponse.redirect(loginUrl)
}

async function verifyJwt(token: string): Promise<Record<string, unknown> | null> {
  const secret = process.env.SECRET_KEY || process.env.JWT_SECRET
  if (secret) {
    try {
      const secretKey = new TextEncoder().encode(secret)
      const { payload } = await jwtVerify(token, secretKey, {
        algorithms: ['HS256'],
      })
      return payload as Record<string, unknown>
    } catch {
      return null
    }
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` },
      signal: AbortSignal.timeout(3000),
    })
    if (!response.ok) return null
    const data = await response.json()
    return { sub: data.id || data.sub, role: data.role || data.user_role, verified_by_backend: true }
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (isPublicPath(pathname)) {
    return NextResponse.next()
  }

  if (DEV_AUTO_LOGIN) {
    const token = await getDevToken()
    if (token) {
      const requestHeaders = new Headers(request.headers)
      requestHeaders.set('Authorization', `Bearer ${token}`)

      const response = NextResponse.next({ request: { headers: requestHeaders } })

      response.cookies.set('lia_access_token', token, {
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
        secure: COOKIE_SECURE,
        sameSite: COOKIE_SAMESITE,
        httpOnly: true,
      })
      response.cookies.set('lia_auth_method', 'dev-auto-login', {
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
        secure: COOKIE_SECURE,
        sameSite: COOKIE_SAMESITE,
        httpOnly: false,
      })

      response.cookies.delete("lia_logged_out")
      return response
    }
  }

  const accessTokenCookie = request.cookies.get('lia_access_token')
  const workosSessionCookie = request.cookies.get('workos_session')

  if (workosSessionCookie?.value) {
    const sessionData = verifyAndDecodeSession(workosSessionCookie.value)
    if (!sessionData) {
      return denyAccess(request, pathname)
    }

    const requestHeaders = new Headers(request.headers)
    if (sessionData.accessToken && !requestHeaders.get('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${sessionData.accessToken}`)
      requestHeaders.set('X-Auth-Method', 'workos')
    }

    return NextResponse.next({
      request: { headers: requestHeaders },
    })
  }

  if (accessTokenCookie && accessTokenCookie.value !== '_sso_session_') {
    const token = accessTokenCookie.value

    const payload = await verifyJwt(token)
    if (!payload) {
      return denyAccess(request, pathname)
    }

    const requestHeaders = new Headers(request.headers)
    if (!requestHeaders.get('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }

    return NextResponse.next({
      request: { headers: requestHeaders },
    })
  }

  return denyAccess(request, pathname)
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
