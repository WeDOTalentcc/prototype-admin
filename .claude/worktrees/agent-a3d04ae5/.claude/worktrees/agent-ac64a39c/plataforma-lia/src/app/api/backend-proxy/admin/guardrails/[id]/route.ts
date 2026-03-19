import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET    /api/backend-proxy/admin/guardrails/[id]        → GET    /api/v1/guardrails/{id}
// PUT    /api/backend-proxy/admin/guardrails/[id]        → PUT    /api/v1/guardrails/{id}
// PATCH  /api/backend-proxy/admin/guardrails/[id]        → PATCH  /api/v1/guardrails/{id}/toggle
// DELETE /api/backend-proxy/admin/guardrails/[id]        → DELETE /api/v1/guardrails/{id}

type Params = { params: { id: string } }

export async function GET(_request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails/${params.id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json({ error: 'Guardrail não encontrado' }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno ao buscar guardrail' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest, { params }: Params) {
  try {
    const body = await request.json()
    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails/${params.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json({ error: 'Erro ao atualizar guardrail' }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno ao atualizar guardrail' }, { status: 500 })
  }
}

export async function PATCH(_request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails/${params.id}/toggle`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json({ error: 'Erro ao alternar guardrail' }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno ao alternar guardrail' }, { status: 500 })
  }
}

export async function DELETE(_request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/guardrails/${params.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.status === 404) {
      return NextResponse.json({ error: 'Guardrail não encontrado' }, { status: 404 })
    }

    if (!response.ok) {
      return NextResponse.json({ error: 'Erro ao deletar guardrail' }, { status: response.status })
    }

    return new NextResponse(null, { status: 204 })
  } catch {
    return NextResponse.json({ error: 'Erro interno ao deletar guardrail' }, { status: 500 })
  }
}
