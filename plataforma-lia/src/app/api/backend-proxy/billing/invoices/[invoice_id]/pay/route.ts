export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'

const routeParamsSchema = z.object({
  invoice_id: z.string().min(1, 'invoice_id is required'),
})

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ invoice_id: string }> }
) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { invoice_id } = await params
    const paramValidation = validateParams({ invoice_id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const backendUrl = `${BACKEND_URL}/api/v1/billing/my-invoices/${invoice_id}/pay`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao marcar fatura como paga', details: errorData },
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
