export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params
    const searchParams = request.nextUrl.searchParams
    const backendParams = new URLSearchParams()
    for (const key of ["include_warnings", "limit", "offset"]) {
      const val = searchParams.get(key)
      if (val !== null) backendParams.set(key, val)
    }

    const url = `${BACKEND_URL}/api/v1/fairness/jobs/${encodeURIComponent(jobId)}/blocks?${backendParams.toString()}`
    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: "Erro ao consultar bloqueios de fairness da vaga" },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json(
      { error: "Erro interno ao consultar bloqueios de fairness" },
      { status: 500 }
    )
  }
}
