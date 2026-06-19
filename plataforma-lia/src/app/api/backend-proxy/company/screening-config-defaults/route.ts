export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { resolveCompanyId } from "@/lib/api/resolve-company-id"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: "Company ID não disponível" }, { status: 401 })
    }
    const res = await fetch(
      `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/screening-config-defaults`,
      { method: "GET", headers: getAuthHeaders(request), signal: AbortSignal.timeout(8000) },
    )
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
  } catch (e) {
    return NextResponse.json({ error: "Erro ao buscar configurações de triagem" }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: "Company ID não disponível" }, { status: 401 })
    }
    const body = await request.json().catch(() => ({}))
    const res = await fetch(
      `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/screening-config-defaults`,
      {
        method: "PUT",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(8000),
      },
    )
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
  } catch (e) {
    return NextResponse.json({ error: "Erro ao salvar configurações de triagem" }, { status: 500 })
  }
}
