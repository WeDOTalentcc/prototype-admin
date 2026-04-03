export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://localhost:8000"

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
