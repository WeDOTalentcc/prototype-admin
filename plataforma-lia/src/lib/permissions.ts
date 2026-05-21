/**
 * WT-2022 P0.RBAC (registrado 2026-05-21) — escopo DESTE módulo:
 *
 * `PERMISSION_CATALOG` + helpers (`canPerform`, `isAdmin`,
 * `isManagerOrAbove`, etc.) — RBAC permission catalog client-side com
 * enforcement metadata (server | client-only | both).
 *
 * NÃO CONFUNDIR com `User.role` canonical em `src/services/auth-service.ts`:
 *   - `auth-service.ts` User.role = `'admin' | 'recruiter' | 'viewer' | 'wedotalent_admin'`
 *     (authority canonical do JWT/backend).
 *   - `lib/permissions.ts` UserRole (re-export do `utils/permissions.ts`) =
 *     `'admin' | 'manager' | 'senior_recruiter' | 'recruiter' | 'intern'`
 *     (níveis de permissão UI; legado RBAC).
 *
 * Status (2026-05-21): SEM CONSUMERS EXTERNOS além do próprio módulo.
 * Não deletar sem autorização Paulo (roadmap consolidação RBAC pendente).
 */
import type { UserRole } from '@/utils/permissions'

export type PermissionAction = 'read' | 'write' | 'delete' | 'execute' | '*'
export type PermissionResource =
  | 'candidates'
  | 'jobs'
  | 'reports'
  | 'team_performance'
  | 'evaluations'
  | 'lia_insights'
  | 'lia_actions'
  | 'interviews'
  | 'assessments'
  | 'references'
  | 'analytics'
  | 'settings'
  | '*'

export interface PermissionCheck {
  action: PermissionAction
  resource: PermissionResource
  enforcement: 'server' | 'client-only' | 'both'
  description: string
}

export const PERMISSION_CATALOG: Record<string, PermissionCheck> = {
  'read:candidates': {
    action: 'read',
    resource: 'candidates',
    enforcement: 'both',
    description: 'View candidate profiles and lists',
  },
  'write:candidates': {
    action: 'write',
    resource: 'candidates',
    enforcement: 'both',
    description: 'Create and edit candidate records',
  },
  'delete:candidates': {
    action: 'delete',
    resource: 'candidates',
    enforcement: 'server',
    description: 'Delete candidate records',
  },
  'read:jobs': {
    action: 'read',
    resource: 'jobs',
    enforcement: 'both',
    description: 'View job listings',
  },
  'write:jobs': {
    action: 'write',
    resource: 'jobs',
    enforcement: 'both',
    description: 'Create and edit jobs',
  },
  'read:reports': {
    action: 'read',
    resource: 'reports',
    enforcement: 'client-only',
    description: 'View reports and dashboards',
  },
  'write:reports': {
    action: 'write',
    resource: 'reports',
    enforcement: 'client-only',
    description: 'Generate and export reports',
  },
  'read:analytics': {
    action: 'read',
    resource: 'analytics',
    enforcement: 'client-only',
    description: 'View analytics dashboards',
  },
  'read:team_performance': {
    action: 'read',
    resource: 'team_performance',
    enforcement: 'client-only',
    description: 'View team performance metrics',
  },
  'write:evaluations': {
    action: 'write',
    resource: 'evaluations',
    enforcement: 'both',
    description: 'Create and edit candidate evaluations',
  },
  'read:lia_insights': {
    action: 'read',
    resource: 'lia_insights',
    enforcement: 'client-only',
    description: 'View LIA AI insights',
  },
  'execute:lia_actions': {
    action: 'execute',
    resource: 'lia_actions',
    enforcement: 'both',
    description: 'Execute LIA AI actions',
  },
  'read:interviews': {
    action: 'read',
    resource: 'interviews',
    enforcement: 'both',
    description: 'View interview schedules',
  },
  'write:interviews': {
    action: 'write',
    resource: 'interviews',
    enforcement: 'both',
    description: 'Schedule and manage interviews',
  },
  'read:assessments': {
    action: 'read',
    resource: 'assessments',
    enforcement: 'both',
    description: 'View candidate assessments',
  },
  'write:assessments': {
    action: 'write',
    resource: 'assessments',
    enforcement: 'both',
    description: 'Create and edit assessments',
  },
  'read:references': {
    action: 'read',
    resource: 'references',
    enforcement: 'client-only',
    description: 'View reference checks',
  },
  'write:references': {
    action: 'write',
    resource: 'references',
    enforcement: 'client-only',
    description: 'Request and manage references',
  },
  'write:settings': {
    action: 'write',
    resource: 'settings',
    enforcement: 'both',
    description: 'Modify application settings',
  },
}

export function canPerform(action: PermissionAction, resource: PermissionResource): string {
  return `${action}:${resource}`
}

export function isAdmin(role: UserRole): boolean {
  return role === 'admin'
}

export function isManagerOrAbove(role: UserRole): boolean {
  return role === 'admin' || role === 'manager'
}

export function canManageUsers(role: UserRole): boolean {
  return role === 'admin' || role === 'manager'
}

export function canAccessAdmin(role: UserRole): boolean {
  return role === 'admin'
}

export function canAccessSettings(role: UserRole): boolean {
  return role === 'admin' || role === 'manager'
}

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  intern: 1,
  recruiter: 2,
  senior_recruiter: 3,
  manager: 4,
  admin: 5,
}

export function hasHigherRole(a: UserRole, b: UserRole): boolean {
  return ROLE_HIERARCHY[a] > ROLE_HIERARCHY[b]
}

export function getEnforcementStatus(action: PermissionAction, resource: PermissionResource): PermissionCheck['enforcement'] | 'unknown' {
  const key = canPerform(action, resource)
  return PERMISSION_CATALOG[key]?.enforcement ?? 'unknown'
}
