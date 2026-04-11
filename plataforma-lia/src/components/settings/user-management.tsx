"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  X, Search, UserPlus, Info, ExternalLink, CheckCircle
} from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import { useUserManagement } from './use-user-management'
import { UserForm } from './user-form'
import { UserList } from './user-list'
import type { UserManagementProps } from './user-management-types'

export function UserManagement(_props: UserManagementProps) {
  const {
    filteredUsers,
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
  } = useUserManagement()

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
      <UserForm
        isCreating={isCreating}
        formData={formData}
        setFormData={setFormData}
        onSave={handleSaveUser}
        onCancel={handleCancelForm}
      />
    )
  }

  return (
    <div className="space-y-4">
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className={textStyles.metricLarge}>{stats.total}</div>
            <div className={textStyles.description}>Total de Usuários</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-semibold text-status-success dark:text-status-success">{stats.active}</div>
            <div className={textStyles.description}>Usuários Ativos</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-semibold text-wedo-purple dark:text-wedo-purple">{stats.managers}</div>
            <div className={textStyles.description}>Gestores</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 transform -translate-y-1/2 text-lia-text-secondary" />
          <input
            type="text"
            placeholder="Buscar usuários..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
          />
        </div>

        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">Todos os Departamentos</option>
          {departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">Todos os Status</option>
          <option value="ativo">Ativo</option>
          <option value="inativo">Inativo</option>
          <option value="pendente">Pendente</option>
        </select>

        <div className="flex bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl p-0.5">
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

      <UserList
        filteredUsers={filteredUsers}
        viewMode={viewMode}
        isSCIMEnabled={isSCIMEnabled}
        resendingInvite={resendingInvite}
        getStatusColor={getStatusColor}
        onEditUser={handleEditUser}
        onDeleteUser={handleDeleteUser}
        onResendInvitation={handleResendInvitation}
      />
    </div>
  )
}
