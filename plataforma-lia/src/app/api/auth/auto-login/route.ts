export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { loginDemoUser, isDevAutoLoginEnabled } from '@/lib/auth/dev-auto-login'

const IS_PRODUCTION = process.env.NODE_ENV === 'production'

export async function GET(request: NextRequest) {
  if (!isDevAutoLoginEnabled()) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  const redirectTo = request.nextUrl.searchParams.get('next') || '/'

  try {
    const result = await loginDemoUser()

    if (!result) {
      const url = new URL('/login', request.url)
      url.searchParams.set('error', 'auto-login-failed')
      return NextResponse.redirect(url)
    }

    const accessToken = result.accessToken
    const refreshToken = result.refreshToken

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
      sameSite: (IS_PRODUCTION ? 'none' : 'lax') as 'none' | 'lax',
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
