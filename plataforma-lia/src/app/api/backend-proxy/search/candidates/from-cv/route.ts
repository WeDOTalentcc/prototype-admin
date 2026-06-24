export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'
import { getAuthHeadersForForm } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
import { MAX_FILE_SIZE } from '@/constants/upload'

const fromCvQuerySchema = z.object({
  limit: z.string().regex(/^\d+$/).optional().default('20'),
  search_pearch: z.enum(['true', 'false']).optional().default('true'),
  pearch_type: z.enum(['fast', 'deep']).optional().default('fast'),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, fromCvQuerySchema)
    if (!queryValidation.success) return queryValidation.response

    const formData = await request.formData()
    const file = formData.get('file') as File | null

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { error: 'Arquivo CV é obrigatório' },
        { status: 400 }
      )
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: 'File too large (max 10MB)' },
        { status: 413 }
      )
    }

    const { limit, search_pearch, pearch_type } = queryValidation.data

    const backendFormData = new FormData()
    backendFormData.append('file', file)

    const backendUrl = `${BACKEND_URL}/api/v1/search/from-cv?limit=${limit}&search_pearch=${search_pearch}&pearch_type=${pearch_type}`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeadersForForm(request),
      body: backendFormData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar candidatos pelo CV', details: errorData },
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
