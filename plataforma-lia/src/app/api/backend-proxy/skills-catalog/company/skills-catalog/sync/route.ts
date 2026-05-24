export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from "@/lib/api/validate"
import { z } from "zod"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const _bodySchema = z.object({
  tech_stack: z.array(z.string()),
})

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const body = bodyResult.data

    const response = await fetch(
      `${BACKEND_URL}/api/v1/skills-catalog/company/skills-catalog/sync`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      },
    )

    const text = await response.text()
    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: text || "Failed to sync skills catalog" },
        { status: response.status },
      )
    }
    try {
      return NextResponse.json(JSON.parse(text))
    } catch {
      return NextResponse.json({ success: true })
    }
  } catch {
    return NextResponse.json(
      { success: false, error: "Proxy connection error" },
      { status: 500 },
    )
  }
}
