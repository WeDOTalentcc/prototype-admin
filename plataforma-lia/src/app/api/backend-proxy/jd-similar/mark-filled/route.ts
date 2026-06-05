export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * POST /api/backend-proxy/jd-similar/mark-filled
 * Sprint B Phase 1 - manual outcome trigger (alternative to automatic hook).
 * Body: { company_id, job_id, time_to_fill_days, candidates_count }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    if (!body.company_id || !body.job_id) {
      return NextResponse.json(
        { ok: false, error: "company_id and job_id required" },
        { status: 400 },
      )
    }
    const res = await fetch(`${BACKEND_URL}/api/v1/jd-similar/mark-filled`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      return NextResponse.json({ ok: false, message: "backend rejected" }, { status: 200 })
    }
    return NextResponse.json(await res.json(), { status: 200 })
  } catch {
    return NextResponse.json({ ok: false, message: "request failed" }, { status: 200 })
  }
}
