export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'


export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    // FIX 2026-05-25: trailing slash obrigatório — FastAPI router list endpoint
    // tem prefix "/data-subject-requests" + route "/" → full path "/data-subject-requests/".
    // Sem slash, FastAPI retorna 404 ao chamar collection list (caso DSRInboxPanel).
    const response = await fetch(
      `${BACKEND_URL}/api/v1/data-subject-requests/${queryString ? `?${queryString}` : ''}`,
      {
        headers: getAuthHeaders(request)
      }
    )
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { error: error.detail || 'Failed to fetch data subject requests' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await fetch(`${BACKEND_URL}/api/v1/data-subject-requests/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(request),
      },
      body: JSON.stringify(body)
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { error: error.detail || 'Failed to create data subject request' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
