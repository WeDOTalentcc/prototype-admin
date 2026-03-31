export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://localhost:8000"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const queryString = searchParams.toString()
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/${queryString ? `?${queryString}` : ""}`
    
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch pipeline templates" },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/`
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to create pipeline template" },
      { status: 500 }
    )
  }
}
