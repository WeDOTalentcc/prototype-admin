export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const response = await fetch(
      `${BACKEND_URL}/api/v1/recruitment-stages/sync-canonical-sub-statuses`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { error: 'Erro ao sincronizar sub-statuses canônicos', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
