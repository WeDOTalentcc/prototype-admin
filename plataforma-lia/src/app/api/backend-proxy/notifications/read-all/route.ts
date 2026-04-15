export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const readAllQuerySchema = z.object({
  user_id: z.string().min(1).optional(),
  category: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, readAllQuerySchema)
    if (!queryValidation.success) return queryValidation.response

    const userId = queryValidation.data.user_id
    const category = queryValidation.data.category

    // BUG-08: recusar default_user — caller deve aguardar auth antes de chamar
    if (!userId || userId === "default_user") {
      return NextResponse.json(
        { success: false, error: "user_id ausente ou inválido" },
        { status: 400 }
      )
    }

    const params = new URLSearchParams()
    params.append("user_id", userId)
    if (category) params.append("category", category)

    const response = await fetch(
      `${BACKEND_URL}/api/v1/notifications/read-all?${params.toString()}`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to mark all notifications as read" },
      { status: 500 }
    )
  }
}
