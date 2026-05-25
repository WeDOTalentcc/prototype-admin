import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  // forward x-company-id se cliente injetar — backend canonical valida via JWT mas
  // mantém defesa-em-profundidade pra ambientes onde JWT carrega só user info
  const cid = req.headers.get("x-company-id")
  if (cid) headers["X-Company-ID"] = cid
  return headers
}

// GET /api/backend-proxy/agent-template-catalog?category=X&sector=Y&active_only=true
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const qs = searchParams.toString()
  const url = `${BACKEND_URL}/api/v1/agent-template-catalog${qs ? "?" + qs : ""}`
  const res = await fetch(url, { headers: getAuthHeaders(req) })
  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}

export async function POST(req: NextRequest) {
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-template-catalog`, {
    method: "POST",
    headers: getAuthHeaders(req),
    body,
  })
  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
