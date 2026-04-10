import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// GET /api/backend-proxy/digital-twins — list twins
export async function GET(req: NextRequest) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/digital-twins`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

// POST /api/backend-proxy/digital-twins — create twin
export async function POST(req: NextRequest) {
  try {
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/digital-twins`, { method: "POST", headers: getAuthHeaders(req), body })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
