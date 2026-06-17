export interface CompanyUser {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  active_jobs_count: number
  performance_score: number
}

export interface CompanyUsersResponse {
  users: CompanyUser[]
  total: number
}

// =============================================
// EMAIL TEMPLATES TYPES
// =============================================
