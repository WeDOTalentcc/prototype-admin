export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { z } from 'zod'

const sessionBodySchema = z.object({
  access_token: z.string().min(1, 'access_token is required'),
  refresh_token: z.string().optional(),
  auth_method: z.string().optional(),
})

function isSecureContext(request: NextRequest): boolean {
  const proto = request.headers.get('x-forwarded-proto')
  return proto === 'https' || process.env.NODE_ENV === 'production'
}

export async function POST(request: NextRequest) {
  try {
    const origin = request.headers.get('origin')
    const host = request.headers.get('host')
    const forwardedHost = request.headers.get('x-forwarded-host')
    const effectiveHost = forwardedHost || host
    if (origin && effectiveHost) {
      let originHost: string
      try {
        originHost = new URL(origin).host
      } catch {
        return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
      }
      if (originHost !== effectiveHost) {
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

    const isProd = process.env.NODE_ENV === 'production'
    const cookieOpts = {
      httpOnly: true,
      secure: isProd,
      sameSite: (isProd ? 'none' : 'lax') as 'none' | 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 7,
    }

    const response = NextResponse.json({ success: true })

    response.cookies.set('lia_access_token', access_token, cookieOpts)
    if (refresh_token) {
      response.cookies.set('lia_refresh_token', refresh_token, cookieOpts)
    }
    response.cookies.set('lia_auth_method', auth_method || 'jwt', {
      ...cookieOpts,
      httpOnly: false,
    })

    return response
  } catch {
    return NextResponse.json(
      { error: 'Failed to create session' },
      { status: 500 }
    )
  }
}

export async function DELETE() {
  try {
    const response = NextResponse.json({ success: true })
    response.cookies.delete('lia_access_token')
    response.cookies.delete('lia_refresh_token')
    response.cookies.delete('lia_auth_method')
    return response
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

    let user: Record<string, unknown> | null = null
    if (accessToken?.value) {
      try {
        const parts = accessToken.value.split('.')
        if (parts.length === 3) {
          const payload = JSON.parse(
            Buffer.from(parts[1], 'base64url').toString('utf-8')
          )
          user = {
            company_id: payload.company_id || payload.company || null,
            company: payload.company_name || payload.company || null,
            email: payload.email || payload.sub || null,
          }
        }
      } catch {
      }
    }

    return NextResponse.json({
      authenticated: !!accessToken,
      authMethod: authMethod?.value || null,
      user,
    })
  } catch {
    return NextResponse.json(
      { authenticated: false, authMethod: null, user: null },
      { status: 500 }
    )
  }
}
