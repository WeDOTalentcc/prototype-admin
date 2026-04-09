/**
 * Place at: src/app/api/backend-proxy/talent-pools/[id]/route.ts
 */
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

// GET /api/backend-proxy/talent-pools/:id
export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await fetch(`${FASTAPI_URL}/api/v1/talent_pools/${params.id}`, {
    headers: getAuthHeaders(req),
  })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}

// PATCH /api/backend-proxy/talent-pools/:id
export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.text()
  const res = await fetch(`${FASTAPI_URL}/api/v1/talent_pools/${params.id}`, {
    method: "PATCH",
    headers: getAuthHeaders(req),
    body,
  })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}

// DELETE /api/backend-proxy/talent-pools/:id
export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await fetch(`${FASTAPI_URL}/api/v1/talent_pools/${params.id}`, {
    method: "DELETE",
    headers: getAuthHeaders(req),
  })
  const data = await res.text()
  return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
}
