/**
 * Place at: src/app/api/backend-proxy/agent-templates/[id]/route.ts
 * Proxies Stage 8 CRUD: get, patch, delete (archive) agent template
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// GET /api/backend-proxy/agent-templates/:id
export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates/${params.id}`, { headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

// PATCH /api/backend-proxy/agent-templates/:id
export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates/${params.id}`, { method: "PATCH", headers: getAuthHeaders(req), body })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

// DELETE /api/backend-proxy/agent-templates/:id — soft archive
export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates/${params.id}`, { method: "DELETE", headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
