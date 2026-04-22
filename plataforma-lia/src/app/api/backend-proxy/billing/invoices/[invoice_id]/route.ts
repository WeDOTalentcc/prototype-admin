export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ invoice_id: string }> }
) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { invoice_id } = await params
    const backendUrl = `${BACKEND_URL}/api/v1/billing/my-invoices/${invoice_id}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar fatura', details: errorData },
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
