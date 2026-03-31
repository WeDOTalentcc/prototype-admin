export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

type Params = { params: { id: string } }

// GET   /api/backend-proxy/guardrails/[id]          → GET   /api/v1/guardrails/{id}
// PUT   /api/backend-proxy/guardrails/[id]          → PUT   /api/v1/guardrails/{id}
// PATCH /api/backend-proxy/guardrails/[id]/toggle   → handled in /[id]/toggle/route.ts

export async function GET(request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/guardrails/${params.id}`,
      { method: 'GET', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Guardrail não encontrado' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest, { params }: Params) {
  try {
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails/${params.id}`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao atualizar guardrail' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
