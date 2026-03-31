export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const backendUrl = `${BACKEND_URL}/api/v1/short-lists${queryString ? `?${queryString}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar short lists', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const body = _bodySchema.parse(await request.json())
    const backendUrl = `${BACKEND_URL}/api/v1/short-lists${queryString ? `?${queryString}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar short list', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json(), { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
