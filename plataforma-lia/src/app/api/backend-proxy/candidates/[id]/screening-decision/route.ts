export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody, validateParams } from '@/lib/api/validate'
import { candidateDecisionSchema } from '@/lib/schemas'
import { idSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const rawParams = await params
    const paramsResult = validateParams(rawParams, idSchema)
    if (!paramsResult.success) return paramsResult.response

    const bodyResult = await validateBody(request, candidateDecisionSchema)
    if (!bodyResult.success) return bodyResult.response

    const { id } = paramsResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/candidates/${id}/screening-decision`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar decisão de triagem', details: errorData },
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
