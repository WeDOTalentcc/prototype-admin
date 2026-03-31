export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/policies${queryString ? `?${queryString}` : ''}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': 'admin_company',
        'X-User-ID': 'admin_user',
        'X-User-Role': 'admin'
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to fetch policies' }, { status: response.status })
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
    const body = _bodySchema.parse(await request.json())
    
    const response = await fetch(`${BACKEND_URL}/api/v1/policies`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': 'admin_company',
        'X-User-ID': 'admin_user',
        'X-User-Role': 'admin'
      },
      body: JSON.stringify(body)
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to create policy' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
