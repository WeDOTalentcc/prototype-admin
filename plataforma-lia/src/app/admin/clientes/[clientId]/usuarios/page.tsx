"use client"

import React, { use, useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import {
  Users,
  Plus,
  Search,
  MoreHorizontal,
  Mail,
  Shield,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  RefreshCw,
  Pencil,
  Trash2,
  Send,
  AlertCircle,
  UserX,
  Filter,
  Info,
  ExternalLink
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'manager' | 'recruiter' | 'viewer'
  status: 'active' | 'pending' | 'inactive'
  lastLogin?: string
  createdAt: string
  is_scim_managed?: boolean
}

const roleLabels: Record<string, { label: string, color: string }> = {
  admin: { label: 'Administrador', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  manager: { label: 'Gestor', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' },
 recruiter: { label: 'Recrutador', color: 'bg-gray-100 text-gray-900 dark:text-gray-300' },
  viewer: { label: 'Visualizador', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' }
}

const statusConfig: Record<string, { label: string, icon: React.ComponentType<{ className?: string }>, variant: 'success' | 'warning' | 'default' }> = {
  active: { label: 'Ativo', icon: CheckCircle2, variant: 'success' },
  pending: { label: 'Pendente', icon: Clock, variant: 'warning' },
  inactive: { label: 'Inativo', icon: XCircle, variant: 'default' }
}


function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-3 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
          <Skeleton className="w-10 h-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-56" />
          </div>
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
          <div className="text-right space-y-1">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="w-8 h-8 rounded" />
        </div>
      ))}
    </div>
  )
}

