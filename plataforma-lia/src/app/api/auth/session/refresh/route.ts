export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

export async function POST(_request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const refreshTokenCookie = cookieStore.get('lia_refresh_token')

    if (!refreshTokenCookie) {
      return NextResponse.json(
        { error: 'No refresh token available' },
        { status: 401 }
      )
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshTokenCookie.value }),
    })

    if (!response.ok) {
      cookieStore.delete('lia_access_token')
      cookieStore.delete('lia_refresh_token')
      cookieStore.delete('lia_auth_method')

      return NextResponse.json(
        { error: 'Token refresh failed' },
        { status: response.status }
      )
    }

    const data = await response.json()

    cookieStore.set('lia_access_token', data.access_token, COOKIE_OPTIONS)
    if (data.refresh_token) {
      cookieStore.set('lia_refresh_token', data.refresh_token, COOKIE_OPTIONS)
    }

    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json(
      { error: 'Failed to refresh session' },
      { status: 500 }
    )
  }
}
