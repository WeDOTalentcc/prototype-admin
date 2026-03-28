export interface WorkOSLinks {
  dashboard: string
  users: string
  events: string
  logStreams: string
  directorySync: string
  adminPortal: string
}

export function getWorkOSLinks(organizationId?: string): WorkOSLinks {
  const base = 'https://dashboard.workos.com'
  
  if (organizationId) {
    return {
      dashboard: `${base}/organizations/${organizationId}`,
      users: `${base}/organizations/${organizationId}/users`,
      events: `${base}/events?organization_id=${organizationId}`,
      logStreams: `${base}/log-streams`,
      directorySync: `${base}/directory-sync?organization_id=${organizationId}`,
      adminPortal: `${base}/admin-portal?organization_id=${organizationId}`,
    }
  }
  
  return {
    dashboard: base,
    users: `${base}/users`,
    events: `${base}/events`,
    logStreams: `${base}/log-streams`,
    directorySync: `${base}/directory-sync`,
    adminPortal: `${base}/admin-portal`,
  }
}
