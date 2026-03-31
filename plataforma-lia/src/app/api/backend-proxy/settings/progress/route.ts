export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/settings/progress`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json({
        overall: 50,
        sections: {
          'company-team': 60,
          'recruitment': 40,
          'communication': 60,
          'goals-planning': 50,
          'global-search': 80
        },
        subsections: {}
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      overall: 50,
      sections: {
        'company-team': 60,
        'recruitment': 40,
        'communication': 60,
        'goals-planning': 50,
        'global-search': 80
      },
      subsections: {},
      error: 'Failed to connect to backend'
    })
  }
}
