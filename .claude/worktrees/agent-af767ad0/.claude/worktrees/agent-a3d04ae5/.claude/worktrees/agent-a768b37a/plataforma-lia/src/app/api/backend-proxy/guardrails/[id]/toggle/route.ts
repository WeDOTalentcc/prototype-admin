import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

type Params = { params: { id: string } }

// PATCH /api/backend-proxy/guardrails/[id]/toggle → PATCH /api/v1/guardrails/{id}/toggle
export async function PATCH(request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/guardrails/${params.id}/toggle`,
      { method: 'PATCH', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao alternar status do guardrail' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
