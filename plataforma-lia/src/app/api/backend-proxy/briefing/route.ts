export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id")

    // BUG-08: não aceitar default_user como fallback no server-side. Quando o
    // FE ainda não sabe quem é o usuário, o backend recebe user_id=default_user
    // e contamina contadores. Agora devolve 400 para estimular o caller a
    // aguardar auth antes de chamar.
    if (!userId || userId === "default_user") {
      return NextResponse.json(
        { success: false, error: "user_id ausente ou inválido" },
        { status: 400 }
      )
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/briefing?user_id=${encodeURIComponent(userId)}`, {
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: "Failed to fetch briefing" },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch briefing" },
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
    
    const response = await fetch(`${BACKEND_URL}/api/v1/briefing/refresh`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: "Failed to refresh briefing" },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to refresh briefing" },
      { status: 500 }
    )
  }
}
