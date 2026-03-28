import { WorkOS } from '@workos-inc/node'

if (!process.env.WORKOS_API_KEY) {
  throw new Error('WORKOS_API_KEY environment variable is required')
}

if (!process.env.WORKOS_CLIENT_ID) {
  throw new Error('WORKOS_CLIENT_ID environment variable is required')
}

export const workos = new WorkOS(process.env.WORKOS_API_KEY)

export const WORKOS_CONFIG = {
  clientId: process.env.WORKOS_CLIENT_ID!,
  redirectUri: process.env.WORKOS_REDIRECT_URI || `${process.env.REPLIT_DEV_DOMAIN ? `https://${process.env.REPLIT_DEV_DOMAIN}` : 'http://localhost:5000'}/api/auth/workos/callback`,
}

export interface WorkOSProfile {
  id: string
  email: string
  firstName: string
  lastName: string
  organizationId: string | null
  connectionId: string
  connectionType: string
  idpId: string
  rawAttributes: Record<string, unknown>
}

export interface WorkOSUser {
  id: string
  email: string
  firstName: string | null
  lastName: string | null
  emailVerified: boolean
  profilePictureUrl: string | null
  createdAt: string
  updatedAt: string
}
