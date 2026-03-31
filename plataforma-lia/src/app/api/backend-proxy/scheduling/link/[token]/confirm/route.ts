export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// POST /api/backend-proxy/scheduling/link/[token]/confirm
// Proxies to: POST /api/v1/scheduling/link/{token}/confirm
// PUBLIC — no auth required (candidate-facing action)
// Body: { start: string, end: string }
// Returns: { success, message, candidate_name, job_title, selected_slot }
const _bodySchema = z.record(z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: { token: string } }
) {
  try {
    const { token } = params
    const body = _bodySchema.parse(await request.json())

    if (!token) {
      return NextResponse.json({ error: 'Token inválido' }, { status: 400 })
    }

    if (!body.start || !body.end) {
      return NextResponse.json(
        { error: 'Os campos start e end são obrigatórios' },
        { status: 422 }
      )
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/scheduling/link/${token}/confirm`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )

    if (response.status === 404) {
      return NextResponse.json(
        { error: 'Link de agendamento não encontrado' },
        { status: 404 }
      )
    }

    if (response.status === 410) {
      return NextResponse.json(
        { error: 'Este link já foi utilizado ou expirou' },
        { status: 410 }
      )
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao confirmar agendamento', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao confirmar agendamento' },
      { status: 500 }
    )
  }
}
