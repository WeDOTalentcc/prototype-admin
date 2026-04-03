export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { z } from 'zod'

const sessionBodySchema = z.object({
  access_token: z.string().min(1, 'access_token is required'),
  refresh_token: z.string().optional(),
  auth_method: z.string().optional(),
})

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

const SESSION_FLAG_OPTIONS = {
  httpOnly: false,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict' as const,
  path: '/',
  maxAge: 60 * 60 * 24 * 7,
}

export async function POST(request: NextRequest) {
  try {
    const origin = request.headers.get('origin')
    const host = request.headers.get('host')
    if (origin && host) {
      let originHost: string
      try {
        originHost = new URL(origin).host
      } catch {
        return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
      }
      if (originHost !== host) {
        return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
      }
    }

    let body: unknown
    try {
      body = await request.json()
    } catch {
      return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
    }

    const parsed = sessionBodySchema.safeParse(body)
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Validation error', details: parsed.error.flatten() },
        { status: 400 }
      )
    }
    const { access_token, refresh_token, auth_method } = parsed.data

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
