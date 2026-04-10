import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// GET /api/backend-proxy/agent-templates — list templates (public + company)
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const domain = searchParams.get("domain")
  const params = domain ? `?domain=${domain}` : ""
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates${params}`, { headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}

// POST /api/backend-proxy/agent-templates — create template
export async function POST(req: NextRequest) {
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates`, { method: "POST", headers: getAuthHeaders(req), body })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
