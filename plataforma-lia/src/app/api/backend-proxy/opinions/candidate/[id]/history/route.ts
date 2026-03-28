import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const searchParams = request.nextUrl.searchParams
    const company_id = searchParams.get("company_id") || "demo_company"
    
    const response = await fetch(`${BACKEND_URL}/api/v1/opinions/candidate/${id}/history?company_id=${company_id}`)
    
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
