/**
 * Place at: src/app/api/backend-proxy/talent-pools/[id]/candidates/route.ts
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

// GET /api/backend-proxy/talent-pools/:id/candidates
export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(req.url)
  const stage = searchParams.get("stage")
  const path = `/v1/users/talent_pools/${params.id}/candidates${stage ? `?stage=${stage}` : ""}`
  const res = await fetch(`${RAILS_URL}${path}`, { headers: getAuthHeaders(req) })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}

// POST /api/backend-proxy/talent-pools/:id/candidates — add candidates
export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.text()
  const res = await fetch(`${RAILS_URL}/v1/users/talent_pools/${params.id}/add_candidates`, {
    method: "POST",
    headers: getAuthHeaders(req),
    body,
  })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}
