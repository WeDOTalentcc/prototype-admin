export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

/**
 * Public consent lookup proxy — Phase 4 LGPD Portal (2026-06-11)
 * Maps: GET /api/backend-proxy/public/consents?cpf=...&email=...
 *   to: GET /api/v1/public/consents?cpf=...&email=...
 *
 * No auth forwarded — this is a public endpoint for the /privacidade portal.
 * Rate-limiting: handled at infrastructure level.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    const backendUrl = queryString
      ? `${BACKEND_URL}/api/v1/public/consents?${queryString}`
      : `${BACKEND_URL}/api/v1/public/consents`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Erro ao consultar consentimentos' }))
      return NextResponse.json(
        { error: errorData.detail || 'Falha ao consultar consentimentos' },
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
