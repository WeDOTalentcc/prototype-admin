export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams(await Promise.resolve({ id }), routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id") || "default_user"
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/notifications/${id}/read?user_id=${userId}`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
      }
    )
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to mark notification as read" },
      { status: 500 }
    )
  }
}
