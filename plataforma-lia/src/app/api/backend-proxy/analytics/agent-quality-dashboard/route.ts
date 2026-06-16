/**
 * Proxy route for Agent Quality Dashboard API.
 * GET /api/backend-proxy/analytics/agent-quality-dashboard?period=7d
 */
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function GET(request: NextRequest) {
  const auth = request.headers.get("Authorization") || ""
  const search = request.nextUrl.search

  const resp = await fetch(
    `${BACKEND_URL}/api/v1/analytics/agent-quality-dashboard${search}`,
    {
      headers: {
        Authorization: auth,
        "Content-Type": "application/json",
      },
    }
  )

  const data = await resp.json()
  return NextResponse.json(data, { status: resp.status })
}
