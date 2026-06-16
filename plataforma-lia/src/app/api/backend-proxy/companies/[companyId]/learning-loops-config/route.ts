export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * Backend proxy for Sprint B Phase 1+2 — Learning Loops config.
 *
 * GET   /api/backend-proxy/companies/{companyId}/learning-loops-config
 * PATCH /api/backend-proxy/companies/{companyId}/learning-loops-config
 *
 * Multi-tenancy: companyId from path (passed by frontend from JWT context).
 * Fail-graceful: erros retornam defaults (status 200) pra nao quebrar UI.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ companyId: string }> },
) {
  const { companyId } = await params
  if (!companyId) {
    return NextResponse.json(
      { error: "companyId required", config: null, source: "default" },
      { status: 400 },
    )
  }
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/companies/${encodeURIComponent(companyId)}/learning-loops-config`,
      { method: "GET", headers: getAuthHeaders(request) },
    )
    if (!res.ok) {
      return NextResponse.json(
        { config: null, source: "default", message: "backend unavailable" },
        { status: 200 },
      )
    }
    const data = await res.json()
    return NextResponse.json(data, { status: 200 })
  } catch {
    return NextResponse.json(
      { config: null, source: "default", message: "request failed" },
      { status: 200 },
    )
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ companyId: string }> },
) {
  const { companyId } = await params
  if (!companyId) {
    return NextResponse.json(
      { ok: false, error: "companyId required" },
      { status: 400 },
    )
  }
  try {
    const body = await request.json()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/companies/${encodeURIComponent(companyId)}/learning-loops-config`,
      {
        method: "PATCH",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      },
    )
    if (!res.ok) {
      return NextResponse.json(
        { ok: false, message: "backend rejected" },
        { status: res.status },
      )
    }
    const data = await res.json()
    return NextResponse.json(data, { status: 200 })
  } catch {
    return NextResponse.json(
      { ok: false, message: "request failed" },
      { status: 500 },
    )
  }
}
