import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest) {
  const body = await req.text()
  const res = await fetch(`${BACKEND_URL}/api/v1/upgrade-requests`, {
    method: "POST",
    headers: getAuthHeaders(req),
    body,
  })
  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
