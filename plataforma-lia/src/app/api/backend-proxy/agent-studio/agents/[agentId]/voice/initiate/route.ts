/**
 * Sprint 3.7 W4-1 — proxy: POST /voice/initiate
 *
 * Forward para lia-agent-system: POST /api/v1/agent-studio/agents/{id}/voice/initiate
 * Multi-tenancy via JWT (Authorization header pass-through).
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ agentId: string }> },
) {
  try {
    const { agentId } = await params
    const body = await req.text()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/agent-studio/agents/${encodeURIComponent(agentId)}/voice/initiate`,
      { method: "POST", headers: getAuthHeaders(req), body },
    )
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
