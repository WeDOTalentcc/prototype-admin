export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

/**
 * Consent revoke proxy — Phase 4 LGPD Portal (2026-06-11)
 * Maps: PUT /api/backend-proxy/observability/consents/{consentId}/revoke
 *   to: PUT /api/v1/observability/consents/{consentId}/revoke
 *
 * Param name reuses [candidateId] slug to avoid Next.js App Router slug conflict
 * with sibling [candidateId]/route.ts at the same level.
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ candidateId: string }> }
) {
  try {
    const { candidateId: consentId } = await params

    if (!consentId) {
      return NextResponse.json({ error: 'consentId obrigatório' }, { status: 400 })
    }

    const backendUrl = `${BACKEND_URL}/api/v1/observability/consents/${consentId}/revoke`

    // Body may be empty or contain revocation reason
    let body: object = {}
    try {
      body = await request.json()
    } catch {
      // empty body is fine
    }

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(request),
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Erro ao revogar consentimento' }))
      return NextResponse.json(
        { error: errorData.detail || 'Falha ao revogar consentimento' },
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
