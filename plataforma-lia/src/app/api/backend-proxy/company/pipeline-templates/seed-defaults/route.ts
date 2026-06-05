export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const seedQuerySchema = z.object({
  force: z.enum(['true', 'false']).optional(),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, seedQuerySchema)
    if (!queryValidation.success) return queryValidation.response

    const force = queryValidation.data.force === "true"
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/seed-defaults${force ? "?force=true" : ""}`
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...getAuthHeaders(request),
        "Accept": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to seed default templates" },
      { status: 500 }
    )
  }
}
