export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id')

    let url = `${BACKEND_URL}/api/v1/tasks/summary`
    if (userId) url += `?user_id=${userId}`

    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json(
        { pending: 0, in_progress: 0, completed: 0, overdue: 0, critical: 0, total_active: 0 },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { pending: 0, in_progress: 0, completed: 0, overdue: 0, critical: 0, total_active: 0 },
      { status: 200 }
    )
  }
}
