export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// SECURITY (auditoria 2026-05-22): companyId vinha apenas da query string sem
// JWT forwarding — qualquer pessoa que descobrisse o UUID podia aplicar setor
// compliance template a qualquer company (cross-tenant). Fix: forward JWT via
// getAuthHeaders canonical. Backend deve validar companyId da path contra JWT
// (canonical require_company_id). Defense-in-depth ate backend team migrar a
// rota pra derivar companyId puramente do JWT.
const applySectorQuerySchema = z.object({
  companyId: z.string().min(1, 'companyId is required'),
  sector: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, applySectorQuerySchema)
    if (!queryValidation.success) return queryValidation.response
    const { companyId, sector } = queryValidation.data

    const url = new URL(
      `${BACKEND_URL}/api/v1/policy-engine/apply-sector/${companyId}`,
    )
    if (sector) url.searchParams.set("sector", sector)

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: errorText || "Falha ao aplicar setor" },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Erro de conexão com o backend" },
      { status: 500 },
    )
  }
}
