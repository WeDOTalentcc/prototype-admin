export const runtime = 'nodejs'

import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const DEV_AUTO_LOGIN = process.env.NODE_ENV !== 'production'

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

function denyAccess(request: NextRequest, pathname: string): NextResponse {
  if (pathname.startsWith('/api/')) {
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    )
  }

  if (DEV_AUTO_LOGIN) {
    const autoLoginUrl = new URL('/api/auth/auto-login', request.url)
    autoLoginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(autoLoginUrl)
  }

  const loginUrl = new URL('/login', request.url)
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

  const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8001'
  try {
    const response = await fetch(`${backendUrl}/api/v1/auth/me`, {
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

  if (!accessTokenCookie || accessTokenCookie.value === '_sso_session_') {
    return denyAccess(request, pathname)
  }

  const token = accessTokenCookie.value

  if (DEV_AUTO_LOGIN) {
    const requestHeaders = new Headers(request.headers)
    if (!requestHeaders.get('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }
    return NextResponse.next({ request: { headers: requestHeaders } })
  }

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

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
