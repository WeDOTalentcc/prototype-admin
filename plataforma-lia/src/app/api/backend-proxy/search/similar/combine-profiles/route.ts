export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeadersForForm } from "@/lib/api/auth-headers"
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_FILE_SIZE = 10 * 1024 * 1024

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    const urls: string[] = []
    const cvFiles: File[] = []
    
    for (const [key, value] of formData.entries()) {
      if (key.startsWith("urls[") || key === "urls") {
        urls.push(value as string)
      } else if (key.startsWith("cvs[") || key === "cvs") {
        cvFiles.push(value as File)
      }
    }

    for (const file of cvFiles) {
      if (file.size > MAX_FILE_SIZE) {
        return NextResponse.json(
          { error: "CV file too large (max 10MB)" },
          { status: 413 }
        )
      }
    }

    if (urls.length === 0 && cvFiles.length === 0) {
      return NextResponse.json(
        { error: "Provide at least one URL or CV" },
        { status: 400 }
      )
    }

    const backendFormData = new FormData()
    urls.forEach((url) => {
      if (url.trim()) {
        backendFormData.append("urls", url)
      }
    })
    
    for (const file of cvFiles) {
      backendFormData.append("cvs", file)
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/search/similar/combine-profiles`, {
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
        { error: "Backend service unavailable. Please try again later." },
        { status: 503 }
      )
    }

    return NextResponse.json(
      { error: "Failed to combine profiles" },
      { status: 502 }
    )
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to process profiles" },
      { status: 500 }
    )
  }
}
