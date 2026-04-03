import { NextRequest } from 'next/server'

export function getAuthHeaders(request: NextRequest, required = false): HeadersInit {
  let authHeader = request.headers.get('Authorization')

  if (!authHeader) {
    const tokenCookie = request.cookies.get('lia_access_token')
    if (tokenCookie) {
      authHeader = `Bearer ${tokenCookie.value}`
    }
  }

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    'Content-Type': 'application/json',
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}

export function getAuthHeadersForForm(request: NextRequest, required = false): HeadersInit {
  let authHeader = request.headers.get('Authorization')

  if (!authHeader) {
    const tokenCookie = request.cookies.get('lia_access_token')
    if (tokenCookie) {
      authHeader = `Bearer ${tokenCookie.value}`
    }
  }

  if (required && !authHeader) {
    throw new Error('Authentication required: Authorization header missing')
  }

  return {
    ...(authHeader ? { 'Authorization': authHeader } : {}),
  }
}
