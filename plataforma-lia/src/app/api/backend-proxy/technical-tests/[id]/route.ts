export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'
import { z } from 'zod'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const backendUrl = `${BACKEND_URL}/api/v1/technical-tests/${id}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar teste técnico', details: errorData },
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/technical-tests/${id}`

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: auth.headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar teste técnico', details: errorData },
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

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const backendUrl = `${BACKEND_URL}/api/v1/technical-tests/${id}`

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: auth.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao excluir teste técnico', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
