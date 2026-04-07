export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

async function proxyRequest(
  request: NextRequest,
  method: string,
  path: string[]
) {
  try {
    const backendPath = `/portal/data-request/${path.join("/")}`
    const url = `${BACKEND_URL}${backendPath}`
    
    const headers: Record<string, string> = {}

    const contentType = request.headers.get("content-type") || ""
    if (contentType && !contentType.includes("multipart/form-data")) {
      headers["Content-Type"] = contentType
    }

    const fetchOptions: RequestInit = {
      method,
      headers,
    }

    if (method !== "GET" && method !== "HEAD") {
      if (contentType.includes("multipart/form-data")) {
        const formData = await request.formData()
        fetchOptions.body = formData
      } else if (contentType.includes("application/json")) {
        try {
          const bodyResult = await validateBody(request, _bodySchema)

          if (!bodyResult.success) return bodyResult.response

          const body = bodyResult.data
          fetchOptions.body = JSON.stringify(body)
          headers["Content-Type"] = "application/json"
        } catch {
        }
      }
    }

    const response = await fetch(url, fetchOptions)
    
    const responseContentType = response.headers.get("content-type") || ""
    
    if (responseContentType.includes("application/json")) {
      const data = await response.json()
      return NextResponse.json(data, { status: response.status })
    } else {
      const text = await response.text()
      return new NextResponse(text, { 
        status: response.status,
        headers: { "Content-Type": responseContentType }
      })
    }
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to proxy request to backend" },
      { status: 500 }
    )
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "GET", pathParams.path)
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "POST", pathParams.path)
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "PUT", pathParams.path)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "DELETE", pathParams.path)
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "PATCH", pathParams.path)
}
