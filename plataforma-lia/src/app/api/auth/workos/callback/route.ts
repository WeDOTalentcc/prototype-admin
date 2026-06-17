export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { workos, WORKOS_CONFIG } from '@/lib/workos'
import { cookies } from 'next/headers'
import { signSession, SessionPayload } from '@/lib/session-crypto'

const WORKOS_SESSION_COOKIE = 'workos_session'
const SESSION_DURATION = 60 * 60 * 24 * 7
const INTERNAL_API_SECRET = process.env.INTERNAL_API_SECRET || process.env.WORKOS_WEBHOOK_SECRET

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')
    const errorDescription = searchParams.get('error_description')

    if (error) {
      const loginUrl = new URL('/login', req.url)
      loginUrl.searchParams.set('error', errorDescription || error)
      return NextResponse.redirect(loginUrl)
    }

    if (!code) {
      const loginUrl = new URL('/login', req.url)
      loginUrl.searchParams.set('error', 'No authorization code received')
      return NextResponse.redirect(loginUrl)
    }

    const { profile, accessToken } = await workos.sso.getProfileAndToken({
      code,
      clientId: WORKOS_CONFIG.clientId,
    })

    let returnTo = '/dashboard'
    if (state) {
      try {
        const decodedState = JSON.parse(Buffer.from(state, 'base64').toString())
        returnTo = decodedState.returnTo || '/dashboard'
      } catch {
      }
    }

    const sessionData: SessionPayload = {
      workosProfile: {
        id: profile.id,
        email: profile.email,
        firstName: profile.firstName ?? null,
        lastName: profile.lastName ?? null,
        organizationId: profile.organizationId ?? null,
        connectionId: profile.connectionId,
        connectionType: profile.connectionType,
        idpId: profile.idpId,
      },
      accessToken,
      expiresAt: Date.now() + (SESSION_DURATION * 1000),
      createdAt: Date.now(),
    }

    const signedToken = signSession(sessionData)

    const cookieStore = await cookies()
    cookieStore.set(WORKOS_SESSION_COOKIE, signedToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: SESSION_DURATION,
      path: '/',
    })

    const syncHeaders: HeadersInit = { 'Content-Type': 'application/json' }
    if (INTERNAL_API_SECRET) {
      syncHeaders['X-Internal-Auth'] = INTERNAL_API_SECRET
    }

    const syncResponse = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:8001'}/api/v1/auth/workos/sync-user`, {
      method: 'POST',
      headers: syncHeaders,
      body: JSON.stringify({
        workos_id: profile.id,
        email: profile.email,
        first_name: profile.firstName,
        last_name: profile.lastName,
        organization_id: profile.organizationId,
        connection_type: profile.connectionType,
        raw_attributes: profile.rawAttributes,
      }),
    })

    if (!syncResponse.ok) {
    }

    // Phase 2a (2026-06-10): issue a FastAPI JWT so WorkOS SSO users get
    // lia_access_token (same cookie as password-login) instead of relying on
    // the workos_session cookie + WorkOS accessToken forwarding (which FastAPI
    // cannot validate). Gate: WORKOS_FASTAPI_JWT=true on backend.
    const issueTokenHeaders: HeadersInit = { 'Content-Type': 'application/json' }
    if (INTERNAL_API_SECRET) {
      issueTokenHeaders['X-Internal-Auth'] = INTERNAL_API_SECRET
    }
    const issueTokenResponse = await fetch(
      `${process.env.BACKEND_URL || 'http://127.0.0.1:8001'}/api/v1/auth/workos/issue-token`,
      {
        method: 'POST',
        headers: issueTokenHeaders,
        body: JSON.stringify({ email: profile.email, workos_id: profile.id }),
      },
    ).catch(() => null)

    const welcomeUrl = new URL('/login/welcome', req.url)
    welcomeUrl.searchParams.set('sso', 'true')
    welcomeUrl.searchParams.set('returnTo', returnTo)
    const redirectResponse = NextResponse.redirect(welcomeUrl)

    if (issueTokenResponse?.ok) {
      const tokenData = await issueTokenResponse.json().catch(() => null)
      if (tokenData?.access_token) {
        // Set FastAPI JWT as lia_access_token — same httpOnly cookie as password login.
        // When this cookie is present, proxy.ts prefers it over workos_session.
        redirectResponse.cookies.set('lia_access_token', tokenData.access_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: tokenData.expires_in ?? 86400,
          path: '/',
        })
      }
    }
    // Whether or not issue-token succeeded, workos_session is still set as fallback.
    return redirectResponse
  } catch (error) {
    const loginUrl = new URL('/login', req.url)
    loginUrl.searchParams.set('error', 'Failed to complete SSO login')
    return NextResponse.redirect(loginUrl)
  }
}
