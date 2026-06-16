export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeadersForForm } from "@/lib/api/auth-headers"
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
import { MAX_FILE_SIZE } from '@/constants/upload'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { success: false, error: "No file provided" },
        { status: 400 }
      )
    }

    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "File too large (max 10MB)" },
        { status: 413 }
      )
    }

    const backendFormData = new FormData()
    backendFormData.append("file", file)

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/analysis/file`, {
        method: "POST",
        headers: getAuthHeadersForForm(request),
        body: backendFormData,
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }

    } catch (backendError) {
      return NextResponse.json(
        { success: false, error: "Backend service unavailable. Please try again later." },
        { status: 503 }
      )
    }

    return NextResponse.json(
      { success: false, error: "Failed to analyze file" },
      { status: 502 }
    )
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to analyze file" },
      { status: 500 }
    )
  }
}
