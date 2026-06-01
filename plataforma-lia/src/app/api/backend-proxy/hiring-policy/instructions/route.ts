export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// P3b: free-text policy instructions (prompt hints). { instructions: {concept: text} }
const _bodySchema = z.object({
  instructions: z.record(z.string(), z.string()),
})

export async function PATCH(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/instructions`
    const response = await fetch(backendUrl, {
      method: 'PATCH',
      headers: getAuthHeaders(request),
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar instruções', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    const unwrapped = data && typeof data === 'object' && data.ok === true && 'data' in data
      ? data.data
      : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
