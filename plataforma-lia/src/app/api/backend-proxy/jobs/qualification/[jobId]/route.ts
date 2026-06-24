export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateParams, validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  jobId: z.string().min(1, 'jobId is required'),
})

const _bodySchema = z.record(z.string(), z.unknown())

export async function GET(request: NextRequest, { params }: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await params
    const paramValidation = validateParams({ jobId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const backendUrl = `${BACKEND_URL}/api/v1/jobs/qualification/${jobId}`
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao buscar classificação', details: errorData }, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await params
    const paramValidation = validateParams({ jobId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const backendUrl = `${BACKEND_URL}/api/v1/jobs/qualification/${jobId}/classify`
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
    })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao classificar e salvar', details: errorData }, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await params
    const paramValidation = validateParams({ jobId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response

    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/jobs/qualification/${jobId}/override`
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao alterar classificação', details: errorData }, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
