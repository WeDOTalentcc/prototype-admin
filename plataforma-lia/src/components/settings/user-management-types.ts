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
}

import type { DepartmentItem } from "@/hooks/settings/useDepartmentsList"

export interface UserManagementProps {
  onUserUpdate?: (user: UserData) => void
  // Bug 2 fix (2026-05-25): departments lifted to UsuariosDepartamentosHub (single SoT).
  departments?: DepartmentItem[]
  onDepartmentChanged?: () => void | Promise<void>
}
