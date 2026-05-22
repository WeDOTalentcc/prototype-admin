export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request, true)
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()

    if (searchParams.get('search')) params.set('search', searchParams.get('search')!)
    if (searchParams.get('status')) params.set('status', searchParams.get('status')!)
    if (searchParams.get('plan')) params.set('plan', searchParams.get('plan')!)
    if (searchParams.get('limit')) params.set('limit', searchParams.get('limit')!)
    if (searchParams.get('offset')) params.set('offset', searchParams.get('offset')!)

    const backendUrl = `${BACKEND_URL}/api/v1/clients${params.toString() ? `?${params.toString()}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar clientes', details: errorData },
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

export async function POST(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request, true)
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const backendUrl = `${BACKEND_URL}/api/v1/clients`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar cliente', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: 201 })
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
