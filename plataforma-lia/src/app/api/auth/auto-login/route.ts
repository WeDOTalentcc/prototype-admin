export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

const IS_PRODUCTION = process.env.NODE_ENV === 'production'

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

    const safeRedirect = redirectTo.startsWith('/') && !redirectTo.startsWith('//') ? redirectTo : '/'
    const forwardedHost = request.headers.get('x-forwarded-host')
    const forwardedProto = request.headers.get('x-forwarded-proto') || 'https'
    const host = forwardedHost || request.headers.get('host') || 'localhost:5000'
    const protocol = forwardedHost ? forwardedProto : 'http'
    const baseUrl = `${protocol}://${host}`

    const response = NextResponse.redirect(new URL(safeRedirect, baseUrl))

    const cookieBase = {
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
      secure: IS_PRODUCTION,
      sameSite: 'lax' as const,
    }

    response.cookies.set('lia_access_token', accessToken, { ...cookieBase, httpOnly: true })
    if (refreshToken) {
      response.cookies.set('lia_refresh_token', refreshToken, { ...cookieBase, httpOnly: true })
    }
    response.cookies.set('lia_auth_method', 'jwt', { ...cookieBase, httpOnly: false })

    return response
  } catch {
    const url = new URL('/login', request.url)
    url.searchParams.set('error', 'backend-unreachable')
    return NextResponse.redirect(url)
  }
}
