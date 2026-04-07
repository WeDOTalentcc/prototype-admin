export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { bulkStartScreeningSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, bulkStartScreeningSchema)
    if (!bodyResult.success) return bodyResult.response

    const { candidate_ids, job_vacancy_id, job_id, screening_type, use_pearch, use_gemini, user_instructions, override_saturation } = bodyResult.data

    const requestBody = {
      candidate_ids,
      job_vacancy_id: job_vacancy_id || job_id,
      screening_type: screening_type || 'text',
      use_pearch: use_pearch !== undefined ? use_pearch : true,
      use_gemini: use_gemini !== undefined ? use_gemini : true,
      user_instructions,
      override_saturation: override_saturation || false,
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/start-screening`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('Authorization') ? { 'Authorization': request.headers.get('Authorization')! } : {}),
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao iniciar triagem', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
