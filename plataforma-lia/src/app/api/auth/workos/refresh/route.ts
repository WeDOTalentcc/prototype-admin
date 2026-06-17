export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession, signSession, SessionPayload } from '@/lib/session-crypto'

const WORKOS_SESSION_COOKIE = 'workos_session'
const SESSION_DURATION = 8 * 60 * 60 * 1000 // 8 hours
const REFRESH_THRESHOLD = 30 * 60 * 1000 // Refresh if less than 30 min left

export async function POST(req: NextRequest) {
  try {
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get(WORKOS_SESSION_COOKIE)

    if (!sessionCookie) {
      return NextResponse.json({ refreshed: false, reason: 'no_session' }, { status: 401 })
    }

    const sessionData = verifyAndDecodeSession(sessionCookie.value)

    if (!sessionData) {
      cookieStore.delete(WORKOS_SESSION_COOKIE)
      return NextResponse.json({ refreshed: false, reason: 'invalid_session' }, { status: 401 })
    }

    // Check if refresh is needed
    const timeUntilExpiry = sessionData.expiresAt - Date.now()
    if (timeUntilExpiry > REFRESH_THRESHOLD) {
      return NextResponse.json({ 
        refreshed: false, 
        reason: 'not_needed',
        expiresAt: sessionData.expiresAt,
        timeUntilExpiry
      })
    }

    // Create new session with extended expiry
    const newSessionData: SessionPayload = {
      ...sessionData,
      expiresAt: Date.now() + SESSION_DURATION,
    }

    const newSessionToken = signSession(newSessionData)

    const response = NextResponse.json({
      refreshed: true,
      expiresAt: newSessionData.expiresAt,
    })

    response.cookies.set(WORKOS_SESSION_COOKIE, newSessionToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: SESSION_DURATION / 1000,
    })

    return response
  } catch (error) {
    return NextResponse.json({ refreshed: false, reason: 'error' }, { status: 500 })
  }
}
