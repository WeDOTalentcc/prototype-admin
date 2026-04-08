import { WorkOS } from '@workos-inc/node'

// Lazy initialization — env vars checked at runtime only (not at build time)
// This allows `next build` to complete without WORKOS_API_KEY in the build environment.
let _workos: WorkOS | null = null

export function getWorkOS(): WorkOS {
  if (!process.env.WORKOS_API_KEY) {
    throw new Error('WORKOS_API_KEY environment variable is required')
  }
  if (!_workos) {
    _workos = new WorkOS(process.env.WORKOS_API_KEY)
  }
  return _workos
}

// Legacy export for backwards compatibility — resolves lazily
export const workos = new Proxy({} as WorkOS, {
  get(_target, prop) {
    return (getWorkOS() as unknown as Record<string | symbol, unknown>)[prop]
  }
})

export const WORKOS_CONFIG = {
  clientId: process.env.WORKOS_CLIENT_ID!,
  redirectUri: process.env.WORKOS_REDIRECT_URI || `${
    process.env.REPLIT_DEV_DOMAIN
      ? `https://${process.env.REPLIT_DEV_DOMAIN}`
      : process.env.APP_DOMAIN
        ? `https://${process.env.APP_DOMAIN}`
        : 'https://wedotalent.cc'
  }/api/auth/workos/callback`,
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
