export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { resolveCompanyId } from "@/lib/api/resolve-company-id"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

// Gera o parecer job-directed (matriz de qualificação) e auto-salva versionado.
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const company_id = await resolveCompanyId(request)
    if (!company_id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }
    const body = await request.text()
    const response = await fetch(
      `${BACKEND_URL}/api/v1/opinions/candidate/${id}/parecer?company_id=${encodeURIComponent(company_id)}`,
      {
        method: "POST",
        headers: { ...getAuthHeaders(request), "Content-Type": "application/json" },
        body: body || "{}",
      }
    )
    const text = await response.text()
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch {
    return NextResponse.json({ error: "Failed to generate parecer" }, { status: 500 })
  }
}
