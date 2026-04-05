export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const tokenCookie = request.cookies.get('lia_access_token')
  if (!tokenCookie?.value || tokenCookie.value === '_sso_session_') {
    return NextResponse.json({ token: null }, { status: 401 })
  }
  return NextResponse.json({ token: tokenCookie.value })
}
