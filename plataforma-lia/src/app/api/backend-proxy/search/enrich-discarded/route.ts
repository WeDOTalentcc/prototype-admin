export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from "@/lib/api/validate"
import { z } from "zod"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const _bodySchema = z.object({
  linkedin_url: z.string().min(1),
  candidate_id: z.string().nullable().optional(),
  candidate_name: z.string().nullable().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const response = await fetch(`${BACKEND_URL}/api/v1/search/enrich-discarded`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(bodyResult.data),
    })

    const data = await response.json()
    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || "Failed to re-enrich candidate" },
        { status: response.status }
      )
    }
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 }
    )
  }
}
