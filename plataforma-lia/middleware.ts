import { NextRequest, NextResponse } from 'next/server'

// ── Route classifications ────────────────────────────────────────────────────

const PROTECTED_PAGE_PREFIXES = [
  '/funil-de-talentos',
  '/vagas',
  '/busca',
  '/kanban',
  '/chat',
  '/agenda',
  '/configuracoes',
]

const PROTECTED_API_PREFIXES = [
  '/api/backend-proxy',
  '/api/lia',
  '/api/ai',
]

const PUBLIC_PREFIXES = [
  '/login',
  '/register',
  '/api/auth',
  '/api/public-proxy',
  '/portal',
  '/shared',
  '/_next',
  '/favicon',
  '/static',
]

// ── Helpers ──────────────────────────────────────────────────────────────────

function isPublic(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((p) => pathname.startsWith(p))
}

function isProtectedApi(pathname: string): boolean {
  return PROTECTED_API_PREFIXES.some((p) => pathname.startsWith(p))
}

function isProtectedPage(pathname: string): boolean {
  return PROTECTED_PAGE_PREFIXES.some((p) => pathname.startsWith(p))
}

function isAuthenticated(request: NextRequest): boolean {
  // Accept wos-session cookie OR Authorization header
  const sessionCookie = request.cookies.get('wos-session')
  if (sessionCookie?.value) return true

  const authHeader = request.headers.get('authorization')
  if (authHeader?.startsWith('Bearer ')) return true

  return false
}

// ── Middleware ───────────────────────────────────────────────────────────────

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Always allow public routes
  if (isPublic(pathname)) {
    return NextResponse.next()
  }

  // Protected API routes → 401 JSON when unauthenticated
  if (isProtectedApi(pathname)) {
    if (!isAuthenticated(request)) {
      return NextResponse.json(
        { error: 'Unauthorized', message: 'Authentication required' },
        { status: 401 }
      )
    }
    return NextResponse.next()
  }

  // Protected page routes → redirect to /login when unauthenticated
  if (isProtectedPage(pathname)) {
    if (!isAuthenticated(request)) {
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('next', pathname)
      return NextResponse.redirect(loginUrl)
    }
    return NextResponse.next()
  }

  // Everything else passes through
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all paths except static files and Next.js internals.
     * This lets the middleware run for all dynamic routes.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|eot)$).*)',
  ],
}
