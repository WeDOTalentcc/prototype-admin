export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const DEV_AUTO_LOGIN = process.env.NODE_ENV !== 'production'

let cachedDevToken: { token: string; expiresAt: number } | null = null

async function getDevToken(): Promise<string | null> {
  if (cachedDevToken && cachedDevToken.expiresAt > Date.now()) {
    return cachedDevToken.token
  }
  const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
  const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      signal: AbortSignal.timeout(15000),
    })
    if (!res.ok) return null
    const data = await res.json()
    const token = data.access_token || data?.data?.access_token
    if (!token) return null
    cachedDevToken = { token, expiresAt: Date.now() + 25 * 60 * 1000 }
    return token
  } catch {
    return null
  }
}

export async function GET(request: NextRequest) {
  const tokenCookie = request.cookies.get('lia_access_token')
  if (tokenCookie?.value && tokenCookie.value !== '_sso_session_') {
    return NextResponse.json({ token: tokenCookie.value })
  }

  const workosSession = request.cookies.get('workos_session')
  if (workosSession?.value) {
    const sessionData = verifyAndDecodeSession(workosSession.value)
    if (sessionData?.accessToken) {
      return NextResponse.json({ token: sessionData.accessToken })
    }
  }

  if (DEV_AUTO_LOGIN) {
    const devToken = await getDevToken()
    if (devToken) {
      const response = NextResponse.json({ token: devToken })
      response.cookies.set('lia_access_token', devToken, {
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
        httpOnly: true,
      })
      return response
    }
  }

  return NextResponse.json({ token: null }, { status: 401 })
}
