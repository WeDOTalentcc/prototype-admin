export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})


export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/integrations`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar integrações', details: errorData },
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/integrations`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar integração', details: errorData },
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
