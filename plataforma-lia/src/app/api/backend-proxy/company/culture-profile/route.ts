export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// Backend expects company_id as a path param: GET /api/v1/company/culture-profile/{company_id}
// Frontend callers send it as a query param: ?company_id=<uuid>
// This proxy converts query param → path param automatically.

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get("company_id")
  const path = companyId
    ? `/api/v1/company/culture-profile/${encodeURIComponent(companyId)}`
    : `/api/v1/company/culture-profile`
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, { headers: getAuthHeaders(request) })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/company/culture-profile`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body,
    })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function PUT(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get("company_id")
  const path = companyId
    ? `/api/v1/company/culture-profile/${encodeURIComponent(companyId)}`
    : `/api/v1/company/culture-profile`
  try {
    const body = await request.text()
    const res = await fetch(`${BACKEND_URL}${path}`, {
      method: "PUT",
      headers: getAuthHeaders(request),
      body,
    })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
