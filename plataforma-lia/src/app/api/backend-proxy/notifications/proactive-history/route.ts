export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const limit = url.searchParams.get("limit") ?? "50"
    const backendUrl = `${BACKEND_URL}/api/v1/notifications/proactive/history?limit=${limit}`
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: getAuthHeaders(request),
      signal: AbortSignal.timeout(8000),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "Erro ao buscar histórico de alertas", details: err },
        { status: response.status }
      )
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: "Erro ao conectar com o backend" }, { status: 500 })
  }
}
