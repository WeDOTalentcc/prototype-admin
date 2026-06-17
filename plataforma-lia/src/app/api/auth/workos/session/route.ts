export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const WORKOS_SESSION_COOKIE = 'workos_session'

export async function GET(req: NextRequest) {
  try {
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get(WORKOS_SESSION_COOKIE)

    if (!sessionCookie) {
      return NextResponse.json({ authenticated: false }, { status: 401 })
    }

    const sessionData = verifyAndDecodeSession(sessionCookie.value)

    if (!sessionData) {
      cookieStore.delete(WORKOS_SESSION_COOKIE)
      return NextResponse.json({ authenticated: false, reason: 'invalid_or_expired' }, { status: 401 })
    }

    return NextResponse.json({
      authenticated: true,
      user: {
        id: sessionData.workosProfile.id,
        email: sessionData.workosProfile.email,
        name: `${sessionData.workosProfile.firstName || ''} ${sessionData.workosProfile.lastName || ''}`.trim(),
        firstName: sessionData.workosProfile.firstName,
        lastName: sessionData.workosProfile.lastName,
        organizationId: sessionData.workosProfile.organizationId,
        connectionType: sessionData.workosProfile.connectionType,
        authMethod: 'sso',
      },
      expiresAt: sessionData.expiresAt,
      refreshAt: sessionData.expiresAt - (30 * 60 * 1000),
    })
  } catch (error) {
    return NextResponse.json({ authenticated: false }, { status: 500 })
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const cookieStore = await cookies()
    cookieStore.delete(WORKOS_SESSION_COOKIE)
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ error: 'Failed to logout' }, { status: 500 })
  }
}
