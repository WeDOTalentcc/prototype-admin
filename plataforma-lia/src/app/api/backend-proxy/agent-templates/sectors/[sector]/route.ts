import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

// POST /api/backend-proxy/agent-templates/sectors/:sector/apply
export async function POST(req: NextRequest, { params: pRaw }: { params: Promise<{ sector: string }> }) {
  const { sector } = await pRaw;
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-templates/sectors/${sector}/apply`, {
    method: "POST", headers: getAuthHeaders(req), body,
  })
  return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
}
