export const dynamic = 'force-dynamic'
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const bodySchema = z.object({
  message: z.string().min(1).max(2000),
  token: z.string().min(1),
  vacancy_id: z.string().uuid().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const rawBody = await request.json()
    const parsed = bodySchema.safeParse(rawBody)
    if (!parsed.success) {
      return NextResponse.json({ error: 'invalid_request' }, { status: 400 })
    }

    const { message, token, vacancy_id } = parsed.data

    const response = await fetch(`${BACKEND_URL}/api/v1/candidate/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message, vacancy_id }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        { error: (data as Record<string, unknown>).detail as string || 'erro_backend' },
        { status: response.status }
      )
    }

    const { thought: _t, ...safe } = data as Record<string, unknown>
    return NextResponse.json(safe)
  } catch {
    return NextResponse.json({ error: 'internal_error' }, { status: 500 })
  }
}
