export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from "@/lib/api/validate"
import { z } from "zod"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const authHeaders = getAuthHeaders(request) as Record<string, string>
    const headers: Record<string, string> = { ...authHeaders }
    const companyHeader = request.headers.get("x-company-id")
    if (companyHeader) headers["x-company-id"] = companyHeader
    const cookieHeader = request.headers.get("cookie")
    if (cookieHeader) headers["cookie"] = cookieHeader

    const backendPath = `${BACKEND_URL}/api/v1/jd/suggest-responsibilities`
    const response = await fetch(backendPath, {
      method: "POST",
      headers,
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errText = await response.text().catch(() => "")
      return NextResponse.json(
        { success: false, responsibilities: [], error: errText.slice(0, 200) },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { success: false, responsibilities: [], error: "Proxy connection error" },
      { status: 500 }
    )
  }
}
