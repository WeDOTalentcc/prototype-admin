export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const path = searchParams.get("path") || ""
    const params = new URLSearchParams()

    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)

    const queryString = params.toString() ? `?${params.toString()}` : ""
    const url = `${BACKEND_URL}/api/v1/proactive-actions/${path}${queryString}`

    const response = await fetch(url, {
      headers: getAuthHeaders(request),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch proactive actions" },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const path = searchParams.get("path") || ""
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const url = `${BACKEND_URL}/api/v1/proactive-actions/${path}`

    const response = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to process proactive action" },
      { status: 500 }
    )
  }
}
