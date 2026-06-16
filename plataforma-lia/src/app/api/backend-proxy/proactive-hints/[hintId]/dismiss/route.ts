// WT-2022 Camada IA Proativa: dismiss proxy
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ hintId: string }> },
) {
  try {
    const { hintId } = await params
    const url = `${BACKEND_URL}/api/v1/proactive-hints/${encodeURIComponent(hintId)}/dismiss`
    const response = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(request),
    })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "dismiss proxy failed" },
      { status: 500 },
    )
  }
}
