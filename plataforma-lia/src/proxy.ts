import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'
import { verifyAndDecodeSession } from '@/lib/session-crypto'
import { getDevToken, isDevAutoLoginEnabled } from '@/lib/auth/dev-auto-login'
import createMiddleware from 'next-intl/middleware'
import { routing } from '@/i18n/routing'
import { locales, defaultLocale } from '@/i18n/config'

const DEV_AUTO_LOGIN = isDevAutoLoginEnabled()
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const IS_PRODUCTION = process.env.NODE_ENV === 'production'
const COOKIE_SECURE = IS_PRODUCTION
const COOKIE_SAMESITE: 'lax' | 'none' = IS_PRODUCTION ? 'none' : 'lax'

const intlMiddleware = createMiddleware(routing)

const PUBLIC_PATHS = [
  '/login',
  '/privacidade',
  '/privacy',
  '/portal',
  '/vagas',
  '/jobs',
  '/shared',
  '/forgot-password',
  '/acesso-negado',
  '/register',
  '/reset-password',
  '/triagem',
  '/aceitar-convite',
  '/accept-invitation',
  '/access',
  '/candidate',  // Candidate self-service portal — public JWT-auth
]

const PUBLIC_API_PATHS = [
  '/api/auth',
  '/api/backend-proxy/auth',
  '/api/public-proxy',
  '/api/portal',
  '/api/v1/teams/messages',
  '/api/v1/teams/webhook',
  '/api/v1/teams/health',
]

const STATIC_PATHS = [
  '/_next',
  '/fonts',
  '/logos',
  '/images',
  '/favicon',
  '/__mockup',
]

function stripLocalePrefix(pathname: string): string {
  for (const locale of locales) {
    if (pathname === `/${locale}`) return '/'
    if (pathname.startsWith(`/${locale}/`)) return pathname.slice(locale.length + 1)
  }
  return pathname
}

function isStaticOrApiPath(pathname: string): boolean {
  if (STATIC_PATHS.some(p => pathname.startsWith(p))) return true
  if (pathname.startsWith('/api/')) return true
  if (pathname.endsWith('.ico') || pathname.endsWith('.png') || pathname.endsWith('.jpg') || pathname.endsWith('.svg') || pathname.endsWith('.webp') || pathname.endsWith('.json') || pathname.endsWith('.xml') || pathname.endsWith('.txt')) return true
  return false
}

function isPublicPath(strippedPathname: string): boolean {
  if (PUBLIC_PATHS.some(p => strippedPathname.startsWith(p))) return true
  return false
}

function isPublicApiPath(pathname: string): boolean {
  if (PUBLIC_API_PATHS.some(p => pathname.startsWith(p))) return true
  // P1-5 (audit 2026-06-05): REMOVIDO `if (pathname.startsWith('/api/v1')) return true`.
  // A regra blanket marcava TODO /api/v1 como público → o middleware encaminhava
  // sem Bearer → backend 401 (quebrava agendar entrevista / gerar e-mail LIA).
  // Fluxos públicos reais usam prefixos dedicados (/api/auth, /api/public-proxy,
  // /api/portal) já listados em PUBLIC_API_PATHS.
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

function extractLocaleFromPath(pathname: string): string {
  for (const locale of locales) {
    if (pathname === `/${locale}` || pathname.startsWith(`/${locale}/`)) {
      return locale
    }
  }
  return defaultLocale
}

function denyAccess(request: NextRequest, pathname: string): NextResponse {
  if (pathname.startsWith('/api/')) {
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    )
  }

  const base = getBaseUrl(request)
  const currentLocale = extractLocaleFromPath(pathname)
  const loginUrl = new URL(`/${currentLocale}/login`, base)
  loginUrl.searchParams.set('next', pathname)
  return NextResponse.redirect(loginUrl)
}


