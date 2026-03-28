import { NextRequest } from 'next/server'

/**
 * Returns standard JSON headers including Authorization if present.
 *
 * @param request - The incoming Next.js request.
 * @param required - If true, throws an error when Authorization header is missing.
 */
export function getAuthHeaders(request: NextRequest, required = false): HeadersInit {
  const authHeader = request.headers.get('Authorization')

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    'Content-Type': 'application/json',
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}

/**
 * Returns headers for multipart/form-data requests (no Content-Type so browser can set boundary).
 *
 * @param request - The incoming Next.js request.
 * @param required - If true, throws an error when Authorization header is missing.
 */
export function getAuthHeadersForForm(request: NextRequest, required = false): HeadersInit {
  const authHeader = request.headers.get('Authorization')

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}

