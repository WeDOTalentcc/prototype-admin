// P1-W1-19: migrado — AbortSignal.timeout adicionado, BACKEND_URL via env canônico
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const backendParams = new URLSearchParams()

    const allowed = ["company_id", "days"]
    for (const key of allowed) {
      const val = searchParams.get(key)
      if (val !== null) backendParams.set(key, val)
    }

    const url = BACKEND_URL + "/api/v1/fairness/reports/summary?" + backendParams.toString()
    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(request),
      signal: AbortSignal.timeout(30000),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: "Erro ao consultar resumo de fairness" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Erro interno ao consultar fairness summary" },
      { status: 500 }
    )
  }
}
