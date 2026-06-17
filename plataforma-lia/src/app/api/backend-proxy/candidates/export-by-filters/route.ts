export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const response = await fetch(
      ,
      {
        method: "POST",
        headers: { ...getAuthHeaders(request), "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    )
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "Erro ao exportar candidatos", details: errorData },
        { status: response.status }
      )
    }
    const blob = await response.blob()
    const contentDisposition =
      response.headers.get("Content-Disposition") ||
      "attachment; filename=candidatos.csv"
    const headers = new Headers()
    headers.set("Content-Type", "text/csv; charset=utf-8")
    headers.set("Content-Disposition", contentDisposition)
    headers.set("X-Export-Total", response.headers.get("X-Export-Total") || "0")
    headers.set("X-Export-Filtered", "true")
    return new NextResponse(blob, { headers })
  } catch {
    return NextResponse.json(
      { error: "Erro ao conectar com o backend" },
      { status: 500 }
    )
  }
}
