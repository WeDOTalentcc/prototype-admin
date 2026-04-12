import { NextRequest, NextResponse } from "next/server"

const FASTAPI_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  const cookie = req.headers.get("cookie")
  if (cookie) headers["Cookie"] = cookie
  return headers
}

// GET /api/backend-proxy/talent-pools — list pools
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const status = searchParams.get("status")
    const path = `/api/v1/talent-pools${status ? `?status=${status}` : ""}`
    const res = await fetch(`${FASTAPI_URL}${path}`, { headers: getAuthHeaders(req) })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

// POST /api/backend-proxy/talent-pools — create pool
export async function POST(req: NextRequest) {
  try {
    const body = await req.text()
    const res = await fetch(`${FASTAPI_URL}/api/v1/talent-pools`, {
      method: "POST",
      headers: getAuthHeaders(req),
      body,
    })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
