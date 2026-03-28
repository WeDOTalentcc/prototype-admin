import { checkPaymentRequired } from '@/lib/api/handle-payment-required'

export const BACKEND_URL = '/api/backend-proxy'

export { checkPaymentRequired }

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export function getAuthHeaders(): HeadersInit {
  const token = getAccessToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

export function getAuthHeadersForFormData(): HeadersInit {
  const token = getAccessToken()
  return {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}
