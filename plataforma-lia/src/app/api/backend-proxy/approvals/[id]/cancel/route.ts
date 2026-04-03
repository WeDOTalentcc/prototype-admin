export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const { searchParams } = new URL(request.url)
    const cancelledBy = searchParams.get('cancelled_by')
    
    if (!cancelledBy) {
      return NextResponse.json(
        { error: 'cancelled_by é obrigatório' },
        { status: 400 }
      )
    }
    
    const backendUrl = `${BACKEND_URL}/api/v1/approvals/${id}/cancel?cancelled_by=${encodeURIComponent(cancelledBy)}`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao cancelar solicitação', details: errorData },
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
