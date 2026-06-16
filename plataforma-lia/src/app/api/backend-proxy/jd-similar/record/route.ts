export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * POST /api/backend-proxy/jd-similar/record
 *
 * Sprint B Phase 1 — Registra JD enriquecida no historico ao publicar vaga.
 * Proxy para FastAPI: POST /api/v1/jd-similar/record
 *
 * Body: { company_id, job_id, title, jd_enriched, seniority_level?, department? }
 *
 * Fail-soft: erros nao bloqueiam o publish. Frontend pode chamar fire-and-forget.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    if (!body.company_id || !body.job_id || !body.title || !body.jd_enriched) {
      return NextResponse.json(
        { ok: false, error: "company_id, job_id, title, jd_enriched required" },
        { status: 400 },
      )
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/jd-similar/record`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      // Fail-soft: log no backend, frontend continua
      return NextResponse.json(
        { ok: false, message: "backend unavailable" },
        { status: 200 },
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (err) {
    return NextResponse.json(
      { ok: false, message: "request failed" },
      { status: 200 },
    )
  }
}
