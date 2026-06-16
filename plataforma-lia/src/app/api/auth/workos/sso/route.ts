export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'
import { workos, WORKOS_CONFIG } from '@/lib/workos'

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams
    const organizationId = searchParams.get('organization')
    const connectionId = searchParams.get('connection')
    const email = searchParams.get('email')
    const returnTo = searchParams.get('returnTo') || '/dashboard'

    if (!organizationId && !connectionId && !email) {
      return NextResponse.json(
        { error: 'Either organization, connection, or email is required to initiate SSO' },
        { status: 400 }
      )
    }

    const state = Buffer.from(JSON.stringify({ returnTo })).toString('base64')

    const authorizationUrl = workos.sso.getAuthorizationUrl({
      clientId: WORKOS_CONFIG.clientId,
      redirectUri: WORKOS_CONFIG.redirectUri,
      ...(organizationId && { organization: organizationId }),
      ...(connectionId && { connection: connectionId }),
      state,
    })

    return NextResponse.redirect(authorizationUrl)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to initiate SSO' },
      { status: 500 }
    )
  }
}
