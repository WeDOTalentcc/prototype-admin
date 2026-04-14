"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { useSCIMConfig } from '@/hooks/company/use-scim-config'
import { useCurrentCompany } from '@/hooks/company/use-current-company'
import { badgeStyles } from '@/lib/design-tokens'
import type { UserData } from './user-management-types'

function mapRoleToApi(role?: string): string {
  if (!role) return 'viewer'
  const lower = role.toLowerCase()
  if (lower === 'admin' || lower.includes('admin')) return 'admin'
  if (lower === 'manager' || lower.includes('gestor') || lower.includes('manager')) return 'manager'
  if (lower === 'recruiter' || lower.includes('recrut') || lower.includes('recruit')) return 'recruiter'
  return 'viewer'
}

const EMPTY_FORM: Partial<UserData> = {
  name: '',
  email: '',
  phone: '',
  whatsapp: '',
  role: '',
  department: '',
  position: '',
  emailSignature: '',
  location: '',
  permissions: [],
  status: 'active'
}

export function useUserManagement() {
  const t = useTranslations("settings")
  const [users, setUsers] = useState<UserData[]>([])
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [resendingInvite, setResendingInvite] = useState<string | null>(null)
  const [formData, setFormData] = useState<Partial<UserData>>(EMPTY_FORM)

  const { isSCIMEnabled, scimConfig } = useSCIMConfig()
  const { companyId, tenantId } = useCurrentCompany()
  const effectiveCompanyId = tenantId || companyId

  const fetchUsers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const cid = effectiveCompanyId || 'demo_company'
      const response = await fetch(`/api/backend-proxy/company/users?company_id=${cid}`)
      if (!response.ok) throw new Error('Failed to fetch users')
      const data = await response.json()
      const usersData = Array.isArray(data) ? data : (data.data || data.users || [])
      const mappedUsers = (Array.isArray(usersData) ? usersData : []).map((u: Record<string, unknown>) => ({
        id: u.id,
        name: u.name || '',
        email: u.email || '',
        phone: '',
        whatsapp: '',
        role: u.role === 'admin' ? t('users.roleAdmin') : u.role === 'recruiter' ? t('users.roleRecruiter') : u.role === 'manager' ? t('users.roleManager') : t('users.roleViewer'),
        department: 'Talent Acquisition',
        position: u.role,
        status: u.status === 'active' || !u.status ? 'active' : u.status === 'inactive' ? 'inactive' : 'pending',
        permissions: Array.isArray(u.permissions) && (u.permissions as unknown[]).length > 0 ? u.permissions as string[] : [],
        emailSignature: '',
        location: '',
        hireDate: (u.created_at as string)?.split('T')[0] || '',
        isManager: u.role === 'admin',
        createdAt: u.created_at,
        updatedAt: u.updated_at,
        isScimManaged: u.is_scim_managed || false
      }))
      setUsers(mappedUsers as UserData[])
    } catch {
      setError(t('users.errorLoadUsers'))
    } finally {
      setIsLoading(false)
    }
  }, [effectiveCompanyId, t])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      const matchesSearch = searchTerm === '' ||
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.role.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesDepartment = departmentFilter === 'all' || user.department === departmentFilter
      const matchesStatus = statusFilter === 'all' || user.status === statusFilter
      return matchesSearch && matchesDepartment && matchesStatus
    })
  }, [users, searchTerm, departmentFilter, statusFilter])

  const stats = useMemo(() => {
    const total = users.length
    const active = users.filter(u => u.status === 'active').length
    const managers = users.filter(u => u.isManager).length
    return { total, active, managers }
  }, [users])

  const departments = useMemo(() => {
    return [...new Set(users.map(u => u.department))]
  }, [users])

  const handleCreateUser = useCallback(() => {
    setIsCreating(true)
    setIsEditing(false)
    setSelectedUser(null)
    setFormData(EMPTY_FORM)
  }, [])

  const handleEditUser = useCallback((user: UserData) => {
    setSelectedUser(user)
    setIsEditing(true)
    setIsCreating(false)
    setFormData({ ...user })
  }, [])

  const handleCancelForm = useCallback(() => {
    setIsCreating(false)
    setIsEditing(false)
    setSelectedUser(null)
  }, [])

  const handleSaveUser = useCallback(async () => {
    const cid = effectiveCompanyId || 'demo_company'
    try {
      if (isCreating) {
        const response = await fetch(`/api/backend-proxy/company/users?company_id=${cid}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            name: formData.name,
            role: mapRoleToApi(formData.role),
            permissions: formData.permissions || []
          })
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || error.details?.detail || 'Failed to create user')
        }
        await fetchUsers()
        setSuccessMessage(t('users.userCreatedSuccess', { email: formData.email || '' }))
        setTimeout(() => setSuccessMessage(null), 8000)
      } else if (selectedUser) {
        const response = await fetch(`/api/backend-proxy/company/users/${selectedUser.id}?company_id=${cid}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.name,
            role: mapRoleToApi(formData.role),
            status: formData.status === 'active' ? 'active' : 'inactive',
            permissions: formData.permissions || []
          })
        })
        if (!response.ok) throw new Error('Failed to update user')
        await fetchUsers()
      }
      setIsCreating(false)
      setIsEditing(false)
      setSelectedUser(null)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : t('users.errorSaveUser'))
    }
  }, [effectiveCompanyId, isCreating, formData, selectedUser, fetchUsers, t])

  const handleResendInvitation = useCallback(async (userId: string, userEmail: string) => {
    const cid = effectiveCompanyId || 'demo_company'
    setResendingInvite(userId)
    try {
      const response = await fetch(`/api/backend-proxy/company/users/${userId}/resend-invitation?company_id=${cid}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || error.details?.detail || 'Failed to resend invitation')
      }
      setSuccessMessage(t('users.inviteResentSuccess', { email: userEmail }))
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : t('users.errorResendInvite'))
    } finally {
      setResendingInvite(null)
    }
  }, [effectiveCompanyId, t])

  const handleDeleteUser = useCallback(async (userId: string) => {
    const cid = effectiveCompanyId || 'demo_company'
    if (confirm(t('users.confirmDeleteUser'))) {
      try {
        const response = await fetch(`/api/backend-proxy/company/users/${userId}?company_id=${cid}`, {
          method: 'DELETE'
        })
        if (!response.ok) throw new Error('Failed to delete user')
        await fetchUsers()
      } catch {
        alert(t('users.errorDeleteUser'))
      }
    }
  }, [effectiveCompanyId, fetchUsers, t])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'active': return `${badgeStyles.success} border-status-success/30`
      case 'inactive': return `${badgeStyles.error} border-status-error/30`
      case 'pending': return `${badgeStyles.warning} border-status-warning/30`
      default: return `${badgeStyles.default} border-lia-border-subtle`
    }
  }, [])

  return {
    users,
    filteredUsers,
    selectedUser,
    isCreating,
    isEditing,
    searchTerm,
    setSearchTerm,
    departmentFilter,
    setDepartmentFilter,
    statusFilter,
    setStatusFilter,
    viewMode,
    setViewMode,
    isLoading,
    error,
    successMessage,
    setSuccessMessage,
    resendingInvite,
    formData,
    setFormData,
    stats,
    departments,
    isSCIMEnabled,
    scimConfig,
    fetchUsers,
    handleCreateUser,
    handleEditUser,
    handleCancelForm,
    handleSaveUser,
    handleResendInvitation,
    handleDeleteUser,
    getStatusColor,
  }
}
