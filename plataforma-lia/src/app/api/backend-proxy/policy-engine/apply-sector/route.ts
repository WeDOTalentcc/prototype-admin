export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

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
      headers: { "Content-Type": "application/json" },
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
