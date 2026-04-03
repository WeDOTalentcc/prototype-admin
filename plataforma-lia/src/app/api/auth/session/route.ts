export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

const SESSION_FLAG_OPTIONS = {
  httpOnly: false,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

export async function POST(request: NextRequest) {
  try {
    const origin = request.headers.get('origin')
    const host = request.headers.get('host')
    if (origin && host && !origin.includes(host.split(':')[0])) {
      return NextResponse.json(
        { error: 'Invalid origin' },
        { status: 403 }
      )
    }

    const body = await request.json()
    const { access_token, refresh_token, auth_method } = body

    if (!access_token) {
      return NextResponse.json(
        { error: 'access_token is required' },
        { status: 400 }
      )
    }

    const cookieStore = await cookies()

    cookieStore.set('lia_access_token', access_token, COOKIE_OPTIONS)

    if (refresh_token) {
      cookieStore.set('lia_refresh_token', refresh_token, COOKIE_OPTIONS)
    }

    cookieStore.set('lia_auth_method', auth_method || 'jwt', SESSION_FLAG_OPTIONS)

    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json(
      { error: 'Failed to create session' },
      { status: 500 }
    )
  }
}

export async function DELETE() {
  try {
    const cookieStore = await cookies()

    cookieStore.delete('lia_access_token')
    cookieStore.delete('lia_refresh_token')
    cookieStore.delete('lia_auth_method')

    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json(
      { error: 'Failed to clear session' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const cookieStore = await cookies()
    const accessToken = cookieStore.get('lia_access_token')
    const authMethod = cookieStore.get('lia_auth_method')

    return NextResponse.json({
      authenticated: !!accessToken,
      authMethod: authMethod?.value || null,
    })
  } catch {
    return NextResponse.json(
      { authenticated: false, authMethod: null },
      { status: 500 }
    )
  }
}
