export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'

export async function GET(request: NextRequest) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const limit = searchParams.get('limit') || '50'

    let backendUrl = `${BACKEND_URL}/api/v1/billing/my-invoices?limit=${limit}`
    if (status) {
      backendUrl += `&status=${status}`
    }

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar faturas', details: errorData },
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
