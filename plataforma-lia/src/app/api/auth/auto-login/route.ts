export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const IS_PRODUCTION = process.env.NODE_ENV === 'production'

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: IS_PRODUCTION,
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

const SESSION_FLAG_OPTIONS = {
  httpOnly: false,
  secure: IS_PRODUCTION,
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

export async function GET(request: NextRequest) {
  if (IS_PRODUCTION) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
  const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'

  const redirectTo = request.nextUrl.searchParams.get('next') || '/'

  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

  try {
    const loginResponse = await fetch(`${backendUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      signal: AbortSignal.timeout(5000),
    })

    if (!loginResponse.ok) {
      const url = new URL('/login', request.url)
      url.searchParams.set('error', 'auto-login-failed')
      return NextResponse.redirect(url)
    }

    const data = await loginResponse.json()
    const accessToken = data.access_token
    const refreshToken = data.refresh_token

    if (!accessToken) {
      const url = new URL('/login', request.url)
      url.searchParams.set('error', 'no-token')
      return NextResponse.redirect(url)
    }

    const cookieStore = await cookies()
    cookieStore.set('lia_access_token', accessToken, COOKIE_OPTIONS)
    if (refreshToken) {
      cookieStore.set('lia_refresh_token', refreshToken, COOKIE_OPTIONS)
    }
    cookieStore.set('lia_auth_method', 'jwt', SESSION_FLAG_OPTIONS)

    const safeRedirect = redirectTo.startsWith('/') && !redirectTo.startsWith('//') ? redirectTo : '/'
    const baseUrl = new URL(request.url)
    const host = request.headers.get('host')
    if (host) {
      baseUrl.host = host
    }
    return NextResponse.redirect(new URL(safeRedirect, baseUrl))
  } catch {
    const url = new URL('/login', request.url)
    url.searchParams.set('error', 'backend-unreachable')
    return NextResponse.redirect(url)
  }
}
