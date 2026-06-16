// WT-2022 Camada IA Proativa: proxy canonical para /api/v1/proactive-hints/
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const url = `${BACKEND_URL}/api/v1/proactive-hints/`
    const response = await fetch(url, {
      headers: getAuthHeaders(request),
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { hints: [], count: 0, error: "proxy failed" },
      { status: 500 },
    )
  }
}
