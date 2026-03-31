export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const authHeader = request.headers.get('authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  return headers
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const params = new URLSearchParams()
    
    if (searchParams.get("company_id")) params.append("company_id", searchParams.get("company_id")!)
    if (searchParams.get("user_id")) params.append("user_id", searchParams.get("user_id")!)
    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)
    
    const response = await fetch(`${BACKEND_URL}/api/v1/lia/suggestions?${params.toString()}`, {
      headers: getAuthHeaders(request),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch suggestions" },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
