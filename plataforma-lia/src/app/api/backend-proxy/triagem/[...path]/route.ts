export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathStr = path.join("/")
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/triagem/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
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
    const pathStr = path.join("/")
    const contentType = request.headers.get("content-type") || ""
    const backendUrl = `${BACKEND_URL}/api/v1/triagem/${pathStr}`

    let fetchOptions: RequestInit

    if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData()
      fetchOptions = {
        method: "POST",
        body: formData,
      }
    } else {
      let body: string | undefined
      if (contentType.includes("application/json")) {
        try {
          const jsonBody = await request.json()
          body = JSON.stringify(jsonBody)
        } catch {
          body = undefined
        }
      }
      fetchOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
