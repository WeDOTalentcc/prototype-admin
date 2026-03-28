import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { domain: string } }
) {
  try {
    const { searchParams } = new URL(request.url)
    const company_id = searchParams.get('company_id')
    const days = searchParams.get('days') || '30'
    const domain = params.domain

    if (!company_id) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    const backendUrl = `${BACKEND_URL}/api/v1/agent-monitoring/domains/${domain}/metrics?company_id=${company_id}&days=${days}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: `Erro ao buscar métricas do domínio ${domain}`, details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
