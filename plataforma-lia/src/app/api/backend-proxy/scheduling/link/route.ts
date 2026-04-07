export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// POST /api/backend-proxy/scheduling/link
// Proxies to: POST /api/v1/scheduling/link
// Creates a self-scheduling link and sends it to the candidate via WhatsApp or email.
// Body: CreateSchedulingLinkRequest (see self_scheduling_public.py)
// Returns: { success, link_id, token, scheduling_url, expires_at, slots_offered, send_result }
const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

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
