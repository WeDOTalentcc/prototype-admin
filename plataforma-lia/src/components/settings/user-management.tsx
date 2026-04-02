"use client"

import { useState, useMemo, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  X, Edit, Trash2, Save, User, Mail,
  Search, UserPlus,
  MapPin, Briefcase, Users, Shield, Loader2, Send, CheckCircle, Info, ExternalLink
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { useSCIMConfig } from '@/hooks/use-scim-config'
import { useCurrentCompany } from '@/hooks/use-current-company'

interface User {
  id: string
  name: string
  email: string
  phone: string
  whatsapp: string
  role: string
  department: string
  position: string
  avatar?: string
  status: 'ativo' | 'inativo' | 'pendente'
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
}

interface UserManagementProps {
  onUserUpdate?: (user: User) => void
}

export function UserManagement({ onUserUpdate }: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
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

  const { isSCIMEnabled, scimConfig } = useSCIMConfig()
  const { companyId } = useCurrentCompany()

  const fetchUsers = async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/backend-proxy/company/users?company_id=${companyId}`)
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
        // @ts-ignore TODO: fix type
        permissions: u.permissions && u.permissions.length > 0 ? u.permissions : 
          (u.role === 'admin' ? ['admin', 'recruitment', 'candidates', 'interviews', 'reports', 'settings', 'users', 'analytics'] : ['recruitment', 'candidates']),
        emailSignature: '',
        location: '',
        // @ts-ignore TODO: fix type
        hireDate: u.created_at?.split('T')[0] || '',
        isManager: u.role === 'admin',
        createdAt: u.created_at,
        updatedAt: u.updated_at,
        isScimManaged: u.is_scim_managed || false
      }))
      // @ts-ignore TODO: fix type
      setUsers(mappedUsers)
    } catch (err) {
      setError('Erro ao carregar usuários')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (companyId) {
      fetchUsers()
    }
  }, [companyId])

  // Formulário para criar/editar usuário
  const [formData, setFormData] = useState<Partial<User>>({
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
  })

  // Filtros e busca
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

  // Estatísticas
  const stats = useMemo(() => {
    const total = users.length
    const active = users.filter(u => u.status === 'ativo').length
    const managers = users.filter(u => u.isManager).length

    return { total, active, managers }
  }, [users])

  // Departamentos únicos
  const departments = useMemo(() => {
    const depts = [...new Set(users.map(u => u.department))]
    return depts
  }, [users])

  const handleCreateUser = () => {
    setIsCreating(true)
    setIsEditing(false)
    setSelectedUser(null)
    setFormData({
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
    })
  }

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    setIsEditing(true)
    setIsCreating(false)
    setFormData({ ...user })
  }

  const handleSaveUser = async () => {
    if (!companyId) {
      alert('Empresa não identificada. Recarregue a página.')
      return
    }
    try {
      if (isCreating) {
        const response = await fetch(`/api/backend-proxy/company/users?company_id=${companyId}`, {
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
        const response = await fetch(`/api/backend-proxy/company/users/${selectedUser.id}?company_id=${companyId}`, {
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
      alert(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao salvar usuário')
    }
  }

  const handleResendInvitation = async (userId: string, userEmail: string) => {
    if (!companyId) return
    setResendingInvite(userId)
    try {
      const response = await fetch(`/api/backend-proxy/company/users/${userId}/resend-invitation?company_id=${companyId}`, {
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
      alert(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao reenviar convite')
    } finally {
      setResendingInvite(null)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!companyId) return
    if (confirm('Tem certeza que deseja excluir este usuário?')) {
      try {
        const response = await fetch(`/api/backend-proxy/company/users/${userId}?company_id=${companyId}`, {
          method: 'DELETE'
        })
        if (!response.ok) throw new Error('Failed to delete user')
        await fetchUsers()
      } catch (err) {
        alert('Erro ao excluir usuário')
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ativo': return `${badgeStyles.success} border-status-success/30`
      case 'inativo': return `${badgeStyles.error} border-status-error/30`
      case 'pendente': return `${badgeStyles.warning} border-status-warning/30`
      default: return `${badgeStyles.default} border-lia-border-subtle`
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="text-xs text-lia-text-secondary">Carregando usuários...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-6 gap-3">
        <div className="text-xs text-status-error">{error}</div>
        <Button onClick={fetchUsers} size="sm">Tentar novamente</Button>
      </div>
    )
  }

  if (isCreating || isEditing) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className={textStyles.title}>
              {isCreating ? 'Novo Usuário' : 'Editar Usuário'}
            </h3>
            <p className={textStyles.description}>
              {isCreating ? 'Cadastre um novo recrutador na plataforma' : 'Atualize as informações do usuário'}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setIsCreating(false)
              setIsEditing(false)
              setSelectedUser(null)
            }}
          >
            <X className="w-3.5 h-3.5 mr-1.5" />
            Cancelar
          </Button>
        </div>

        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Dados Pessoais */}
              <div className="space-y-3">
                <h4 className={`${textStyles.title} flex items-center gap-2`}>
                  <User className="w-3.5 h-3.5" />
                  Dados Pessoais
                </h4>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Nome Completo</label>
                  <input
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="Ex: Ana Silva"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Email</label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="ana.silva@empresa.com"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Telefone</label>
                  <input
                    type="tel"
                    value={formData.phone || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="+55 11 99999-9999"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>WhatsApp</label>
                  <input
                    type="tel"
                    value={formData.whatsapp || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, whatsapp: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="+55 11 99999-9999"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Localização</label>
                  <input
                    type="text"
                    value={formData.location || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="São Paulo, SP"
                  />
                </div>
              </div>

              {/* Dados Profissionais */}
              <div className="space-y-3">
                <h4 className={`${textStyles.title} flex items-center gap-2`}>
                  <Briefcase className="w-3.5 h-3.5" />
                  Dados Profissionais
                </h4>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Cargo/Função</label>
                  <input
                    type="text"
                    value={formData.role || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="Ex: Recrutadora Sênior"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Departamento</label>
                  <select
                    value={formData.department || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                  >
                    <option value="">Selecione...</option>
                    <option value="Talent Acquisition">Talent Acquisition</option>
                    <option value="RH">Recursos Humanos</option>
                    <option value="Operações">Operações</option>
                    <option value="Tecnologia">Tecnologia</option>
                  </select>
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Posição</label>
                  <input
                    type="text"
                    value={formData.position || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, position: e.target.value }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                    placeholder="Senior Recruiter"
                  />
                </div>

                <div>
                  <label className={textStyles.label + " block mb-1.5"}>Status</label>
                  <select
                    value={formData.status || 'ativo'}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as typeof prev.status }))}
                    className="w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900"
                  >
                    <option value="ativo">Ativo</option>
                    <option value="inativo">Inativo</option>
                    <option value="pendente">Pendente</option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.isManager || false}
                      onChange={(e) => setFormData(prev => ({ ...prev, isManager: e.target.checked }))}
                      className="w-3.5 h-3.5 rounded-md border-lia-border-default"
                    />
                    <span className={textStyles.label}>É Gestor</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Permissões */}
            <div className="mt-4">
              <h4 className={`${textStyles.title} flex items-center gap-2 mb-3`}>
                <Shield className="w-3.5 h-3.5" />
                Permissões
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {[
                  { id: 'recruitment', label: 'Recrutamento' },
                  { id: 'candidates', label: 'Candidatos' },
                  { id: 'interviews', label: 'Entrevistas' },
                  { id: 'reports', label: 'Relatórios' },
                  { id: 'settings', label: 'Configurações' },
                  { id: 'users', label: 'Usuários' },
                  { id: 'admin', label: 'Administrador' },
                  { id: 'analytics', label: 'Analytics' }
                ].map((permission) => (
                  <label key={permission.id} className="flex items-center gap-1.5">
                    <input
                      type="checkbox"
                      checked={(formData.permissions || []).includes(permission.id)}
                      onChange={(e) => {
                        const permissions = formData.permissions || []
                        if (e.target.checked) {
                          setFormData(prev => ({ ...prev, permissions: [...permissions, permission.id] }))
                        } else {
                          setFormData(prev => ({ ...prev, permissions: permissions.filter(p => p !== permission.id) }))
                        }
                      }}
                      className="w-3.5 h-3.5 rounded-md border-lia-border-default"
                    />
                    <span className={textStyles.label}>{permission.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsCreating(false)
                  setIsEditing(false)
                  setSelectedUser(null)
                }}
              >
                Cancelar
              </Button>
              <Button onClick={handleSaveUser} size="sm" className="gap-1.5">
                <Save className="w-3.5 h-3.5" />
                {isCreating ? 'Criar Usuário' : 'Salvar Alterações'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* SCIM/SSO Banner */}
      {isSCIMEnabled && (
        <Card className="border-wedo-cyan/30 dark:border-wedo-cyan/30">
          <CardContent className="p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-wedo-cyan-dark dark:text-wedo-cyan-dark flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className={textStyles.subtitle}>
                Provisionamento automático ativo via {scimConfig?.directoryName || 'SSO Enterprise'}
              </p>
              <p className={textStyles.description + " mt-1"}>
                Os usuários são gerenciados automaticamente pelo seu provedor de identidade corporativo.
                Adicione ou remova usuários diretamente no Azure AD, Okta ou Google Workspace.
              </p>
            </div>
            <a
              href="https://workos.com/docs/directory-sync"
              target="_blank"
              rel="noopener noreferrer"
              className="text-wedo-cyan-dark dark:text-wedo-cyan-dark hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan-dark flex items-center gap-1 text-xs flex-shrink-0"
            >
              <ExternalLink className="w-3 h-3" />
              Saiba mais
            </a>
          </CardContent>
        </Card>
      )}

      {/* Success Message */}
      {successMessage && (
        <Card className="border-status-success/30 dark:border-status-success/30">
          <CardContent className="p-3 flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-status-success dark:text-status-success flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className={textStyles.subtitle}>{successMessage}</p>
            </div>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-status-success dark:text-status-success hover:text-status-success dark:hover:text-status-success"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.h3}>Gestão de Usuários</h3>
          <p className={textStyles.description}>
            {isSCIMEnabled 
              ? 'Usuários sincronizados automaticamente via provedor de identidade'
              : 'Cadastro e gestão dos recrutadores da plataforma'
            }
          </p>
        </div>
        {!isSCIMEnabled && (
          <Button onClick={handleCreateUser} size="sm" className="gap-1.5">
            <UserPlus className="w-3.5 h-3.5" />
            Novo Usuário
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className={textStyles.metricLarge}>{stats.total}</div>
            <div className={textStyles.description}>Total de Usuários</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-status-success dark:text-status-success">{stats.active}</div>
            <div className={textStyles.description}>Usuários Ativos</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-wedo-purple dark:text-wedo-purple">{stats.managers}</div>
            <div className={textStyles.description}>Gestores</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 transform -translate-y-1/2 text-lia-text-secondary" />
          <input
            type="text"
            placeholder="Buscar usuários..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-lia-border-default rounded-md focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900 dark:bg-lia-bg-elevated dark:border-lia-border-default"
          />
        </div>

        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-md focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900 dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">Todos os Departamentos</option>
          {departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-md focus:ring-1 focus:ring-gray-900/10 focus:border-gray-900 dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">Todos os Status</option>
          <option value="ativo">Ativo</option>
          <option value="inativo">Inativo</option>
          <option value="pendente">Pendente</option>
        </select>

        <div className="flex bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-0.5">
          <button
            onClick={() => setViewMode('cards')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors motion-reduce:transition-none ${
              viewMode === 'cards'
                ? 'bg-lia-bg-primary text-lia-text-primary'
                : 'text-lia-text-secondary hover:text-lia-text-primary'
            }`}
          >
            Cards
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors motion-reduce:transition-none ${
              viewMode === 'table'
                ? 'bg-lia-bg-primary text-lia-text-primary'
                : 'text-lia-text-secondary hover:text-lia-text-primary'
            }`}
          >
            Tabela
          </button>
        </div>
      </div>

      {/* Users List */}
      {viewMode === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredUsers.map((user) => (
            <Card key={user.id} className="rounded-md hover:transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={user.avatar} alt={user.name} />
                      <AvatarFallback className={`${badgeStyles.info} font-medium text-xs`}>
                        {user.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h4 className={textStyles.subtitle}>{user.name}</h4>
                      <p className={textStyles.description}>{user.role}</p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <Badge className={`text-micro ${getStatusColor(user.status)}`}>
                          {user.status}
                        </Badge>
                        {user.isScimManaged && (
                          <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                            <Shield className="w-2.5 h-2.5 mr-0.5" />
                            SSO
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  {!isSCIMEnabled && (
                    <div className="flex items-center gap-0.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditUser(user)}
                        className="h-7 w-7 p-0"
                        title="Editar"
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteUser(user.id)}
                        className="h-7 w-7 p-0 text-status-error dark:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/30"
                        title="Excluir"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-3 text-micro text-lia-text-secondary">
                    <span className="flex items-center gap-1">
                      <Mail className="w-3 h-3" />
                      {user.email}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {user.location}
                    </span>
                  </div>

                  {user.isManager && (
                    <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                      <Users className="w-3 h-3 mr-1" />
                      Gestor
                    </Badge>
                  )}

                  {user.status === 'inativo' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleResendInvitation(user.id, user.email)}
                      disabled={resendingInvite === user.id}
                      className="w-full mt-1.5 text-micro gap-1.5 h-7"
                    >
                      {resendingInvite === user.id ? (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                          Enviando...
                        </>
                      ) : (
                        <>
                          <Send className="w-3 h-3" />
                          Reenviar Convite
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="rounded-md">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-lia-bg-secondary">
                  <tr>
                    <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                      Usuário
                    </th>
                    <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                      Cargo
                    </th>
                    <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                      Status
                    </th>
                    {!isSCIMEnabled && (
                      <th className="px-2 py-2.5 text-center text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                        Ações
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-lia-bg-secondary divide-y divide-gray-200 dark:lia-divide-700">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-2 py-1.5 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Avatar className="w-8 h-8">
                            <AvatarImage src={user.avatar} alt={user.name} />
                            <AvatarFallback className={`${badgeStyles.info} font-medium text-micro`}>
                              {user.name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className={textStyles.subtitle}>{user.name}</div>
                            <div className={textStyles.description}>{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap">
                        <div className={textStyles.subtitle}>{user.role}</div>
                        <div className={textStyles.description}>{user.department}</div>
                      </td>
                      <td className="px-2 py-1.5 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Badge className={`${getStatusColor(user.status)} text-micro`}>
                            {user.status}
                          </Badge>
                          {user.isScimManaged && (
                            <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                              <Shield className="w-2.5 h-2.5 mr-0.5" />
                              SSO
                            </Badge>
                          )}
                        </div>
                      </td>
                      {!isSCIMEnabled && (
                        <td className="px-2 py-1.5 whitespace-nowrap text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditUser(user)}
                              className="h-7 w-7 p-0"
                              title="Editar"
                            >
                              <Edit className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteUser(user.id)}
                              className="h-7 w-7 p-0 text-status-error dark:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/30"
                              title="Excluir"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {filteredUsers.length === 0 && (
        <Card className="rounded-md">
          <CardContent className="p-4 text-center">
            <div className="text-lia-text-secondary">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-50" />
              <h3 className={textStyles.subtitle}>Nenhum usuário encontrado</h3>
              <p className={textStyles.description + " mt-1"}>Ajuste os filtros ou crie um novo usuário</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
