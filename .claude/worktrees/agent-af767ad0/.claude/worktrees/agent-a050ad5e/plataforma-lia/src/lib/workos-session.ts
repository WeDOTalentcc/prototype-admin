export interface WorkOSSession {
  accessToken?: string
  userId?: string
  email?: string
  organizationId?: string
}

export async function getWorkOSSession(): Promise<WorkOSSession | null> {
  return null
}
