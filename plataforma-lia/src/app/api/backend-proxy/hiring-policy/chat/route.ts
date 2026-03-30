import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const DEFAULT_COMPANY_ID = 'demo_company'

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const companyId = DEFAULT_COMPANY_ID
    const body = _bodySchema.parse(await request.json())
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/chat`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...body,
        company_id: companyId,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar mensagem', details: errorData },
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
