// Onda 4 F1 (2026-05-28) — proxy canonical para GET /ai-consumption/budget-alerts.
//
// Espelha endpoint Onda 4 B3 em lia-agent-system/app/api/v1/ai_consumption.py.
// Sem query params; tenant via JWT.
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/ai-consumption/budget-alerts`,
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
