export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications/send`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to send notification" },
      { status: 500 }
    )
  }
}
