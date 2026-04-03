export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET  /api/backend-proxy/admin/guardrails  → GET  /api/v1/guardrails
// POST /api/backend-proxy/admin/guardrails  → POST /api/v1/guardrails
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const url = `${BACKEND_URL}/api/v1/guardrails${queryString ? `?${queryString}` : ''}`

    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao listar guardrails' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno ao listar guardrails' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    return NextResponse.json({ error: 'Erro interno ao criar guardrail' }, { status: 500 })
  }
}
