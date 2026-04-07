export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const DEFAULT_WORKFORCE = [
  { month: 'Jan', department: 'Tecnologia', planned: 5, actual: 4, ai_suggestion: 6 },
  { month: 'Fev', department: 'Tecnologia', planned: 4, actual: 5 },
  { month: 'Mar', department: 'Tecnologia', planned: 6, actual: 0, ai_suggestion: 5 },
  { month: 'Jan', department: 'Comercial', planned: 3, actual: 3 },
  { month: 'Fev', department: 'Comercial', planned: 2, actual: 2 },
  { month: 'Mar', department: 'Comercial', planned: 4, actual: 0, ai_suggestion: 3 },
  { month: 'Jan', department: 'RH', planned: 1, actual: 1 },
  { month: 'Fev', department: 'RH', planned: 1, actual: 0 },
  { month: 'Mar', department: 'RH', planned: 2, actual: 0, ai_suggestion: 1 }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const year = searchParams.get('year')
    
    let backendUrl = `${BACKEND_URL}/api/v1/workforce/entries`
    if (year) {
      backendUrl = `${backendUrl}?year=${year}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json(DEFAULT_WORKFORCE, { status: 200 })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(DEFAULT_WORKFORCE, { status: 200 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/workforce/entries`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao salvar planejamento de workforce', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
