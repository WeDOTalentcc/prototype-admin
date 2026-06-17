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

// Dev fallback header injection (task #293).
//
// Contrato cross-service:
//   - Front só injeta `X-Dev-Api-Key` quando `LIA_DEV_MODE === 'true'` E
//     `LIA_DEV_API_KEY` está presente. Ambas as variáveis são server-side
//     (Next route handlers), nunca expostas ao browser.
//   - Backend só aceita a chave quando `LIA_DEV_MODE === 'true'` no ambiente
//     do FastAPI. Em produção, `LIA_DEV_MODE` é false e o header é ignorado.
//
// Portanto: não há bypass em produção; o header é apenas um opt-in explícito
// coordenado pelos operadores via duas variáveis distintas nos dois serviços.
function getDevFallbackHeaders(): Record<string, string> {
  if (process.env.LIA_DEV_MODE !== 'true') return {}
  const devKey = process.env.LIA_DEV_API_KEY
  if (!devKey) return {}
  return { 'X-Dev-Api-Key': devKey }
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
