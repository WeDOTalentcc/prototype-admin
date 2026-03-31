export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// POST /api/backend-proxy/admin/guardrails/seed-defaults → POST /api/v1/guardrails/seed-defaults
export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')
    const url = `${BACKEND_URL}/api/v1/guardrails/seed-defaults${companyId ? `?company_id=${companyId}` : ''}`

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao executar seed de guardrails' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno ao executar seed' }, { status: 500 })
  }
}
