export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'
import { z } from 'zod'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    let body: Record<string, unknown> = {}
    const parseResult = _bodySchema.safeParse(await request.json().catch(() => ({})))
    body = parseResult.success ? parseResult.data : {}

    const backendUrl = `${BACKEND_URL}/api/v1/technical-tests/seed`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: auth.headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao popular testes técnicos', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
