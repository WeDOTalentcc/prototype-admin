export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  method_id: z.string().min(1, 'method_id is required'),
})

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ method_id: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { method_id } = await params
    const paramValidation = validateParams({ method_id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const backendUrl = `${BACKEND_URL}/api/v1/billing/my-payment-methods/${method_id}`

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao remover método de pagamento', details: errorData },
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
