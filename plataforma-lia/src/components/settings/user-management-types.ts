export interface UserData {
  id: string
  name: string
  email: string
  phone: string
  whatsapp: string
  role: string
  department: string
  position: string
  avatar?: string
  status: 'active' | 'inactive' | 'pending'
  permissions: string[]
  emailSignature: string
  location: string
  hireDate: string
  isManager: boolean
  managerId?: string
  teamMembers?: string[]
  lastLogin?: string
  createdAt: string
  updatedAt: string
  isScimManaged?: boolean
  // Sprint 2 RBAC (2026-05-25): department FK (UUID) — alongside legacy `department` (name string)
  department_id?: string | null
  // Sprint 5.5 RBAC (2026-05-25): financial PII grant (LGPD Art. 6 III)
  can_view_salary?: boolean
  // Sprint 8 RBAC (2026-05-26): sensitive PII grant (LGPD Art. 5 II)
  // Cobre CPF + DoB + endereço + secondary contacts. Default true (opt-out).
  can_view_sensitive_pii?: boolean
  // A6-FE-1 (2026-06-06): per-user PII field-level override. Omitted = inherit role default.
  pii_field_visibility?: PiiFieldVisibility
}

import type { DepartmentItem } from "@/hooks/settings/useDepartmentsList"

export interface UserManagementProps {
  onUserUpdate?: (user: UserData) => void
  // Bug 2 fix (2026-05-25): departments lifted to UsuariosDepartamentosHub (single SoT).
  departments?: DepartmentItem[]
  onDepartmentChanged?: () => void | Promise<void>
}

// PII field-level visibility (2026-06-06). Mirror of app/shared/rbac/pii_field_catalog.py.
export const PII_SALARY_FIELDS = [
  "current_salary", "desired_salary_min", "desired_salary_max",
  "salary_expectation_clt", "salary_expectation_pj", "salary_expectation_freelance",
] as const

export const PII_SENSITIVE_FIELDS = [
  "cpf", "date_of_birth", "address_street", "address_number", "address_zip",
  "address_complement", "secondary_email", "secondary_phone", "personal_emails",
  "business_emails", "best_personal_email", "best_business_email",
] as const

export const PII_GATEABLE_FIELDS = [...PII_SALARY_FIELDS, ...PII_SENSITIVE_FIELDS] as const
export type PiiField = (typeof PII_GATEABLE_FIELDS)[number]
// Per-user override: partial map. Omitted field = inherit (role default -> legacy -> show).
export type PiiFieldVisibility = Partial<Record<PiiField, boolean>>
// Per-role defaults: {role: {field: bool}}
export type PiiVisibilityDefaults = Record<string, PiiFieldVisibility>
