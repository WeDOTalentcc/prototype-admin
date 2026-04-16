import { NextRequest } from 'next/server'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

function resolveAuthHeader(request: NextRequest): string | null {
  const authHeader = request.headers.get('Authorization')
  if (authHeader) return authHeader

  const tokenCookie = request.cookies.get('lia_access_token')
  if (tokenCookie && tokenCookie.value !== '_sso_session_') {
    return `Bearer ${tokenCookie.value}`
  }

  const workosSession = request.cookies.get('workos_session')
  if (workosSession?.value) {
    const sessionData = verifyAndDecodeSession(workosSession.value)
    if (sessionData?.accessToken) {
      return `Bearer ${sessionData.accessToken}`
    }
  }

  return null
}

// Task #293: em não-prod, quando nenhum Bearer está disponível (ex.: usuário
// sem cookie válido em onboarding), permitimos que o proxy injete
// `X-Dev-Api-Key` a partir de um secret server-side. O backend valida essa
// chave em `AuthEnforcementMiddleware._check_dev_api_key` APENAS quando
// `LIA_DEV_MODE=true`. Em produção, `LIA_DEV_MODE` é false e a chave é
// ignorada — logo este header nunca gera bypass em prod.
function getDevFallbackHeaders(): Record<string, string> {
  const isDevMode =
    process.env.LIA_DEV_MODE === 'true' ||
    (process.env.NODE_ENV !== 'production' &&
      process.env.APP_ENV !== 'production')
  const devKey = process.env.LIA_DEV_API_KEY
  if (isDevMode && devKey) {
    return { 'X-Dev-Api-Key': devKey }
  }
  return {}
}

export function getAuthHeaders(request: NextRequest, required = false): HeadersInit {
  const authHeader = resolveAuthHeader(request)

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    'Content-Type': 'application/json',
    ...(authHeader ? { 'Authorization': authHeader } : getDevFallbackHeaders()),
  }
}

export function getAuthHeadersForForm(request: NextRequest, required = false): HeadersInit {
  const authHeader = resolveAuthHeader(request)

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    ...(authHeader ? { 'Authorization': authHeader } : getDevFallbackHeaders()),
  }
}
