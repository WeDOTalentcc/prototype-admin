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
    const backendPath = `/api/v1/stage-automation/${path.join("/")}`
    const url = `${BACKEND_URL}${backendPath}`
    
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    const authHeader = request.headers.get("authorization")
    if (authHeader) {
      headers["Authorization"] = authHeader
    }

    const fetchOptions: RequestInit = {
      method,
      headers,
    }

    if (method !== "GET" && method !== "HEAD") {
      try {
        const bodyResult = await validateBody(request, _bodySchema)

        if (!bodyResult.success) return bodyResult.response

        const body = bodyResult.data
        fetchOptions.body = JSON.stringify(body)
      } catch {
      }
    }

    const response = await fetch(url, fetchOptions)
    
    const contentType = response.headers.get("content-type") || ""
    
    if (contentType.includes("application/json")) {
      const data = await response.json()
      return NextResponse.json(data, { status: response.status })
    } else {
      const text = await response.text()
      return new NextResponse(text, { 
        status: response.status,
        headers: { "Content-Type": contentType }
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

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "PATCH", pathParams.path)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const pathParams = await params
  return proxyRequest(request, "DELETE", pathParams.path)
}
