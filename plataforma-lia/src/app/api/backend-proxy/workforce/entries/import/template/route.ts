import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

export const dynamic = "force-dynamic"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// Track B / Fase 3: proxy do template CSV (download) do import de headcount.
export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request)
    const response = await fetch(
      `${BACKEND_URL}/api/v1/workforce/entries/import/template`,
      { method: "GET", headers },
    )
    if (!response.ok) {
      const text = await response.text().catch(() => "")
      return new NextResponse(text || null, { status: response.status })
    }
    const buf = await response.arrayBuffer()
    return new NextResponse(buf, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") || "text/csv",
        "Content-Disposition":
          response.headers.get("content-disposition") ||
          "attachment; filename=workforce_planning_import_template.csv",
      },
    })
  } catch (error) {
    console.error("[workforce/entries/import/template] proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}
