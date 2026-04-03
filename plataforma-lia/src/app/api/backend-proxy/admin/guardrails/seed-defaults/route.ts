export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const seedQuerySchema = z.object({
  company_id: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, seedQuerySchema)
    if (!queryValidation.success) return queryValidation.response
    const { company_id } = queryValidation.data

    const url = `${BACKEND_URL}/api/v1/guardrails/seed-defaults${company_id ? `?company_id=${company_id}` : ''}`

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
