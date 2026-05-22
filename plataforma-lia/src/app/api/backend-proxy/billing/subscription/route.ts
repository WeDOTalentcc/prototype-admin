export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request, true)
    const backendUrl = `${BACKEND_URL}/api/v1/billing/subscription`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar assinatura', details: errorData },
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

export async function PUT(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request, true)
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/billing/subscription`

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar assinatura', details: errorData },
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
