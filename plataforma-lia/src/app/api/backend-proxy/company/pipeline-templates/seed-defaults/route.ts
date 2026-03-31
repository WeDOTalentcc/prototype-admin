export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const force = searchParams.get("force") === "true"
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/seed-defaults${force ? "?force=true" : ""}`
    
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
      { error: "Failed to seed default templates" },
      { status: 500 }
    )
  }
}
