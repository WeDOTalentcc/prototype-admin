export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())

    const backendUrl = `${BACKEND_URL}/api/v1/orchestrator/jobs-management`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar chat de gestão de vagas', details: errorData },
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

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/v1/orchestrator/jobs-management/intents`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar intents do jobs management' },
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
