export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')
    const jobId = searchParams.get('job_id')
    
    let backendUrl = `${BACKEND_URL}/api/v1/job-analytics`
    
    if (action === 'commands') {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/commands`
    } else if (action === 'quick-insights' && jobId) {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/quick-insights/${jobId}`
    } else if (action === 'suggestions' && jobId) {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/suggestions/${jobId}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar dados de analytics', details: errorData },
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    let backendUrl = `${BACKEND_URL}/api/v1/job-analytics`
    
    if (action === 'execute') {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/execute`
    } else if (action === 'natural-query') {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/natural-query`
    } else if (action === 'compare') {
      backendUrl = `${BACKEND_URL}/api/v1/job-analytics/compare`
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao executar análise', details: errorData },
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
