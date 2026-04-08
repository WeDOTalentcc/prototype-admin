export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

function isSecureContext(request: NextRequest): boolean {
  const proto = request.headers.get('x-forwarded-proto')
  return proto === 'https' || process.env.NODE_ENV === 'production'
}

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const refreshTokenCookie = cookieStore.get('lia_refresh_token')

    if (!refreshTokenCookie) {
      return NextResponse.json(
        { error: 'No refresh token available' },
        { status: 401 }
      )
    }

    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshTokenCookie.value }),
    })

    if (!backendResponse.ok) {
      const response = NextResponse.json(
        { error: 'Token refresh failed' },
        { status: backendResponse.status }
      )
      response.cookies.delete('lia_access_token')
      response.cookies.delete('lia_refresh_token')
      response.cookies.delete('lia_auth_method')
      return response
    }

    const data = await backendResponse.json()

    const secure = isSecureContext(request)
    const cookieOpts = {
      httpOnly: true,
      secure,
      sameSite: 'lax' as const,
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
    }

    const response = NextResponse.json({ success: true })
    response.cookies.set('lia_access_token', data.access_token, cookieOpts)
    if (data.refresh_token) {
      response.cookies.set('lia_refresh_token', data.refresh_token, cookieOpts)
    }

    return response
  } catch {
    return NextResponse.json(
      { error: 'Failed to refresh session' },
      { status: 500 }
    )
  }
}
