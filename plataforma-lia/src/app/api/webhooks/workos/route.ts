export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { workos } from '@/lib/workos'

const WORKOS_WEBHOOK_SECRET = process.env.WORKOS_WEBHOOK_SECRET
const INTERNAL_API_SECRET = process.env.INTERNAL_API_SECRET || process.env.WORKOS_WEBHOOK_SECRET

interface DirectorySyncUser {
  id: string
  emails?: Array<{ value: string }>
  first_name?: string
  last_name?: string
  directory_id?: string
  state?: string
  raw_attributes?: Record<string, unknown>
}

interface DirectorySyncGroup {
  id: string
  name: string
  directory_id?: string
}

interface DirectorySyncMembership {
  user?: { id: string }
  group?: { id: string }
}

interface WorkOSConnection {
  id: string
  name: string
}

interface WorkOSDirectory {
  id: string
  name: string
}

function getInternalHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (INTERNAL_API_SECRET) {
    headers['X-Internal-Auth'] = INTERNAL_API_SECRET
  }
  return headers
}

export async function POST(req: NextRequest) {
  try {
    const payload = await req.text()
    const signature = req.headers.get('workos-signature')

    if (!signature) {
      return NextResponse.json({ error: 'Missing signature' }, { status: 401 })
    }

    if (!WORKOS_WEBHOOK_SECRET) {
      return NextResponse.json({ error: 'Webhook secret not configured' }, { status: 500 })
    }

    let event: { event: string; data: unknown }
    try {
      event = await workos.webhooks.constructEvent({
        payload,
        sigHeader: signature,
        secret: WORKOS_WEBHOOK_SECRET,
      }) as { event: string; data: unknown }
    } catch (err) {
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
    }


    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

    switch (event.event) {
      case 'dsync.user.created': {
        const userData = event.data as DirectorySyncUser
        await fetch(`${backendUrl}/api/v1/workos/users/created`, {
          method: 'POST',
          headers: getInternalHeaders(),
          body: JSON.stringify({
            workos_id: userData.id,
            email: userData.emails?.[0]?.value,
            first_name: userData.first_name,
            last_name: userData.last_name,
            directory_id: userData.directory_id,
            state: userData.state,
            raw_attributes: userData.raw_attributes,
          }),
        })
        break
      }

      case 'dsync.user.updated': {
        const userData = event.data as DirectorySyncUser
        await fetch(`${backendUrl}/api/v1/workos/users/updated`, {
          method: 'POST',
          headers: getInternalHeaders(),
          body: JSON.stringify({
            workos_id: userData.id,
            email: userData.emails?.[0]?.value,
            first_name: userData.first_name,
            last_name: userData.last_name,
            state: userData.state,
            raw_attributes: userData.raw_attributes,
          }),
        })
        break
      }

      case 'dsync.user.deleted': {
        const userData = event.data as DirectorySyncUser
        await fetch(`${backendUrl}/api/v1/workos/users/deleted`, {
          method: 'POST',
          headers: getInternalHeaders(),
          body: JSON.stringify({
            workos_id: userData.id,
            email: userData.emails?.[0]?.value,
          }),
        })
        break
      }

      case 'dsync.group.created':
      case 'dsync.group.updated':
      case 'dsync.group.deleted': {
        const groupData = event.data as DirectorySyncGroup
        const action = event.event.split('.')[2]
        await fetch(`${backendUrl}/api/v1/workos/groups/${action}`, {
          method: 'POST',
          headers: getInternalHeaders(),
          body: JSON.stringify({
            workos_id: groupData.id,
            name: groupData.name,
            directory_id: groupData.directory_id,
          }),
        })
        break
      }

      case 'dsync.group.user_added':
      case 'dsync.group.user_removed': {
        const membershipData = event.data as DirectorySyncMembership
        const memberAction = event.event.includes('added') ? 'added' : 'removed'
        await fetch(`${backendUrl}/api/v1/workos/group-membership`, {
          method: 'POST',
          headers: getInternalHeaders(),
          body: JSON.stringify({
            user_id: membershipData.user?.id,
            group_id: membershipData.group?.id,
            action: memberAction,
          }),
        })
        break
      }

      case 'connection.activated':
      case 'connection.deactivated':
      case 'connection.deleted': {
        const connectionData = event.data as WorkOSConnection
        const connAction = event.event.split('.')[1]
        break
      }

      case 'directory.activated':
      case 'directory.deactivated':
      case 'directory.deleted': {
        const directoryData = event.data as WorkOSDirectory
        const dirAction = event.event.split('.')[1]
        break
      }

      default:
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    return NextResponse.json({ error: 'Webhook processing failed' }, { status: 500 })
  }
}
