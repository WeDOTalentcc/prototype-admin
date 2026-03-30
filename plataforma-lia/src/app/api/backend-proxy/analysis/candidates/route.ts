import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000"

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const company_id = searchParams.get("company_id") || "demo_company"
    
    const body = _bodySchema.parse(await request.json())
    
    const response = await fetch(`${BACKEND_URL}/api/v1/analysis/candidates?company_id=${company_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
      { error: "Failed to analyze candidates" },
      { status: 500 }
    )
  }
}
