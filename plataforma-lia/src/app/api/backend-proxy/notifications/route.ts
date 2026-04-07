export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    
    if (searchParams.get("user_id")) params.append("user_id", searchParams.get("user_id")!)
    if (searchParams.get("unread_only")) params.append("unread_only", searchParams.get("unread_only")!)
    if (searchParams.get("category")) params.append("category", searchParams.get("category")!)
    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications?${params.toString()}`, {
      headers: getAuthHeaders(request),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch notifications" },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to create notification" },
      { status: 500 }
    )
  }
}
