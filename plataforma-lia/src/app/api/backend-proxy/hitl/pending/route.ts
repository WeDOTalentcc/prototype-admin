export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request, true)
    const res = await fetch(`${BACKEND_URL}/api/v1/hitl/pending`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return NextResponse.json(
        { error: "Failed to fetch pending approvals", detail: text },
        { status: res.status }
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    return NextResponse.json(
      { error: "Internal error fetching pending approvals" },
      { status: 500 }
    )
  }
}
