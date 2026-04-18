/**
 * GET /api/backend-proxy/jobs-lifecycle-overview
 *
 * Proxy to /api/v1/job-vacancies/lifecycle-overview — companion to
 * /api/backend-proxy/pipeline-overview that powers the "Vagas" half of
 * the Visão do Pipeline toggle. Returns vacancies grouped by 8 lifecycle
 * stages (ATS Importada → Encerrada).
 */
export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const authHeaders = getAuthHeaders(request)
    const url = new URL(request.url)
    const perStage = url.searchParams.get("vacancies_per_stage") || "50"

    const res = await fetch(
      `${BACKEND_URL}/api/v1/job-vacancies/lifecycle-overview?vacancies_per_stage=${encodeURIComponent(perStage)}`,
      { headers: authHeaders }
    )

    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to fetch jobs lifecycle overview", status: res.status },
        { status: res.status }
      )
    }

    const raw = await res.json()
    const data = raw && "ok" in raw && raw.data ? raw.data : raw

    return NextResponse.json({
      stages: data.stages || [],
      total_vacancies: data.total_vacancies ?? 0,
    })
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error", details: String(error) },
      { status: 500 }
    )
  }
}
