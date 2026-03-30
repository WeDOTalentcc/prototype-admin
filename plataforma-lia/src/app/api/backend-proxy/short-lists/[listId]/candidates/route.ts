import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: { listId: string } }
) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const body = _bodySchema.parse(await request.json())
    const backendUrl = `${BACKEND_URL}/api/v1/short-lists/${params.listId}/candidates${queryString ? `?${queryString}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao adicionar candidato', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json(), { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
