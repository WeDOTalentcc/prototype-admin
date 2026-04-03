import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'

const PUBLIC_PATHS = [
  '/login',
  '/privacidade',
  '/portal',
  '/vagas',
  '/shared',
  '/forgot-password',
  '/acesso-negado',
  '/demo-onboarding',
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
  if (pathname === '/') return true
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) return true
  if (PUBLIC_API_PATHS.some(p => pathname.startsWith(p))) return true
  if (pathname.startsWith('/api/v1')) return true
  if (pathname.endsWith('.ico') || pathname.endsWith('.png') || pathname.endsWith('.jpg') || pathname.endsWith('.svg') || pathname.endsWith('.webp')) return true
  return false
}

function redirectToLogin(request: NextRequest, pathname: string): NextResponse {
  const loginUrl = new URL('/login', request.url)
  loginUrl.searchParams.set('next', pathname)
  return NextResponse.redirect(loginUrl)
}

async function verifyJwt(token: string): Promise<Record<string, unknown> | null> {
  const secret = process.env.SECRET_KEY || process.env.JWT_SECRET
  if (!secret) return null
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

async function validateWorkosSession(request: NextRequest): Promise<boolean> {
  const workosSession = request.cookies.get('workos_session')
  if (!workosSession?.value) return false

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  try {
    const response = await fetch(`${backendUrl}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${workosSession.value}`,
        'X-Auth-Method': 'workos',
      },
      signal: AbortSignal.timeout(3000),
    })
    return response.ok
  } catch {
    return false
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (isPublicPath(pathname)) {
    return NextResponse.next()
  }

  const accessTokenCookie = request.cookies.get('lia_access_token')
  const workosSession = request.cookies.get('workos_session')

  if (workosSession?.value) {
    const isValid = await validateWorkosSession(request)
    if (isValid) {
      return NextResponse.next()
    }
    return redirectToLogin(request, pathname)
  }

  if (!accessTokenCookie || accessTokenCookie.value === '_sso_session_') {
    return redirectToLogin(request, pathname)
  }

  const token = accessTokenCookie.value
  const payload = await verifyJwt(token)
  if (!payload) {
    return redirectToLogin(request, pathname)
  }

  if (pathname.startsWith('/admin')) {
    const role = payload.role || payload.user_role
    if (role !== 'admin') {
      return redirectToLogin(request, pathname)
    }
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
