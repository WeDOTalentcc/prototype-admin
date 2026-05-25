import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || ""

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  const cid = req.headers.get("x-company-id")
  if (cid) headers["X-Company-ID"] = cid
  return headers
}

export async function GET(req: NextRequest) {
  const res = await fetch(`${BACKEND_URL}/api/v1/agent-template-catalog/sectors`, {
    headers: getAuthHeaders(req),
  })
  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
