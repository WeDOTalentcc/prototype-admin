export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const DEFAULT_COMPANY_ID = 'demo_company'

const _bodySchema = z.record(z.string(), z.unknown())

export async function PATCH(request: NextRequest) {
  try {
    const companyId = DEFAULT_COMPANY_ID
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/block`

    const response = await fetch(backendUrl, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar bloco', details: errorData },
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
