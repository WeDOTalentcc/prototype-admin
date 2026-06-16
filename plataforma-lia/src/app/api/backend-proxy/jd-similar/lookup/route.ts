export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * GET /api/backend-proxy/jd-similar/lookup
 *
 * Sprint B Phase 1 — Busca JDs similares no historico da empresa.
 * Proxy para FastAPI: GET /api/v1/jd-similar/lookup
 *
 * Fail-open: erros retornam { items: [] } com status 200 pra nao quebrar wizard.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get("company_id") || ""
  const title = searchParams.get("title") || ""
  const department = searchParams.get("department") || ""
  const toggleEnabled = searchParams.get("toggle_enabled") ?? "true"
  const minSimilarity = searchParams.get("min_similarity") || "0.7"
  const limit = searchParams.get("limit") || "3"

  if (!companyId || !title) {
    return NextResponse.json(
      { items: [], total_company_jds: 0, threshold_met: false, error: "company_id and title required" },
      { status: 400 },
    )
  }

  try {
    const url = new URL(`${BACKEND_URL}/api/v1/jd-similar/lookup`)
    url.searchParams.set("company_id", companyId)
    url.searchParams.set("title", title)
    if (department) url.searchParams.set("department", department)
    url.searchParams.set("toggle_enabled", toggleEnabled)
    url.searchParams.set("min_similarity", minSimilarity)
    url.searchParams.set("limit", limit)

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      // Fail-open: nao quebrar wizard se backend reclama
      return NextResponse.json(
        { items: [], total_company_jds: 0, threshold_met: false },
        { status: 200 },
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: 200 })
  } catch (err) {
    return NextResponse.json(
      { items: [], total_company_jds: 0, threshold_met: false },
      { status: 200 },
    )
  }
}
