"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { useSCIMConfig } from '@/hooks/company/use-scim-config'
import { useCurrentCompany } from '@/hooks/company/use-current-company'
import { badgeStyles } from '@/lib/design-tokens'
import type { UserData } from './user-management-types'

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
  status: 'ativo'
}

export function useUserManagement() {
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
    if (!effectiveCompanyId) return
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/backend-proxy/company/users?company_id=${effectiveCompanyId}`)
      if (!response.ok) throw new Error('Failed to fetch users')
      const data = await response.json()
      const usersData = data.data || data.users || data || []
      const mappedUsers = (Array.isArray(usersData) ? usersData : []).map((u: Record<string, unknown>) => ({
        id: u.id,
        name: u.name || '',
        email: u.email || '',
        phone: '',
        whatsapp: '',
        role: u.role === 'admin' ? 'Administrador' : u.role === 'recruiter' ? 'Recrutador' : u.role === 'manager' ? 'Gestor' : 'Visualizador',
        department: 'Talent Acquisition',
        position: u.role,
        status: u.status === 'active' ? 'ativo' : u.status === 'inactive' ? 'inativo' : 'pendente',
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
      setError('Erro ao carregar usuários')
    } finally {
      setIsLoading(false)
    }
  }, [effectiveCompanyId])

  useEffect(() => {
    if (effectiveCompanyId) {
      fetchUsers()
    }
  }, [effectiveCompanyId, fetchUsers])

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
    const active = users.filter(u => u.status === 'ativo').length
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
    if (!effectiveCompanyId) {
      alert('Empresa não identificada. Recarregue a página.')
      return
    }
    try {
      if (isCreating) {
        const response = await fetch(`/api/backend-proxy/company/users?company_id=${effectiveCompanyId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            name: formData.name,
            role: formData.role?.toLowerCase().includes('admin') ? 'admin' : 
                  formData.role?.toLowerCase().includes('gestor') ? 'manager' :
                  formData.role?.toLowerCase().includes('recrutador') ? 'recruiter' : 'viewer',
            permissions: formData.permissions || []
          })
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || error.details?.detail || 'Failed to create user')
        }
        await fetchUsers()
        setSuccessMessage(`Usuário criado com sucesso! Um email de convite foi enviado para ${formData.email} com instruções para ativar a conta.`)
        setTimeout(() => setSuccessMessage(null), 8000)
      } else if (selectedUser) {
        const response = await fetch(`/api/backend-proxy/company/users/${selectedUser.id}?company_id=${effectiveCompanyId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.name,
            role: formData.role?.toLowerCase().includes('admin') ? 'admin' : 
                  formData.role?.toLowerCase().includes('gestor') ? 'manager' :
                  formData.role?.toLowerCase().includes('recrutador') ? 'recruiter' : 'viewer',
            status: formData.status === 'ativo' ? 'active' : 'inactive',
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
      alert(err instanceof Error ? err.message : 'Erro ao salvar usuário')
    }
  }, [effectiveCompanyId, isCreating, formData, selectedUser, fetchUsers])

  const handleResendInvitation = useCallback(async (userId: string, userEmail: string) => {
    if (!effectiveCompanyId) return
    setResendingInvite(userId)
    try {
      const response = await fetch(`/api/backend-proxy/company/users/${userId}/resend-invitation?company_id=${effectiveCompanyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || error.details?.detail || 'Failed to resend invitation')
      }
      setSuccessMessage(`Convite reenviado com sucesso para ${userEmail}!`)
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Erro ao reenviar convite')
    } finally {
      setResendingInvite(null)
    }
  }, [effectiveCompanyId])

  const handleDeleteUser = useCallback(async (userId: string) => {
    if (!effectiveCompanyId) return
    if (confirm('Tem certeza que deseja excluir este usuário?')) {
      try {
        const response = await fetch(`/api/backend-proxy/company/users/${userId}?company_id=${effectiveCompanyId}`, {
          method: 'DELETE'
        })
        if (!response.ok) throw new Error('Failed to delete user')
        await fetchUsers()
      } catch {
        alert('Erro ao excluir usuário')
      }
    }
  }, [effectiveCompanyId, fetchUsers])

  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'ativo': return `${badgeStyles.success} border-status-success/30`
      case 'inativo': return `${badgeStyles.error} border-status-error/30`
      case 'pendente': return `${badgeStyles.warning} border-status-warning/30`
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
