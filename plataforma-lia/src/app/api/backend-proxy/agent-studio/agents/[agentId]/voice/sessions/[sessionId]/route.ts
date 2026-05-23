/**
 * Sprint 3.7 W4-1 — proxy: GET /voice/sessions/{sessionId}
 *
 * Forward para lia-agent-system: GET /api/v1/agent-studio/agents/{id}/voice/sessions/{sid}
 * Polling-friendly. Tenant isolation enforced no backend via JWT.
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ agentId: string; sessionId: string }> },
) {
  try {
    const { agentId, sessionId } = await params
    const res = await fetch(
      `${BACKEND_URL}/api/v1/agent-studio/agents/${encodeURIComponent(
        agentId,
      )}/voice/sessions/${encodeURIComponent(sessionId)}`,
      { method: "GET", headers: getAuthHeaders(req) },
    )
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
