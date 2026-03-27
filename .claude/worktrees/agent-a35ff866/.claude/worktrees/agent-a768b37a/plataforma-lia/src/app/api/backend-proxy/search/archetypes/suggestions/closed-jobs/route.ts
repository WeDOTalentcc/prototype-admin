import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') || '10'
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/search/archetypes/suggestions?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      console.error(`Backend error: ${response.status}`)
      return NextResponse.json({ jobs: [], total: 0 })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Closed jobs suggestions proxy error:', error)
    return NextResponse.json({ jobs: [], total: 0 })
  }
}
