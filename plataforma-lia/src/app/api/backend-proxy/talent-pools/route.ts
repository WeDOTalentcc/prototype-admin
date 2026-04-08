/**
 * Place at: src/app/api/backend-proxy/talent-pools/route.ts
 */
import { NextRequest, NextResponse } from "next/server"

const RAILS_URL = process.env.RAILS_BACKEND_URL || process.env.BACKEND_URL || ""

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
  const { searchParams } = new URL(req.url)
  const status = searchParams.get("status")
  const path = `/v1/users/talent_pools${status ? `?status=${status}` : ""}`
  const res = await fetch(`${RAILS_URL}${path}`, { headers: getAuthHeaders(req) })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}

// POST /api/backend-proxy/talent-pools — create pool
export async function POST(req: NextRequest) {
  const body = await req.text()
  const res = await fetch(`${RAILS_URL}/v1/users/talent_pools`, {
    method: "POST",
    headers: getAuthHeaders(req),
    body,
  })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}
