import { NextRequest } from 'next/server'

function resolveAuthHeader(request: NextRequest): string | null {
  const authHeader = request.headers.get('Authorization')
  if (authHeader) return authHeader

  const tokenCookie = request.cookies.get('lia_access_token')
  if (tokenCookie && tokenCookie.value !== '_sso_session_') {
    return `Bearer ${tokenCookie.value}`
  }

  return null
}

export function getAuthHeaders(request: NextRequest, required = false): HeadersInit {
  const authHeader = resolveAuthHeader(request)

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    'Content-Type': 'application/json',
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}

export function getAuthHeadersForForm(request: NextRequest, required = false): HeadersInit {
  const authHeader = resolveAuthHeader(request)

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}
