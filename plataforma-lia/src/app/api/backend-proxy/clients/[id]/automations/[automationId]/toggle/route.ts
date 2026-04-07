export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
  automationId: z.string().min(1, 'automationId is required'),
})

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'admin_company',
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; automationId: string }> }
) {
  try {
    const { id, automationId } = await params
    const paramValidation = validateParams({ id, automationId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    
    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/automations/${automationId}/toggle`
    
    const response = await fetch(backendUrl, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao alternar status da automação', details: errorData },
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
