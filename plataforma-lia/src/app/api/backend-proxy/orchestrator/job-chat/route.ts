import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())

    const backendUrl = `${BACKEND_URL}/api/v1/orchestrator/job-chat`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      if (response.status === 403 || response.status === 401) {
        return NextResponse.json(
          { success: false, content: 'Sessão expirada ou não autenticada. Tente recarregar a página.', error: 'auth_error' },
          { status: 200 }
        )
      }
      if (process.env.NODE_ENV === 'development') {
      }
      return NextResponse.json(
        { error: 'Erro ao processar chat da vaga', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (process.env.NODE_ENV === 'development') {
    }
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/v1/orchestrator/job-chat/intents`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      if (response.status === 403 || response.status === 401) {
        return NextResponse.json({ intents: [] }, { status: 200 })
      }
      if (process.env.NODE_ENV === 'development') {
      }
      return NextResponse.json(
        { error: 'Erro ao buscar intents do job chat' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (process.env.NODE_ENV === 'development') {
    }
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
