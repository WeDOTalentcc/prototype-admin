export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const backendParams = new URLSearchParams()

    const allowed = ["company_id", "days", "category", "blocked_only", "limit", "offset"]
    for (const key of allowed) {
      const val = searchParams.get(key)
      if (val !== null) backendParams.set(key, val)
    }

    const url = BACKEND_URL + "/api/v1/fairness/audit/logs?" + backendParams.toString()
    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: "Erro ao consultar audit logs de fairness" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Erro interno ao consultar fairness audit logs" },
      { status: 500 }
    )
  }
}
