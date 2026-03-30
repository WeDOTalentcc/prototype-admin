import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { bulkDeleteSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const SERVICE_API_TOKEN = process.env.SERVICE_API_TOKEN || 'dev-service-token'

export async function DELETE(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, bulkDeleteSchema)
    if (!bodyResult.success) return bodyResult.response

    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SERVICE_API_TOKEN}`,
      },
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao excluir candidatos', details: errorData },
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
