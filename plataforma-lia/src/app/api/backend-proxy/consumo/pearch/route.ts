export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

/**
 * GET /api/backend-proxy/consumo/pearch
 *
 * Proxies to /api/v1/consumption/pearch — dedicated Pearch consumption endpoint.
 * Reads external_api_consumption table (provider='pearch'), NOT ai_consumption/LLM tokens.
 * company_id resolved server-side via JWT (no payload supply — REGRA 2 Pydantic canonical).
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const days = searchParams.get('days') ?? '30'

    const backendPath = `/api/v1/consumption/pearch?days=${days}`

    const response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar dados de consumo Pearch', details: errorData },
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
