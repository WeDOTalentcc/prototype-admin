export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request)
    const response = await fetch(`${BACKEND_URL}/api/v1/offer-agent/readiness`, {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(8000),
    })
    if (!response.ok) {
      // fail-open: sem dados suficientes, retorna score 0 sem quebrar o FE
      return NextResponse.json({ score: 0, total: 4, ready: false, items: [] }, { status: 200 })
    }
    const data = await response.json()
    const unwrapped = data?.ok === true && "data" in data ? data.data : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json({ score: 0, total: 4, ready: false, items: [] }, { status: 200 })
  }
}
