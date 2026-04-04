"use client"

import { useState, useEffect, useCallback } from 'react'

export interface Manager {
  id: string
  name: string
  email: string
  role: string
  department?: string
  departmentId?: string
  isActive: boolean
  canApprove: boolean
  avatarUrl?: string
}

interface UseCompanyManagersOptions {
  department?: string
  activeOnly?: boolean
}

interface UseCompanyManagersResult {
  managers: Manager[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getManagersByDepartment: (departmentId: string) => Manager[]
  getApprovers: () => Manager[]
  searchManagers: (query: string) => Manager[]
}

export function useCompanyManagers(options: UseCompanyManagersOptions = {}): UseCompanyManagersResult {
  const [managers, setManagers] = useState<Manager[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchManagers = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Fetch both users and approvers
      const [usersRes, approversRes] = await Promise.all([
        fetch('/api/backend-proxy/company/users'),
        fetch('/api/backend-proxy/company/approvers')
      ])
      
      const approverIds = new Set<string>()
      
      if (approversRes.ok) {
        const approversData = await approversRes.json()
        const approvers = Array.isArray(approversData) ? approversData : approversData.items || []
        approvers.forEach((a: Record<string, unknown>) => {
          if (a.user_id) approverIds.add(String(a.user_id))
        })
      }

      if (!usersRes.ok) {
        if (usersRes.status === 404) {
          setManagers([])
          return
        }
        throw new Error(`Failed to fetch users: ${usersRes.status}`)
      }

      const data = await usersRes.json()
      const users = Array.isArray(data) ? data : data.items || []
      
      // Filter to only managers (those with manager/coordinator/director roles)
      const managerRoles = ['manager', 'gerente', 'director', 'diretor', 'coordinator', 'coordenador', 'lead', 'líder', 'head', 'supervisor', 'admin']
      
      const managersList: Manager[] = users
        .filter((user: Record<string, unknown>) => {
          if (!user.is_active && options.activeOnly !== false) return false
          
          const role = String(user.role || '').toLowerCase()
          const hasManagerRole = managerRoles.some(mr => role.includes(mr))
          
          const isApprover = approverIds.has(String(user.id))
          
          return hasManagerRole || isApprover
        })
        .map((user: Record<string, unknown>) => ({
          id: user.id,
          name: user.name || user.full_name || user.email,
          email: user.email,
          role: user.role || 'Manager',
          department: user.department_name || user.department,
          departmentId: user.department_id,
          isActive: user.is_active ?? true,
          canApprove: approverIds.has(String(user.id)),
          avatarUrl: user.avatar_url
        }))

      setManagers(managersList)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setManagers([])
    } finally {
      setIsLoading(false)
    }
  }, [options.activeOnly])

  useEffect(() => {
    fetchManagers()
  }, [fetchManagers])

  const getManagersByDepartment = useCallback((departmentId: string): Manager[] => {
    return managers.filter(m => {
      if (!m.isActive) return false
      if (!m.departmentId && !m.department) return false
      
      const deptLower = departmentId.toLowerCase()
      return (
        m.departmentId?.toLowerCase() === deptLower ||
        m.department?.toLowerCase().includes(deptLower) ||
        deptLower.includes(m.department?.toLowerCase() || '')
      )
    })
  }, [managers])

  const getApprovers = useCallback((): Manager[] => {
    return managers.filter(m => m.isActive && m.canApprove)
  }, [managers])

  const searchManagers = useCallback((query: string): Manager[] => {
    if (!query.trim()) return managers.filter(m => m.isActive)
    
    const queryLower = query.toLowerCase()
    return managers.filter(m => {
      if (!m.isActive) return false
      return (
        m.name.toLowerCase().includes(queryLower) ||
        m.email.toLowerCase().includes(queryLower) ||
        (m.department && m.department.toLowerCase().includes(queryLower)) ||
        m.role.toLowerCase().includes(queryLower)
      )
    })
  }, [managers])

  // Apply department filter if provided
  const filteredManagers = options.department
    ? managers.filter(m => {
        const deptLower = options.department!.toLowerCase()
        return (
          m.departmentId?.toLowerCase() === deptLower ||
          m.department?.toLowerCase().includes(deptLower)
        )
      })
    : managers

  return {
    managers: filteredManagers,
    isLoading,
    error,
    refetch: fetchManagers,
    getManagersByDepartment,
    getApprovers,
    searchManagers
  }
}

export default useCompanyManagers
