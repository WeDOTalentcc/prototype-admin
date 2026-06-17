// P1-W1-19: migrado — auth headers via getAuthHeaders canonical (não Authorization raw)
// NOTA: mantém lógica de streaming CSV (não pode usar createProxyHandlers que assume JSON)
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const params = searchParams.toString()

  try {
    const response = await fetch(
      BACKEND_URL + "/api/v1/fairness/reports/export" + (params ? "?" + params : ""),
      {
        // P1-W1-19: getAuthHeaders canonical em vez de Authorization raw
        headers: getAuthHeaders(req),
        signal: AbortSignal.timeout(30000),
      }
    )
    const body = await response.text()
    return new NextResponse(body, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "text/csv",
        "Content-Disposition":
          response.headers.get("Content-Disposition") ||
          "attachment; filename=fairness_report.csv",
      },
    })
  } catch {
    return NextResponse.json({ error: "export_unavailable" }, { status: 503 })
  }
}
