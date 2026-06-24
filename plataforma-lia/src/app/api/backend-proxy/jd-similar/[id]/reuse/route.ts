export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * POST /api/backend-proxy/jd-similar/{id}/reuse
 * Sprint B Phase 1 - increment reuse counter when recruiter clicks "use as base".
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  if (!id) {
    return NextResponse.json({ ok: false, error: "id required" }, { status: 400 })
  }
  try {
    const body = await request.json()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/jd-similar/${encodeURIComponent(id)}/reuse`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      },
    )
    if (!res.ok) {
      return NextResponse.json({ ok: false, message: "backend rejected" }, { status: 200 })
    }
    return NextResponse.json(await res.json(), { status: 200 })
  } catch {
    return NextResponse.json({ ok: false, message: "request failed" }, { status: 200 })
  }
}
