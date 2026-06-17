export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { verifyAndDecodeSession } from '@/lib/session-crypto'
import { getDevToken, isDevAutoLoginEnabled } from '@/lib/auth/dev-auto-login'

type WsTokenError = {
  token: null
  code:
    | 'no_credentials'
    | 'invalid_workos_session'
    | 'dev_auto_login_failed'
    | 'unauthenticated'
  reason: string
  authMode: 'jwt-cookie' | 'workos' | 'dev-auto-login' | 'none'
}

function errorResponse(status: number, body: WsTokenError) {
  // no-store evita que browsers/proxies guardem 401/503 transitórios e
  // contaminem o ciclo de relogin (Task #298, audit causa #8).
  const res = NextResponse.json(body, { status })
  res.headers.set('Cache-Control', 'no-store')
  return res
}

export async function GET(request: NextRequest) {
  const tokenCookie = request.cookies.get('lia_access_token')
  if (tokenCookie?.value && tokenCookie.value !== '_sso_session_') {
    return NextResponse.json({ token: tokenCookie.value, authMode: 'jwt-cookie' })
  }

  const workosSession = request.cookies.get('workos_session')
  if (workosSession?.value) {
    const sessionData = verifyAndDecodeSession(workosSession.value)
    if (sessionData?.accessToken) {
      return NextResponse.json({ token: sessionData.accessToken, authMode: 'workos' })
    }
    return errorResponse(401, {
      token: null,
      code: 'invalid_workos_session',
      reason: 'workos_session cookie present but failed signature/expiry verification',
      authMode: 'workos',
    })
  }

  if (isDevAutoLoginEnabled()) {
    const devToken = await getDevToken()
    if (devToken) {
      const response = NextResponse.json({ token: devToken, authMode: 'dev-auto-login' })
      response.cookies.set('lia_access_token', devToken, {
        path: '/',
        maxAge: 60 * 60 * 24 * 7,
        httpOnly: true,
      })
      return response
    }
    return errorResponse(503, {
      token: null,
      code: 'dev_auto_login_failed',
      reason: 'Backend /api/v1/auth/login did not return a token for the demo user',
      authMode: 'dev-auto-login',
    })
  }

  return errorResponse(401, {
    token: null,
    code: 'no_credentials',
    reason: 'No lia_access_token cookie, no workos_session, dev auto-login disabled',
    authMode: 'none',
  })
}
