export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { connection_id, sync_type, filters } = body

    if (!connection_id) {
      return NextResponse.json(
        { success: false, detail: 'connection_id é obrigatório' },
        { status: 400 }
      )
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/ats/connections/${connection_id}/sync`,
      {
        method: 'POST',
        headers: {
          ...getAuthHeaders(request),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sync_type: sync_type || 'full', filters }),
      }
    )

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch {
    return NextResponse.json(
      { success: false, detail: 'Erro ao sincronizar' },
      { status: 500 }
    )
  }
}
