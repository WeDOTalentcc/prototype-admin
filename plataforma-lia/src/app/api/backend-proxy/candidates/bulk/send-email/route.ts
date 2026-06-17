export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { bulkSendEmailSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, bulkSendEmailSchema)
    if (!bodyResult.success) return bodyResult.response

    const { candidate_ids, template_id, custom_variables, custom_data } = bodyResult.data

    const requestBody = {
      candidate_ids,
      template_id,
      custom_variables: custom_variables || custom_data,
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/send-email`, {
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
        { error: 'Erro ao enviar emails', details: errorData },
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
