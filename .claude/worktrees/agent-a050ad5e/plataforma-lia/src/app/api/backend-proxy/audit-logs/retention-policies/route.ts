import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/audit-logs/retention-policies`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': request.headers.get('X-Company-ID') || 'platform',
        'X-User-ID': request.headers.get('X-User-ID') || 'admin_user',
        'X-User-Role': request.headers.get('X-User-Role') || 'admin'
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to fetch retention policies' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching retention policies:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/audit-logs/retention-policies`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': request.headers.get('X-Company-ID') || 'platform',
        'X-User-ID': request.headers.get('X-User-ID') || 'admin_user',
        'X-User-Role': request.headers.get('X-User-Role') || 'admin'
      },
      body: JSON.stringify(body)
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to create retention policy' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating retention policy:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
