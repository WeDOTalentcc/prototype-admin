import { createHmac, timingSafeEqual } from 'crypto'

const SESSION_SECRET = process.env.WORKOS_SESSION_SECRET || process.env.WORKOS_API_KEY || 'fallback-dev-secret'

export interface SessionPayload {
  workosProfile: {
    id: string
    email: string
    firstName: string | null
    lastName: string | null
    organizationId: string | null
    connectionId: string
    connectionType: string
    idpId: string
  }
  accessToken: string
  expiresAt: number
  createdAt: number
}

function createSignature(payload: string): string {
  return createHmac('sha256', SESSION_SECRET)
    .update(payload)
    .digest('hex')
}

function verifySignature(payload: string, signature: string): boolean {
  const expectedSignature = createSignature(payload)
  try {
    return timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    )
  } catch {
    return false
  }
}

export function signSession(data: SessionPayload): string {
  const payload = Buffer.from(JSON.stringify(data)).toString('base64')
  const signature = createSignature(payload)
  return `${payload}.${signature}`
}

export function verifyAndDecodeSession(token: string): SessionPayload | null {
  try {
    const [payload, signature] = token.split('.')
    
    if (!payload || !signature) {
      return null
    }

    if (!verifySignature(payload, signature)) {
      return null
    }

    const data = JSON.parse(Buffer.from(payload, 'base64').toString()) as SessionPayload

    if (data.expiresAt < Date.now()) {
      return null
    }

    if (!data.workosProfile?.id || !data.workosProfile?.email) {
      return null
    }

    return data
  } catch {
    return null
  }
}
