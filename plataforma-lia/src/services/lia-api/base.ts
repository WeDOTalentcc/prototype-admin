import { checkPaymentRequired } from '@/lib/api/handle-payment-required'

export const BACKEND_URL = '/api/backend-proxy'

export { checkPaymentRequired }

export function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
  }
}

export function getAuthHeadersForFormData(): HeadersInit {
  return {}
}
