export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { resolveCompanyId } from "@/lib/api/resolve-company-id"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const company_id = await resolveCompanyId(request)
    if (!company_id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const response = await fetch(`${BACKEND_URL}/api/v1/opinions/candidate/${id}/history?company_id=${company_id}`, { headers: getAuthHeaders(request) })
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json([])
      }
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
      { error: "Failed to fetch opinions history" },
      { status: 500 }
    )
  }
}
