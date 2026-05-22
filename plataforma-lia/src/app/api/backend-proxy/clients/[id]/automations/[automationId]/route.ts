export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
  automationId: z.string().min(1, 'automationId is required'),
})


const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; automationId: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { id, automationId } = await params
    const paramValidation = validateParams({ id, automationId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/automations/${automationId}`

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar automação', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (error instanceof Error && error.message.includes('Authentication required')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; automationId: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { id, automationId } = await params
    const paramValidation = validateParams({ id, automationId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/automations/${automationId}`

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao remover automação', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (error instanceof Error && error.message.includes('Authentication required')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
