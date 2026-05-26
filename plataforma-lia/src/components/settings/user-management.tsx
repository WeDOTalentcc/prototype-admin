"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  X, Search, UserPlus, Info, ExternalLink, CheckCircle
} from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import { useUserManagement } from './use-user-management'
import { UserForm } from './user-form'
// Bug 2 fix (2026-05-25): departments LIFTED to UsuariosDepartamentosHub parent
// (single source of truth). UserManagement consumes via props now.
import type { DepartmentItem } from "@/hooks/settings/useDepartmentsList"
import { UserList } from './user-list'
import type { UserManagementProps } from './user-management-types'
import { useTranslations } from "next-intl"

export function UserManagement({ departments: hubDepartments = [], onDepartmentChanged }: UserManagementProps = {}) {
  const t = useTranslations('settings.users')
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
  // Bug 2 fix (2026-05-25): use lifted props instead of own hook (single SoT)
  const deptList = hubDepartments
  const refetchDepartments = onDepartmentChanged ?? (() => {})

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="text-xs text-lia-text-secondary">{t('loading')}</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-6 gap-3">
        <div className="text-xs text-status-error">{error}</div>
        <Button onClick={fetchUsers} size="sm">{t('retryButton')}</Button>
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
        departments={deptList}
        onDepartmentCreated={refetchDepartments}
      />
    )
  }

  return (
    <div className="space-y-4" data-testid="users-management-root">
      {isSCIMEnabled && (
        <Card className="border-wedo-cyan/30 dark:border-wedo-cyan/30">
          <CardContent className="p-3 flex items-start gap-2">
            <Info className="w-4 h-4 text-wedo-cyan-dark dark:text-wedo-cyan-dark flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className={textStyles.subtitle}>
                {t('scimActiveTitle', { provider: scimConfig?.directoryName || 'SSO Enterprise' })}
              </p>
              <p className={textStyles.description + " mt-1"}>
                {t('scimActiveDescription')}
              </p>
            </div>
            <a
              href="https://workos.com/docs/directory-sync"
              target="_blank"
              rel="noopener noreferrer"
              className="text-wedo-cyan-dark dark:text-wedo-cyan-dark hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan-dark flex items-center gap-1 text-xs flex-shrink-0"
            >
              <ExternalLink className="w-3 h-3" />
              {t('scimLearnMore')}
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
              type="button"
              onClick={() => setSuccessMessage(null)}
              aria-label={t('dismissSuccess')}
              className="text-status-success dark:text-status-success hover:text-status-success dark:hover:text-status-success"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.h3}>{t('title')}</h3>
          <p className={textStyles.description}>
            {isSCIMEnabled 
              ? t('descriptionScim')
              : t('description')
            }
          </p>
        </div>
        {!isSCIMEnabled && (
          <Button data-testid="users-create-button" onClick={handleCreateUser} size="sm" className="gap-1.5">
            <UserPlus className="w-3.5 h-3.5" />
            {t('newUser')}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className={textStyles.metricLarge}>{stats.total}</div>
            <div className={textStyles.description}>{t('totalUsers')}</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-semibold text-status-success dark:text-status-success">{stats.active}</div>
            <div className={textStyles.description}>{t('activeUsers')}</div>
          </CardContent>
        </Card>
        <Card className="rounded-md">
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-semibold text-wedo-purple dark:text-wedo-purple">{stats.managers}</div>
            <div className={textStyles.description}>{t('managers')}</div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 transform -translate-y-1/2 text-lia-text-secondary" />
          <input
            type="text"
            data-testid="users-search-input"
            placeholder={t('searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
          />
        </div>

        <select
          data-testid="users-department-filter"
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">{t('allDepartments')}</option>
          {departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>

        <select
          data-testid="users-status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-2 py-1.5 text-xs border border-lia-border-default rounded-xl focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:bg-lia-bg-elevated dark:border-lia-border-default"
        >
          <option value="all">{t('allStatuses')}</option>
          <option value="active">{t('statusActive')}</option>
          <option value="inactive">{t('statusInactive')}</option>
          <option value="pending">{t('statusPending')}</option>
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
            {t('viewCards')}
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors motion-reduce:transition-none ${
              viewMode === 'table'
                ? 'bg-lia-bg-primary text-lia-text-primary'
                : 'text-lia-text-secondary hover:text-lia-text-primary'
            }`}
          >
            {t('viewTable')}
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
        onSalaryGrantChange={fetchUsers}
      />
    </div>
  )
}
