export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { verifyAndDecodeSession } from '@/lib/session-crypto'
import { getDevToken, isDevAutoLoginEnabled } from '@/lib/auth/dev-auto-login'

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

  if (isDevAutoLoginEnabled()) {
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