// Phase 1c (2026-06-10): transparent Rails→FastAPI token upgrade.
// When FASTAPI_AUTH_PRIMARY becomes true, Rails JWTs are rejected with
// 401 + upgrade_required=true. This interceptor silently exchanges them
// so logged-in users are never kicked out.
async function tryUpgradeRailsToken(token: string): Promise<string | null> {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/v1/auth/exchange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rails_token: token }),
      signal: AbortSignal.timeout(3000),
    })
    if (!resp.ok) return null
    const data = await resp.json().catch(() => null)
    return data?.access_token ?? null
  } catch {
    return null
  }
}

// Returns a NextResponse with the new FastAPI JWT set as lia_access_token cookie
// AND forwarded as Authorization header for the current request.
async function tryUpgradeAndForward(
  request: NextRequest,
  oldToken: string,
): Promise<NextResponse | null> {
  const newToken = await tryUpgradeRailsToken(oldToken)
  if (!newToken) return null
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('Authorization', `Bearer ${newToken}`)
  const response = NextResponse.next({ request: { headers: requestHeaders } })
  response.cookies.set('lia_access_token', newToken, {
    httpOnly: true,
    secure: COOKIE_SECURE,
    sameSite: COOKIE_SAMESITE,
    maxAge: 86400,
    path: '/',
  })
  return response
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

function applyAuthHeaders(request: NextRequest, token: string): NextResponse {
  const requestHeaders = new Headers(request.headers)
  if (!requestHeaders.get('Authorization')) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }
  return NextResponse.next({ request: { headers: requestHeaders } })
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname === '/') {
    const base = getBaseUrl(request)
    const cookieLocale = request.cookies.get('NEXT_LOCALE')?.value
    const preferredLocale = (locales as readonly string[]).includes(cookieLocale ?? '')
      ? (cookieLocale as string)
      : defaultLocale
    // Rewrite (not redirect) so GET / returns 200 for the deploy health-check,
    // while still enforcing auth. Serve the dashboard only when a session is
    // actually VALID (signature/expiry checked, not mere cookie presence);
    // otherwise serve the public login page. Use /<locale> without a trailing
    // slash to avoid Next's 308 trailing-slash normalization.
    let authenticated = false
    if (DEV_AUTO_LOGIN) {
      authenticated = Boolean(await getDevToken())
    } else {
      const workosSession = request.cookies.get('workos_session')?.value
      if (workosSession) {
        const sessionData = verifyAndDecodeSession(workosSession)
        authenticated = Boolean(sessionData?.accessToken)
      }
      if (!authenticated) {
        const accessToken = request.cookies.get('lia_access_token')?.value
        if (accessToken && accessToken !== '_sso_session_') {
          authenticated = Boolean(await verifyJwt(accessToken))
        }
      }
    }
    const target = authenticated
      ? `/${preferredLocale}`
      : `/${preferredLocale}/login`
    return NextResponse.rewrite(new URL(target, base))
  }

  if (isStaticOrApiPath(pathname)) {
    if (pathname.startsWith('/api/') && !isPublicApiPath(pathname)) {
      const accessTokenCookie = request.cookies.get('lia_access_token')
      let devAutoLoginFailed = false
      if (DEV_AUTO_LOGIN) {
        const token = await getDevToken()
        if (token) {
          const requestHeaders = new Headers(request.headers)
          requestHeaders.set('Authorization', `Bearer ${token}`)
          const response = NextResponse.next({ request: { headers: requestHeaders } })
          response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate')
          response.headers.set('Pragma', 'no-cache')
          return response
        }
        devAutoLoginFailed = true
      }
      if (accessTokenCookie && accessTokenCookie.value !== '_sso_session_') {
        const payload = await verifyJwt(accessTokenCookie.value)
        if (payload) return applyAuthHeaders(request, accessTokenCookie.value)
        // verifyJwt failed — may be a Rails JWT; attempt transparent upgrade (Phase 1c)
        const upgraded = await tryUpgradeAndForward(request, accessTokenCookie.value)
        if (upgraded) return upgraded
      }
      const workosSessionCookie = request.cookies.get('workos_session')
      if (workosSessionCookie?.value) {
        const sessionData = verifyAndDecodeSession(workosSessionCookie.value)
        if (sessionData?.accessToken) {
          const requestHeaders = new Headers(request.headers)
          requestHeaders.set('Authorization', `Bearer ${sessionData.accessToken}`)
          requestHeaders.set('X-Auth-Method', 'workos')
          return NextResponse.next({ request: { headers: requestHeaders } })
        }
      }
      if (devAutoLoginFailed) {
        return NextResponse.json(
          {
            error: 'dev_auto_login_failed',
            message:
              'Dev auto-login failed: the demo user could not authenticate against the backend. Check DEV_AUTO_LOGIN_EMAIL/DEV_AUTO_LOGIN_PASSWORD env vars or re-seed the demo user in lia-backend. See server logs for the [dev-auto-login] entry.',
          },
          { status: 503 },
        )
      }
      return denyAccess(request, pathname)
    }
    return NextResponse.next()
  }

  const strippedPath = stripLocalePrefix(pathname)

  if (isPublicPath(strippedPath)) {
    if (DEV_AUTO_LOGIN && strippedPath.startsWith('/login')) {
      const token = await getDevToken()
      if (token) {
        const next = request.nextUrl.searchParams.get('next') || `/${extractLocaleFromPath(pathname)}`
        const base = getBaseUrl(request)
        const redirectUrl = new URL(next, base)
        const response = NextResponse.redirect(redirectUrl)
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
    return intlMiddleware(request)
  }

  if (DEV_AUTO_LOGIN) {
    const token = await getDevToken()
    if (token) {
      const intlResponse = intlMiddleware(request)

      const requestHeaders = new Headers(request.headers)
      requestHeaders.set('Authorization', `Bearer ${token}`)

      const isRedirect = intlResponse.status >= 300 && intlResponse.status < 400
      if (isRedirect) {
        intlResponse.cookies.set('lia_access_token', token, {
          path: '/',
          maxAge: 60 * 60 * 24 * 7,
          secure: COOKIE_SECURE,
          sameSite: COOKIE_SAMESITE,
          httpOnly: true,
        })
        intlResponse.cookies.set('lia_auth_method', 'dev-auto-login', {
          path: '/',
          maxAge: 60 * 60 * 24 * 7,
          secure: COOKIE_SECURE,
          sameSite: COOKIE_SAMESITE,
          httpOnly: false,
        })
        intlResponse.cookies.delete("lia_logged_out")
        return intlResponse
      }

      const response = NextResponse.next({ request: { headers: requestHeaders } })

      for (const [key, value] of intlResponse.headers.entries()) {
        response.headers.set(key, value)
      }

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

    const intlResponse = intlMiddleware(request)
    const isRedirect = intlResponse.status >= 300 && intlResponse.status < 400
    if (isRedirect) return intlResponse

    const requestHeaders = new Headers(request.headers)
    if (sessionData.accessToken && !requestHeaders.get('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${sessionData.accessToken}`)
      requestHeaders.set('X-Auth-Method', 'workos')
    }

    const response = NextResponse.next({ request: { headers: requestHeaders } })
    for (const [key, value] of intlResponse.headers.entries()) {
      response.headers.set(key, value)
    }
    return response
  }

  if (accessTokenCookie && accessTokenCookie.value !== '_sso_session_') {
    const token = accessTokenCookie.value
    const payload = await verifyJwt(token)
    if (!payload) {
      // Attempt transparent Rails→FastAPI upgrade before denying (Phase 1c)
      const upgraded = await tryUpgradeAndForward(request, token)
      if (upgraded) {
        const intlResp = intlMiddleware(request)
        if (intlResp.status >= 300 && intlResp.status < 400) return intlResp
        for (const [k, v] of intlResp.headers.entries()) upgraded.headers.set(k, v)
        return upgraded
      }
      return denyAccess(request, pathname)
    }

    const intlResponse = intlMiddleware(request)
    const isRedirect = intlResponse.status >= 300 && intlResponse.status < 400
    if (isRedirect) return intlResponse

    const requestHeaders = new Headers(request.headers)
    if (!requestHeaders.get('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }

    const response = NextResponse.next({ request: { headers: requestHeaders } })
    for (const [key, value] of intlResponse.headers.entries()) {
      response.headers.set(key, value)
    }
    return response
  }

  return denyAccess(request, pathname)
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
