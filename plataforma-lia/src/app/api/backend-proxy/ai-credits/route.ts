export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// WT-2022 P0.SEG2: anti-pattern admin_company hardcoded removido.
// Agora propaga Authorization header (JWT) do request real - backend resolve
// company_id via tenant_guard.get_verified_company_id (canonical).
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
      case 'agent-trend':
        backendPath = `/api/v1/ai-consumption/agent-trend?days=${days}`
        break
      default:
        return NextResponse.json({ error: 'Endpoint inválido' }, { status: 400 })
    }

    const response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: 'GET',
      headers: getAuthHeaders(request),
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
