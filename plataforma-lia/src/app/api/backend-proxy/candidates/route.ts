export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_LIMIT = 200

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)

    // Cap limit to backend maximum (200)
    const rawLimit = parseInt(searchParams.get("limit") || "20", 10)
    if (rawLimit > MAX_LIMIT) searchParams.set("limit", String(MAX_LIMIT))

    const res = await fetch(`${BACKEND_URL}/api/v1/candidates?${searchParams.toString()}`, {
      headers: getAuthHeaders(request),
    })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/candidates`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body,
    })
    const data = await res.text()
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
