export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://localhost:8000"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const searchParams = request.nextUrl.searchParams
    const newName = searchParams.get("new_name")
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/${id}/clone${newName ? `?new_name=${encodeURIComponent(newName)}` : ""}`
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to clone pipeline template" },
      { status: 500 }
    )
  }
}
