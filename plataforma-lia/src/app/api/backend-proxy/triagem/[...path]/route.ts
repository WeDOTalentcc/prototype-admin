export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders, getAuthHeadersForForm } from "@/lib/api/auth-headers"
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_BODY_SIZE = 5 * 1024 * 1024

const catchAllPathSchema = z.object({
  path: z.array(z.string().min(1)).min(1, 'Path is required'),
})

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathValidation = catchAllPathSchema.safeParse({ path })
    if (!pathValidation.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }
    const pathStr = path.join("/")
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/triagem/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const detail = errorData.detail || errorData.message || "Erro desconhecido"
      return NextResponse.json(
        { ...errorData, detail },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { detail: "Serviço indisponível. Tente novamente em instantes." },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathValidation2 = catchAllPathSchema.safeParse({ path })
    if (!pathValidation2.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }
    const pathStr = path.join("/")
    const contentType = request.headers.get("content-type") || ""
    const backendUrl = `${BACKEND_URL}/api/v1/triagem/${pathStr}`

    let fetchOptions: RequestInit

    if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData()
      fetchOptions = {
        method: "POST",
        headers: getAuthHeadersForForm(request),
        body: formData,
      }
    } else {
      let body: string | undefined
      if (contentType.includes("application/json")) {
        const _jsonSchema = z.record(z.string(), z.unknown())
        const parseResult = _jsonSchema.safeParse(await request.json().catch(() => ({})))
        body = parseResult.success ? JSON.stringify(parseResult.data) : undefined
      }
      fetchOptions = {
        method: "POST",
        headers: getAuthHeaders(request),
        body,
      }
    }

    const response = await fetch(backendUrl, fetchOptions)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const detail = errorData.detail || errorData.message || "Erro desconhecido"
      return NextResponse.json(
        { ...errorData, detail },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { detail: "Serviço indisponível. Tente novamente em instantes." },
      { status: 500 }
    )
  }
}
