import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET  /api/backend-proxy/guardrails         → GET  /api/v1/guardrails
// POST /api/backend-proxy/guardrails         → POST /api/v1/guardrails

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const query = searchParams.toString()

    const response = await fetch(
      `${BACKEND_URL}/api/v1/guardrails${query ? `?${query}` : ''}`,
      { method: 'GET', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao listar guardrails' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails`, {
      method: 'POST',
      headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao criar guardrail' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json(), { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
