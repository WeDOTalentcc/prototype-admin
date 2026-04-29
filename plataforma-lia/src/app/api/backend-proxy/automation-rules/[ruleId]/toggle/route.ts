export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ ruleId: string }> },
) {
  const { ruleId } = await params
  const companyId = request.headers.get("X-Company-ID") || "platform"
  const headers = getAuthHeaders(request) as Record<string, string>
  headers["X-Company-ID"] = companyId
  const url = `${BACKEND_URL}/api/v1/automation-rules/company/${encodeURIComponent(companyId)}/toggle/${encodeURIComponent(ruleId)}`
  const r = await fetch(url, { method: "POST", headers })
  const data = await r.json().catch(() => ({}))
  return NextResponse.json(data, { status: r.status })
}
