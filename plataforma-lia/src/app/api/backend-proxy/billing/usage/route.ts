export const dynamic = "force-dynamic"
import { NextResponse } from 'next/server'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'

export async function GET() {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const backendUrl = `${BACKEND_URL}/api/v1/billing/usage`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar uso de recursos', details: errorData },
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
