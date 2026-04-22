import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession, SessionPayload } from '@/lib/session-crypto'

const WORKOS_SESSION_COOKIE = 'workos_session'
const JWT_COOKIE = 'lia_access_token'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'
const DEV_FALLBACK_COMPANY = process.env.NEXT_PUBLIC_DEV_COMPANY_ID || ''

export interface ResolvedSession {
  companyId: string
  userId: string
  userRole: string
  accessToken?: string
  rawSession: SessionPayload | JWTPayload | null
}

export interface AuthSuccess {
  success: true
  headers: Record<string, string>
  session: ResolvedSession
}

export interface AuthFailure {
  success: false
  response: NextResponse
}

export type AuthResult = AuthSuccess | AuthFailure

interface JWTPayload {
  sub?: string
  email?: string
  company_id?: string
  company?: string
  company_name?: string
  role?: string
  user_role?: string
}

function decodeJwtPayload(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    return JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf-8')) as JWTPayload
  } catch {
    return null
  }
}

function buildHeaders(session: ResolvedSession): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Company-ID': session.companyId,
    'X-User-ID': session.userId,
    'X-User-Role': session.userRole,
  }
  if (session.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`
  }
  return headers
}

function devFallback(): AuthSuccess | null {
  if (!IS_DEVELOPMENT || !DEV_FALLBACK_COMPANY) return null
  const session: ResolvedSession = {
    companyId: DEV_FALLBACK_COMPANY,
    userId: 'dev-user',
    userRole: 'admin',
    rawSession: null,
  }
  return { success: true, headers: buildHeaders(session), session }
}

function unauthorizedResponse(code: 'UNAUTHORIZED' | 'SESSION_EXPIRED'): AuthFailure {
  const message = code === 'UNAUTHORIZED' ? 'Não autenticado' : 'Sessão inválida ou expirada'
  return {
    success: false,
    response: NextResponse.json({ error: message, code }, { status: 401 }),
  }
}

export async function getSessionAuth(): Promise<AuthResult> {
  const cookieStore = await cookies()

  const workosCookie = cookieStore.get(WORKOS_SESSION_COOKIE)
  if (workosCookie?.value) {
    const data = verifyAndDecodeSession(workosCookie.value)
    if (data) {
      const companyId = data.workosProfile.organizationId || data.workosProfile.id
      if (!companyId) return unauthorizedResponse('SESSION_EXPIRED')
      const session: ResolvedSession = {
        companyId,
        userId: data.workosProfile.id,
        userRole: data.workosProfile.connectionType === 'SSO' ? 'admin' : 'user',
        accessToken: data.accessToken,
        rawSession: data,
      }
      return { success: true, headers: buildHeaders(session), session }
    }
  }

  const jwtCookie = cookieStore.get(JWT_COOKIE)
  if (jwtCookie?.value && jwtCookie.value !== '_sso_session_') {
    const payload = decodeJwtPayload(jwtCookie.value)
    const companyId = payload?.company_id || payload?.company || ''
    const userId = payload?.sub || payload?.email || ''
    if (companyId && userId) {
      const session: ResolvedSession = {
        companyId,
        userId,
        userRole: payload?.role || payload?.user_role || 'user',
        accessToken: jwtCookie.value,
        rawSession: payload,
      }
      return { success: true, headers: buildHeaders(session), session }
    }
  }

  const fallback = devFallback()
  if (fallback) return fallback

  return unauthorizedResponse(workosCookie || jwtCookie ? 'SESSION_EXPIRED' : 'UNAUTHORIZED')
}

export async function resolveCompanyId(): Promise<string | null> {
  const auth = await getSessionAuth()
  return auth.success ? auth.session.companyId : null
}
