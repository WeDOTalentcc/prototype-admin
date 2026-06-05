import { NextRequest, NextResponse } from "next/server"
import { getAuthHeadersForForm } from "@/lib/api/auth-headers"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// Track B / Fase 3: este proxy estava AUSENTE — o upload do SmartImportZone
// batia em 404. Encaminha o multipart + a query (?preview=true) ao backend,
// que grava em PlannedHeadcount (Store B) via produtor canonical. NÃO chamar
// request.json() — preserva o boundary do FormData.
export async function POST(request: NextRequest) {
  try {
    const headers = getAuthHeadersForForm(request)
    const formData = await request.formData()
    const search = new URL(request.url).search // preserva ?preview=true
    const response = await fetch(
      `${BACKEND_URL}/api/v1/workforce/entries/import${search}`,
      { method: "POST", headers, body: formData },
    )
    const contentType = response.headers.get("content-type") || ""
    if (contentType.includes("application/json")) {
      const data = await response.json()
      return NextResponse.json(data, { status: response.status })
    }
    const text = await response.text()
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": contentType || "text/plain" },
    })
  } catch (error) {
    console.error("[workforce/entries/import] proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}
