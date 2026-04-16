export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { jobCreateSchema } from '@/lib/schemas'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    const response = await fetch(`${BACKEND_URL}/api/v1/job-vacancies${queryString ? `?${queryString}` : ''}`, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar vagas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    // Unwrap FastAPI envelope: {ok: true, data: {total, items}}
    const payload = (data && typeof data === 'object' && 'ok' in data && data.data) ? data.data : data
    return NextResponse.json(payload)
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error)
    console.error('[job-vacancies] GET error:', msg)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend', details: msg },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, jobCreateSchema)
    if (!bodyResult.success) return bodyResult.response

    const response = await fetch(`${BACKEND_URL}/api/v1/job-vacancies`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar vaga', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    const payload = (data && typeof data === 'object' && 'ok' in data && data.data) ? data.data : data
    return NextResponse.json(payload)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
