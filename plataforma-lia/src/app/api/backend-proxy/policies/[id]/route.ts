export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    
    const response = await fetch(`${BACKEND_URL}/api/v1/policies/${id}`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': 'admin_company',
        'X-User-ID': 'admin_user',
        'X-User-Role': 'admin'
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to fetch policy' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await fetch(`${BACKEND_URL}/api/v1/policies/${id}`, {
      method: 'PUT',
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
      return NextResponse.json({ error: error.detail || 'Failed to update policy' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    
    const response = await fetch(`${BACKEND_URL}/api/v1/policies/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': 'admin_company',
        'X-User-ID': 'admin_user',
        'X-User-Role': 'admin'
      }
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to delete policy' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
