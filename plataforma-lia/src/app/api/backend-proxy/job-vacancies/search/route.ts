export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const query = searchParams.get('query') || ''
    const page = searchParams.get('page') || '1'
    const pageSize = searchParams.get('page_size') || '10'
    
    const backendUrl = `${BACKEND_URL}/api/v1/job-vacancies/search?query=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: 'Backend request failed', details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    const payload = (data && typeof data === 'object' && 'ok' in data && data.data) ? data.data : data
    return NextResponse.json(payload)
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    )
  }
}
