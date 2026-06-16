export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const refineQuerySchema = z.object({
  thread_id: z.string().min(1, 'thread_id is required'),
  additional_query: z.string().min(1, 'additional_query is required'),
  limit: z.string().optional(),
  // Task #1219 — load-more do modo "Híbrida com email": precisa repassar
  // require_emails (e correlatos) ao backend, senão o incremento volta a
  // incluir candidatos sem email.
  require_emails: z.string().optional(),
  require_phone_numbers: z.string().optional(),
  docid_blacklist: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, refineQuerySchema)
    if (!queryValidation.success) return queryValidation.response
    const {
      thread_id,
      additional_query,
      limit,
      require_emails,
      require_phone_numbers,
      docid_blacklist,
    } = queryValidation.data

    let backendUrl = `${BACKEND_URL}/api/v1/search/candidates/refine?thread_id=${encodeURIComponent(thread_id)}&additional_query=${encodeURIComponent(additional_query)}`
    if (limit) {
      backendUrl += `&limit=${limit}`
    }
    if (require_emails) {
      backendUrl += `&require_emails=${encodeURIComponent(require_emails)}`
    }
    if (require_phone_numbers) {
      backendUrl += `&require_phone_numbers=${encodeURIComponent(require_phone_numbers)}`
    }
    if (docid_blacklist) {
      backendUrl += `&docid_blacklist=${encodeURIComponent(docid_blacklist)}`
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao refinar busca', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    const unwrapped = (data && typeof data === 'object' && 'ok' in data && 'data' in data) ? data.data : data
    return NextResponse.json(unwrapped)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
