export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const routeParamsSchema = z.object({
  invoice_id: z.string().min(1, 'invoice_id is required'),
})

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'admin_company',
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ invoice_id: string }> }
) {
  try {
    const { invoice_id } = await params
    const paramValidation = validateParams({ invoice_id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const backendUrl = `${BACKEND_URL}/api/v1/billing/my-invoices/${invoice_id}/pay`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(),
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
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
