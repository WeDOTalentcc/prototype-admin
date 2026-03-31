export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/scheduling/link/[token]
// Proxies to: GET /api/v1/scheduling/link/{token}
// PUBLIC — no auth required (candidate-facing page)
// Returns available slots for the candidate to choose from.
export async function GET(
  _request: NextRequest,
  { params }: { params: { token: string } }
) {
  try {
    const { token } = params

    if (!token) {
      return NextResponse.json({ error: 'Token inválido' }, { status: 400 })
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/scheduling/link/${token}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
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
      return NextResponse.json(
        { error: 'Erro ao carregar link de agendamento' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao carregar link de agendamento' },
      { status: 500 }
    )
  }
}
