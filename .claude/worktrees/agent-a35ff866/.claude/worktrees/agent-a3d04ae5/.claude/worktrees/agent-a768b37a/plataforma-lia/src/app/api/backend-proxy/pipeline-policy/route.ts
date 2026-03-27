import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const DEFAULT_COMPANY_ID = 'demo_company'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action') || 'templates'
    const companyId = searchParams.get('company_id') || DEFAULT_COMPANY_ID
    const candidateId = searchParams.get('candidate_id') || ''
    const targetStage = searchParams.get('target_stage') || ''

    let backendUrl: string

    if (action === 'validate-transition') {
      backendUrl = `${BACKEND_URL}/api/v1/pipeline-policy/${companyId}/validate-transition?candidate_id=${candidateId}&target_stage=${targetStage}`
    } else {
      backendUrl = `${BACKEND_URL}/api/v1/pipeline-policy/${companyId}/templates`
    }

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao consultar política de pipeline', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Pipeline policy proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