export default function ClientUsuariosPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showDeactivateModal, setShowDeactivateModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    role: 'recruiter' as User['role']
  })
  const [editForm, setEditForm] = useState({
    name: '',
    email: '',
    role: 'recruiter' as User['role']
  })
  const [isScimEnabled, setIsScimEnabled] = useState(false)
  const [scimDirectoryName, setScimDirectoryName] = useState<string | null>(null)

  const checkScimStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/workos-config`)
      if (response.ok) {
        const data = await response.json()
        if (data.scim_enabled || data.directory_id) {
          setIsScimEnabled(true)
          setScimDirectoryName(data.directory_name || 'SSO Enterprise')
        }
      }
    } catch (err) {
      console.log('SCIM config not available')
    }
  }, [clientId])

  const loadUsers = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users`)
      if (response.ok) {
        const data = await response.json()
        if (data.users || data.data) {
          setUsers(data.users || data.data)
        } else if (Array.isArray(data)) {
          setUsers(data)
        } else {
          setUsers([])
        }
      } else {
        setUsers([])
        toast.error('Erro ao carregar usuários. Tente novamente.')
      }
    } catch (err) {
      console.error('Erro ao carregar usuários:', err)
      setUsers([])
      toast.error('Erro ao carregar usuários. Verifique sua conexão.')
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    loadUsers()
    checkScimStatus()
  }, [loadUsers, checkScimStatus])

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesRole = roleFilter === 'all' || user.role === roleFilter
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter
    return matchesSearch && matchesRole && matchesStatus
  })

  const handleAddUser = async () => {
    if (!newUser.name || !newUser.email) {
      toast.error('Preencha todos os campos obrigatórios')
      return
    }

    setIsSaving(true)
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newUser.name,
          email: newUser.email,
          role: newUser.role
        })
      })

      if (response.ok) {
        toast.success('Convite enviado com sucesso!')
        setShowAddModal(false)
        setNewUser({ name: '', email: '', role: 'recruiter' })
        loadUsers()
      } else {
        const error = await response.json()
        toast.error(error.message || 'Erro ao convidar usuário')
      }
    } catch (err) {
      toast.error('Erro ao convidar usuário')
    } finally {
      setIsSaving(false)
    }
  }

  const handleEditUser = async () => {
    if (!selectedUser) return
    if (!editForm.name || !editForm.email) {
      toast.error('Preencha todos os campos obrigatórios')
      return
    }

    setIsSaving(true)
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editForm.name,
          email: editForm.email,
          role: editForm.role
        })
      })

      if (response.ok) {
        toast.success('Usuário atualizado com sucesso!')
        setShowEditModal(false)
        setSelectedUser(null)
        loadUsers()
      } else {
        const error = await response.json()
        toast.error(error.message || 'Erro ao atualizar usuário')
      }
    } catch (err) {
      toast.error('Erro ao atualizar usuário')
    } finally {
      setIsSaving(false)
    }
  }

  const handleUpdateRole = async (userId: string, newRole: User['role']) => {
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      })

      if (response.ok) {
        toast.success('Permissão atualizada!')
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u))
      } else {
        toast.error('Erro ao atualizar permissão')
      }
    } catch (err) {
      toast.error('Erro ao atualizar permissão')
    }
  }

  const handleDeactivateUser = async () => {
    if (!selectedUser) return

    setIsSaving(true)
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'inactive' })
      })

      if (response.ok) {
        toast.success('Usuário desativado com sucesso')
        setShowDeactivateModal(false)
        setSelectedUser(null)
        loadUsers()
      } else {
        toast.error('Erro ao desativar usuário')
      }
    } catch (err) {
      toast.error('Erro ao desativar usuário')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return

    setIsSaving(true)
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users/${selectedUser.id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Usuário removido com sucesso')
        setShowDeleteModal(false)
        setSelectedUser(null)
        loadUsers()
      } else {
        toast.error('Erro ao remover usuário')
      }
    } catch (err) {
      toast.error('Erro ao remover usuário')
    } finally {
      setIsSaving(false)
    }
  }

  const handleResendInvite = async (userId: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resend_invitation: true })
      })

      if (response.ok) {
        toast.success('Convite reenviado!')
      } else {
        toast.error('Erro ao reenviar convite')
      }
    } catch (err) {
      toast.error('Erro ao reenviar convite')
    }
  }

  const openEditModal = (user: User) => {
    setSelectedUser(user)
    setEditForm({
      name: user.name,
      email: user.email,
      role: user.role
    })
    setShowEditModal(true)
  }

  const formatDateTime = (dateStr: string | undefined) => {
    if (!dateStr) return 'Nunca'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const activeCount = users.filter(u => u.status === 'active').length
  const pendingCount = users.filter(u => u.status === 'pending').length
  const inactiveCount = users.filter(u => u.status === 'inactive').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Usuários
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Gestão de usuários e permissões do cliente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadUsers} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          {!isScimEnabled && (
            <Button 
              size="sm" 
              onClick={() => setShowAddModal(true)}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Convidar Usuário
            </Button>
          )}
        </div>
      </div>

      {isScimEnabled && (
        <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-900/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-md bg-purple-100 dark:bg-purple-800/50">
                <Shield className="w-5 h-5 text-purple-600 dark:text-purple-300" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-purple-900 dark:text-purple-100 mb-1">
                  Usuários gerenciados via SSO/SCIM
                </h4>
                <p className="text-sm text-purple-700 dark:text-purple-300 mb-2">
                  Este cliente possui provisionamento automático de usuários via {scimDirectoryName}. 
                  Para adicionar, editar ou remover usuários, utilize o portal do provedor de identidade (IdP).
                </p>
                <div className="flex items-center gap-2 text-xs text-purple-600 dark:text-purple-400">
                  <Info className="w-3.5 h-3.5" />
                  <span>Alterações no IdP são sincronizadas automaticamente com a plataforma</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
              {users.length}
            </p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Total de Usuários
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-emerald-600">{activeCount}</p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Ativos
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-amber-500">{pendingCount}</p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Pendentes
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-gray-400">{inactiveCount}</p>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Inativos
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
              Lista de Usuários
            </CardTitle>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-[140px] h-9">
                    <SelectValue placeholder="Role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas Roles</SelectItem>
                    <SelectItem value="admin">Administrador</SelectItem>
                    <SelectItem value="manager">Gestor</SelectItem>
                    <SelectItem value="recruiter">Recrutador</SelectItem>
                    <SelectItem value="viewer">Visualizador</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[130px] h-9">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos Status</SelectItem>
                    <SelectItem value="active">Ativo</SelectItem>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="inactive">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar usuário..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-9"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <TableSkeleton />
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                {searchQuery || roleFilter !== 'all' || statusFilter !== 'all' 
                  ? 'Nenhum usuário encontrado com os filtros aplicados' 
                  : 'Nenhum usuário cadastrado'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredUsers.map((user) => {
                const status = statusConfig[user.status]
                const StatusIcon = status.icon
                const roleConfig = roleLabels[user.role]

                return (
                  <div 
                    key={user.id}
                    className="flex items-center gap-4 p-3 rounded-md border hover:border-gray-900 dark:hover:border-gray-50 transition-colors"
                    style={{ borderColor: 'var(--eleven-border-subtle)' }}
                  >
                    <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        {user.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p 
                          className="font-medium truncate"
                          style={{ color: 'var(--eleven-text-primary)' }}
                        >
                          {user.name}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Mail className="w-3 h-3 text-gray-400" />
                        <p 
                          className="text-sm truncate"
                          style={{ color: 'var(--eleven-text-tertiary)' }}
                        >
                          {user.email}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={roleConfig.color}>
                        {roleConfig.label}
                      </Badge>
                      <Badge variant={status.variant} className="flex items-center gap-1">
                        <StatusIcon className="w-3 h-3" />
                        {status.label}
                      </Badge>
                      {user.is_scim_managed && (
                        <Badge className="bg-purple-50 text-purple-700 border-purple-200 flex items-center gap-1">
                          <Shield className="w-3 h-3" />
                          SSO
                        </Badge>
                      )}
                      <div className="text-right min-w-[100px]">
                        <p 
                          className="text-xs"
                          style={{ color: 'var(--eleven-text-tertiary)' }}
                        >
                          Último acesso
                        </p>
                        <p 
                          className="text-xs"
                          style={{ color: 'var(--eleven-text-secondary)' }}
                        >
                          {formatDateTime(user.lastLogin)}
                        </p>
                      </div>
                      {!isScimEnabled ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditModal(user)}>
                              <Pencil className="w-4 h-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Shield className="w-4 h-4 mr-2" />
                              <span className="mr-2">Alterar Role</span>
                              <DropdownMenu>
                                <DropdownMenuTrigger className="ml-auto">→</DropdownMenuTrigger>
                              </DropdownMenu>
                            </DropdownMenuItem>
                            {user.status === 'pending' && (
                              <DropdownMenuItem onClick={() => handleResendInvite(user.id)}>
                                <Send className="w-4 h-4 mr-2" />
                                Reenviar Convite
                              </DropdownMenuItem>
                            )}
                            {user.status === 'active' && (
                              <DropdownMenuItem 
                                onClick={() => {
                                  setSelectedUser(user)
                                  setShowDeactivateModal(true)
                                }}
                              >
                                <UserX className="w-4 h-4 mr-2" />
                                Desativar
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              className="text-red-600"
                              onClick={() => {
                                setSelectedUser(user)
                                setShowDeleteModal(true)
                              }}
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Remover
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <div className="w-8" />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Convidar Usuário</DialogTitle>
            <DialogDescription>
              Um convite será enviado para o email informado.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome completo *</Label>
              <Input
                placeholder="Nome do usuário"
                value={newUser.name}
                onChange={(e) => setNewUser(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                placeholder="email@empresa.com"
                value={newUser.email}
                onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Permissão</Label>
              <Select
                value={newUser.role}
                onValueChange={(value) => setNewUser(prev => ({ ...prev, role: value as User['role'] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Administrador</SelectItem>
                  <SelectItem value="manager">Gestor</SelectItem>
                  <SelectItem value="recruiter">Recrutador</SelectItem>
                  <SelectItem value="viewer">Visualizador</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddModal(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleAddUser} 
              disabled={isSaving}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Enviar Convite
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Usuário</DialogTitle>
            <DialogDescription>
              Atualize as informações do usuário.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome completo *</Label>
              <Input
                placeholder="Nome do usuário"
                value={editForm.name}
                onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                placeholder="email@empresa.com"
                value={editForm.email}
                onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Permissão</Label>
              <Select
                value={editForm.role}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, role: value as User['role'] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Administrador</SelectItem>
                  <SelectItem value="manager">Gestor</SelectItem>
                  <SelectItem value="recruiter">Recrutador</SelectItem>
                  <SelectItem value="viewer">Visualizador</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleEditUser} 
              disabled={isSaving}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : (
                'Salvar Alterações'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showDeactivateModal} onOpenChange={setShowDeactivateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Desativar Usuário</DialogTitle>
            <DialogDescription>
              O usuário perderá acesso à plataforma.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="flex items-center gap-3 p-4 rounded-md bg-amber-50 dark:bg-amber-950/20">
              <UserX className="w-5 h-5 text-amber-600" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Tem certeza que deseja desativar {selectedUser?.name}?
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  O usuário perderá acesso imediatamente, mas poderá ser reativado posteriormente.
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeactivateModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="default"
              className="bg-amber-500 hover:bg-amber-600 text-white"
              onClick={handleDeactivateUser} 
              disabled={isSaving}
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <UserX className="w-4 h-4 mr-2" />
              )}
              Desativar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remover Usuário</DialogTitle>
            <DialogDescription>
              Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="flex items-center gap-3 p-4 rounded-md bg-red-50 dark:bg-red-950/20">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Tem certeza que deseja remover {selectedUser?.name}?
                </p>
                <p className="text-xs text-red-700 dark:text-red-300 mt-1">
                  O usuário será permanentemente removido e todos os dados associados serão perdidos.
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="destructive"
              onClick={handleDeleteUser} 
              disabled={isSaving}
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Remover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
