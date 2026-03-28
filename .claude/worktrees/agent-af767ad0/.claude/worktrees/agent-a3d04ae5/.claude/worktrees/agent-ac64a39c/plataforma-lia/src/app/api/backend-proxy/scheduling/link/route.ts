import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// POST /api/backend-proxy/scheduling/link
// Proxies to: POST /api/v1/scheduling/link
// Creates a self-scheduling link and sends it to the candidate via WhatsApp or email.
// Body: CreateSchedulingLinkRequest (see self_scheduling_public.py)
// Returns: { success, link_id, token, scheduling_url, expires_at, slots_offered, send_result }
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/v1/scheduling/link`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(request),
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar link de agendamento', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao criar link de agendamento' },
      { status: 500 }
    )
  }
}
