export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { resolveCompanyId } from "@/lib/api/resolve-company-id"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const company_id = await resolveCompanyId(request)
    if (!company_id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const user_id = searchParams.get("user_id") || "system"
    
    const bodyResult = await validateBody(request, _bodySchema)

    
    if (!bodyResult.success) return bodyResult.response

    
    const body = bodyResult.data
    
    const response = await fetch(`${BACKEND_URL}/api/v1/opinions?company_id=${company_id}&user_id=${user_id}`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: "Backend error", details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to create opinion" },
      { status: 500 }
    )
  }
}
