import { NextRequest, NextResponse } from 'next/server'
import { validateBody, validateParams } from '@/lib/api/validate'
import { candidateStageSchema } from '@/lib/schemas'
import { idSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const rawParams = await params
    const paramsResult = validateParams(rawParams, idSchema)
    if (!paramsResult.success) return paramsResult.response

    const bodyResult = await validateBody(request, candidateStageSchema)
    if (!bodyResult.success) return bodyResult.response

    const { id } = paramsResult.data
    const { stage, sub_status, job_vacancy_id } = bodyResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/candidates/${id}/stage`

    const response = await fetch(backendUrl, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage, sub_status, job_vacancy_id }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar etapa do candidato', details: errorData },
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
