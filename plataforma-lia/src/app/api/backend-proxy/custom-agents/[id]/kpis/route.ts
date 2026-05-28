// Onda 4 F1 (2026-05-28) — proxy canonical para GET /custom-agents/{id}/kpis.
//
// Espelha o endpoint Onda 4 B1 em lia-agent-system/app/api/v1/custom_agents.py.
// Aceita query param `period` (7d|30d|90d|all). Auth via Bearer token.
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
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/custom-agents/${encodeURIComponent(id)}/kpis${qs ? `?${qs}` : ""}`,
      { headers: getAuthHeaders(req) },
    )
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
