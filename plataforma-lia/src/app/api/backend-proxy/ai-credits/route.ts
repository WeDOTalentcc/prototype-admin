import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'admin_company',
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const endpoint = searchParams.get('endpoint') || 'balance'
    const days = searchParams.get('days') || '30'

    let backendPath: string

    switch (endpoint) {
      case 'balance':
        backendPath = '/api/v1/ai-consumption/balance'
        break
      case 'summary':
        backendPath = '/api/v1/ai-consumption/summary'
        break
      case 'by-day':
        backendPath = `/api/v1/ai-consumption/by-day?days=${days}`
        break
      case 'by-agent':
        backendPath = '/api/v1/ai-consumption/by-agent'
        break
      default:
        return NextResponse.json({ error: 'Endpoint inválido' }, { status: 400 })
    }

    const response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar dados de consumo de IA', details: errorData },
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
