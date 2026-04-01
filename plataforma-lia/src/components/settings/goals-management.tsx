"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Plus, Edit, Trash2, Save, X, Target, Users, BarChart3, Calendar,
  TrendingUp, Award, CheckCircle, AlertCircle, Clock, Percent,
  Timer, DollarSign, Star, Heart, Zap, UserCheck, Settings,
  Copy, Download, Upload, FileText, Search, Filter, Loader2,
  ChevronDown, ChevronRight, ChevronUp, User
} from "lucide-react"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { typography, textStyles } from "@/lib/design-tokens"
import { EditableCell, GoalsStatsCards, getCategoryIcon, getCategoryColor, getStatusColor } from "./goals"
import { ApplyAllModal, DeleteConfirmModal } from "./goals"

// Camada 1 (hook): Todo o estado e ações extraídas
import {
  useGoalsManagement,
  goalTemplates,
  MONTHS,
  type GoalTemplate,
  type UserGoal,
  type MonthlyGoalValue,
  type CustomGoalForm
} from "./use-goals-management"

interface GoalsMgmtUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

interface GoalsManagementProps {
  users: GoalsMgmtUser[]
  onGoalUpdate: (userId: string, goals: UserGoal[]) => void
}

export function GoalsManagement({ users, onGoalUpdate }: GoalsManagementProps) {
  const { state, actions } = useGoalsManagement(users, onGoalUpdate)
  const {
    selectedUser, showTemplates, showCustomGoal, editingGoal, searchTerm,
    filterCategory, filterPeriod, isLoading, isSaving, savingTemplateId, error,
    successMessage, userGoalsMap, selectedTemplateIds, templateApplyMode,
    deleteConfirmGoal, isDeleting, editingTemplate, templateOverrides, hiddenTemplates,
    selectedYear, collapsedGoals, monthlyGoals, showApplyAllModal, applyAllValue,
    applyAllMonths, applyAllUsers, templateUsersMap, customGoalForm,
    filteredTemplates, activeTemplatesWithUsers, goalStats
  } = state
  const {
    setSelectedUser, setShowTemplates, setShowCustomGoal, setEditingGoal,
    setSearchTerm, setFilterCategory, setFilterPeriod, setSelectedTemplateIds,
    setTemplateApplyMode, setDeleteConfirmGoal, setEditingTemplate, setTemplateOverrides,
    setHiddenTemplates, setSelectedYear, setCollapsedGoals, setShowApplyAllModal,
    setApplyAllValue, setApplyAllMonths, setApplyAllUsers, setCustomGoalForm,
    getMonthlyValue, calculateRowTotal, calculateColumnTotal, calculateGrandTotal,
    getEffectiveTemplate, isTemplateAppliedToUser, getAppliedTemplatesForUser, getUserById,
    findUserGoal, fetchUserGoals,
    setMonthlyValue, applyValueToAll, toggleGoalCollapse, toggleTemplateSelection,
    handleApplyTemplate, handleApplySelectedTemplates, handleCreateCustomGoal,
    handleUpdateGoal, handleDeleteGoal, confirmDeleteGoal, handleAddUserToTemplate
  } = actions

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-4 py-3 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 text-status-success px-4 py-3 rounded-md flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h3 className={`${textStyles.titleLarge} flex items-center gap-2`}>
              <Target className="w-5 h-5 lia-text-700 dark:text-lia-text-secondary" />
              Gestão de Metas - {selectedYear}
            </h3>
            <p className={textStyles.description}>
              Configure e acompanhe as metas de performance da equipe
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedYear.toString()} onValueChange={(val) => setSelectedYear(parseInt(val))}>
            <SelectTrigger className="w-24 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            onClick={() => setShowTemplates(true)} 
            className="gap-2 h-8 text-xs"
            disabled={users.length === 0 || isLoading}
          >
            <Plus className="w-3.5 h-3.5" />
            Aplicar Template
          </Button>
          <Button 
            onClick={() => {
              setSelectedUser(users.length > 0 ? users[0] : null)
              setCustomGoalForm(prev => ({
                ...prev,
                userId: users.length > 0 ? users[0].id : ''
              }))
              setShowCustomGoal(true)
            }} 
            className="gap-2 h-8 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
            disabled={users.length === 0 || isLoading}
          >
            <Target className="w-3.5 h-3.5" />
            Nova Meta
          </Button>
        </div>
      </div>

      <GoalsStatsCards
        totalTemplates={goalStats.totalTemplates}
        totalAssigned={goalStats.totalAssigned}
        achieved={goalStats.achieved}
        inProgress={goalStats.inProgress}
        overdue={goalStats.overdue}
      />

      <Card className="border border-lia-border-subtle dark:lia-border-800">
        <CardHeader className="py-3 border-b border-lia-border-subtle dark:lia-border-800">
          <CardTitle className={`${textStyles.h4} flex items-center justify-between`}>
            <span>Metas por Categoria</span>
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          {users.length === 0 ? (
            <div className="text-center py-8 lia-text-800 dark:text-lia-text-primary">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2`}>Nenhum usuário cadastrado</h3>
              <p className={textStyles.body}>Primeiro cadastre usuários na aba "Usuários" para poder configurar metas</p>
            </div>
          ) : activeTemplatesWithUsers.length === 0 ? (
            <div className="text-center py-8 lia-text-500 dark:text-lia-text-tertiary">
              <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2 !lia-text-950`}>Nenhuma meta configurada</h3>
              <p className={`${textStyles.body} mb-4`}>
                Clique em "Aplicar Template" para adicionar metas aos usuários
              </p>
              <Button 
                onClick={() => setShowTemplates(true)}
                className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
              >
                <Plus className="w-4 h-4" />
                Aplicar Template
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {activeTemplatesWithUsers.map((template) => {
                const isCollapsed = collapsedGoals.has(template.id)
                const assignedUserObjects = template.assignedUsers
                  .map(uid => getUserById(uid))
                  .filter(Boolean)

                return (
                  <div key={template.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
                    <div 
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none bg-gray-50/50"
                      onClick={() => toggleGoalCollapse(template.id)}
                    >
                      <div className="flex items-center gap-2 flex-1">
                        {isCollapsed ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronUp className="w-3.5 h-3.5" />
                        )}
                        {getCategoryIcon(template.category)}
                        <div>
                          <h4 className={`${textStyles.label} !lia-text-900 dark:!lia-text-50`}>
                            {template.name}
                          </h4>
                          <p className={textStyles.caption}>
                            {template.description}
                          </p>
                        </div>
                        <Badge className={`text-micro ml-2 ${getCategoryColor(template.category)}`}>
                          {template.category}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-micro gap-1"
                          onClick={() => {
                            setShowApplyAllModal(template.id)
                            const effectiveTemplate = getEffectiveTemplate(template)
                            setApplyAllValue(effectiveTemplate.defaultTarget)
                          }}
                        >
                          <Settings className="w-3 h-3" />
                          Aplicar para Todos
                        </Button>
                      </div>
                    </div>

                    {!isCollapsed && (
                      <div className="border-t border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/50">
                        <div className="overflow-x-auto">
                        <table className="w-full text-xs font-['Open_Sans',sans-serif]">
                          <thead>
                            <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                              <th className="text-left p-2 min-w-[140px] sticky left-0 bg-gray-50 dark:bg-lia-bg-secondary font-medium lia-text-600 dark:text-lia-text-tertiary border-r border-lia-border-subtle dark:border-lia-border-subtle">
                                Usuário
                              </th>
                              {MONTHS.map((month) => (
                                <th 
                                  key={month.num} 
                                  className="text-center p-2 min-w-10 lia-text-600 font-medium"
                                >
                                  {month.short}
                                </th>
                              ))}
                              <th className="text-center p-2 min-w-[50px] font-semibold lia-text-900 dark:lia-text-50">
                                Total
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {assignedUserObjects.map((user) => (
                              <tr key={user.id} className="border-b border-lia-border-subtle dark:lia-border-800 hover:bg-lia-bg-primary dark:hover:bg-gray-800">
                                <td className="p-2 sticky left-0 bg-gray-50 dark:bg-lia-bg-secondary border-r border-lia-border-subtle dark:border-lia-border-subtle">
                                  <div className="flex items-center gap-2">
                                    <Avatar className="w-5 h-5">
                                      <AvatarImage src={user.avatar} alt={user.name} />
                                      <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated lia-text-700 dark:text-lia-text-secondary font-medium text-micro">
                                        {user.name.split(' ').map((n: string) => n[0]).join('')}
                                      </AvatarFallback>
                                    </Avatar>
                                    // @ts-ignore TODO: fix type
                                    <span className="font-medium text-xs lia-text-800 dark:text-lia-text-primary truncate">{user.name}</span>
                                  </div>
                                </td>
                                {MONTHS.map((month) => (
                                  // @ts-ignore TODO: fix type
                                  <td 
                                    key={month.num} 
                                    className="p-1 text-center"
                                  >
                                    // @ts-ignore TODO: fix type
                                    <EditableCell
                                      value={getMonthlyValue(template.id, user.id, month.num, selectedYear)}
                                      onChange={(value) => setMonthlyValue(template.id, user.id, month.num, selectedYear, value)}
                                    />
                                  </td>
                                ))}
                                <td className="p-2 text-center font-semibold lia-text-900 dark:lia-text-50">
                                  {calculateRowTotal(template.id, user.id, selectedYear)}
                                </td>
                              </tr>
                            ))}
                            <tr className="border-t-2 border-lia-border-default dark:border-lia-border-default bg-gray-100 dark:bg-lia-bg-secondary">
                              <td className="p-2 font-semibold lia-text-800 dark:text-lia-text-primary sticky left-0 bg-gray-100 border-r border-lia-border-subtle">
                                TOTAL EQUIPE
                              </td>
                              {MONTHS.map((month) => (
                                <td 
                                  key={month.num} 
                                  // @ts-ignore TODO: fix type
                                  className="p-2 text-center font-semibold lia-text-800 dark:text-lia-text-primary"
                                >
                                  {calculateColumnTotal(template.id, month.num, selectedYear, template.assignedUsers)}
                                </td>
                              ))}
                              <td className="p-2 text-center font-bold lia-text-900 dark:lia-text-50">
                                {calculateGrandTotal(template.id, selectedYear, template.assignedUsers)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                        </div>
                        <div className="p-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddUserToTemplate(template.id)}
                            className="text-micro h-6 gap-1.5 rounded-xl lia-text-700 border-lia-border-default hover:bg-gray-100"
                            disabled={isSaving}
                          >
                            <Plus className="w-3 h-3" />
                            Adicionar Usuário
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {showApplyAllModal && (
        <ApplyAllModal
          templateId={showApplyAllModal}
          applyAllValue={applyAllValue}
          applyAllMonths={applyAllMonths}
          applyAllUsers={applyAllUsers}
          isSaving={isSaving}
          setApplyAllValue={setApplyAllValue}
          setApplyAllMonths={setApplyAllMonths}
          setApplyAllUsers={setApplyAllUsers}
          setShowApplyAllModal={setShowApplyAllModal}
          applyValueToAll={applyValueToAll}
        />
      )}

      {showTemplates && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-lia-bg-primary rounded-md p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className={textStyles.h4}>Templates de Metas</h3>
                <p className={textStyles.caption}>Selecione uma ou mais metas para aplicar</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => {
                setShowTemplates(false)
                setSelectedTemplateIds(new Set())
              }} className="h-6 w-6 p-0">
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>

            {selectedTemplateIds.size > 0 && (
              <div className="border rounded-md px-2.5 py-1.5 mb-3 flex items-center justify-between bg-gray-50 dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 lia-text-700 dark:text-lia-text-secondary" />
                  <span className={textStyles.caption}>
                    <strong>{selectedTemplateIds.size}</strong> template(s) selecionado(s)
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <select
                    value={templateApplyMode}
                    onChange={(e) => setTemplateApplyMode(e.target.value as 'all' | 'selected')}
                    className="border rounded-full px-1.5 py-0.5 text-micro bg-white dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default lia-text-900 dark:text-lia-text-primary font-['Open_Sans',sans-serif]"
                  >
                    <option value="all">Aplicar a todos usuários</option>
                    {selectedUser && <option value="selected">Aplicar a {selectedUser.name}</option>}
                  </select>
                  <Button
                    size="sm"
                    onClick={handleApplySelectedTemplates}
                    disabled={isSaving}
                    className="text-micro h-6 bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 font-['Open_Sans',sans-serif]"
                  >
                    {isSaving ? <Loader2 className="w-2.5 h-2.5 animate-spin motion-reduce:animate-none mr-1" /> : <Plus className="w-2.5 h-2.5 mr-1" />}
                    Aplicar Selecionados
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedTemplateIds(new Set())}
                    className="text-micro h-6 font-['Open_Sans',sans-serif]"
                  >
                    Limpar
                  </Button>
                </div>
              </div>
            )}

            <div className="flex gap-2 mb-3">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 lia-text-400 dark:lia-text-500" />
                  <input
                    type="text"
                    placeholder="Buscar templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-7 pr-2.5 py-1 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary text-micro font-['Open_Sans',sans-serif]"
                  />
                </div>
              </div>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary px-2 py-1 text-micro font-['Open_Sans',sans-serif]"
              >
                <option value="all">Todas Categorias</option>
                <option value="recruitment">Recrutamento</option>
                <option value="quality">Qualidade</option>
                <option value="efficiency">Eficiência</option>
                <option value="satisfaction">Satisfação</option>
              </select>
              <select
                value={filterPeriod}
                onChange={(e) => setFilterPeriod(e.target.value)}
                className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary px-2 py-1 text-micro font-['Open_Sans',sans-serif]"
              >
                <option value="all">Todos Períodos</option>
                <option value="monthly">Mensal</option>
                <option value="quarterly">Trimestral</option>
                <option value="yearly">Anual</option>
              </select>
            </div>

            {hiddenTemplates.size > 0 && (
              <div className="bg-status-warning/10 border border-status-warning/30 rounded-md px-3 py-1.5 mb-4 flex items-center justify-between">
                <span className={`${textStyles.bodySmall} !text-status-warning`}>
                  {hiddenTemplates.size} template(s) oculto(s)
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setHiddenTemplates(new Set())}
                  className="text-xs text-status-warning hover:text-status-warning hover:bg-status-warning/15 h-7 font-['Open_Sans',sans-serif]"
                >
                  Restaurar Todos
                </Button>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTemplates.map((template) => {
                const appliedCount = Object.values(userGoalsMap).reduce((count, periodGoals) => {
                  const allGoals = [...(periodGoals.monthly || []), ...(periodGoals.quarterly || []), ...(periodGoals.yearly || [])]
                  return count + (allGoals.some(g => g.templateId === template.id) ? 1 : 0)
                }, 0)
                const isAppliedToAll = appliedCount === users.length && users.length > 0
                const isPartiallyApplied = appliedCount > 0 && appliedCount < users.length
                const isSelected = selectedTemplateIds.has(template.id)
                const isAppliedToSelectedUser = selectedUser ? isTemplateAppliedToUser(template.id, selectedUser.id) : false
                
                return (
                <div 
                  key={template.id} 
                  onClick={() => !isAppliedToAll && toggleTemplateSelection(template.id)}
                  className={`border rounded-md p-3 transition-colors motion-reduce:transition-none cursor-pointer ${
                    isAppliedToAll 
                      ? 'border-status-success/30 bg-status-success/10 opacity-60 cursor-not-allowed' 
                      : isSelected
                        ? 'border-gray-900 bg-gray-50 ring-2 ring-gray-400'
                        : isPartiallyApplied 
                          ? 'border-status-warning/30 bg-status-warning/10 hover:border-gray-400' 
                          : 'border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <div className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-colors motion-reduce:transition-none ${
                        isAppliedToAll 
                          ? 'bg-status-success border-status-success/30'
                          : isSelected 
                            ? 'bg-gray-900 border-gray-900 dark:lia-bg-50 dark:lia-border-50' 
                            : 'border-lia-border-default bg-lia-bg-primary'
                      }`}>
                        {(isSelected || isAppliedToAll) && <CheckCircle className="w-2.5 h-2.5 text-white dark:lia-text-900" />}
                      </div>
                      {getCategoryIcon(template.category)}
                      <div>
                        <h4 className={textStyles.label}>{template.name}</h4>
                        <p className={textStyles.caption}>{template.description}</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-0.5">
                      <Badge className={`text-micro px-1.5 py-0.5 font-['Open_Sans',sans-serif] ${getCategoryColor(template.category)}`}>
                        {template.category}
                      </Badge>
                      {isAppliedToAll && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-status-success/15 text-status-success border-status-success/30 font-['Open_Sans',sans-serif]">
                          <CheckCircle className="w-2.5 h-2.5 mr-0.5" />
                          Aplicado a Todos
                        </Badge>
                      )}
                      {isPartiallyApplied && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-status-warning/15 text-status-warning border-status-warning/30 font-['Open_Sans',sans-serif]">
                          {appliedCount}/{users.length} usuários
                        </Badge>
                      )}
                      {selectedUser && isAppliedToSelectedUser && !isAppliedToAll && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-subtle font-['Open_Sans',sans-serif]">
                          Já aplicado a {selectedUser.name.split(' ')[0]}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-md px-1.5 py-1 mb-2 border-l-2 border-gray-400 ml-6">
                    <div className="flex items-start gap-1">
                      <BarChart3 className="w-2.5 h-2.5 lia-text-500 dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                      <p className={textStyles.caption}>
                        <span className="font-medium lia-text-600 dark:text-lia-text-tertiary">Como é calculado:</span>{' '}
                        {template.formula}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-micro ml-6">
                    <span className={textStyles.caption}>
                      Meta: {template.defaultTarget} {template.unit}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <Badge variant="outline" className="text-micro px-1.5 py-0.5 font-['Open_Sans',sans-serif]">
                        {template.period === 'monthly' ? 'Mensal' :
                         template.period === 'quarterly' ? 'Trimestral' : 'Anual'}
                      </Badge>
                      <div className="flex items-center gap-0.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingTemplate(template)
                          }}
                          className="h-5 w-5 p-0 hover:bg-gray-100 hover:lia-text-900"
                          title="Editar template"
                        >
                          <Edit className="w-2.5 h-2.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setHiddenTemplates(prev => new Set([...prev, template.id]))
                          }}
                          className="h-5 w-5 p-0 hover:bg-status-error/10 hover:text-status-error"
                          title="Ocultar template"
                        >
                          <X className="w-2.5 h-2.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          </div>
        </div>
      )}

      {showCustomGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-lia-bg-primary rounded-md p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Nova Meta Customizada</h3>
              <Button variant="ghost" onClick={() => {
                setShowCustomGoal(false)
                setSelectedUser(null)
              }}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                  Aplicar para *
                </label>
                <Select
                  value={customGoalForm.userId || selectedUser?.id || ''}
                  onValueChange={(value) => {
                    setCustomGoalForm(prev => ({ ...prev, userId: value }))
                    if (value === '__all__') {
                      setSelectedUser(null)
                    } else {
                      setSelectedUser(users.find(u => u.id === value) || null)
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione usuário ou todos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">
                      <span className="flex items-center gap-2">
                        <Users className="w-4 h-4 lia-text-700 dark:text-lia-text-secondary" />
                        <span className="font-medium">Todos os Usuários</span>
                      </span>
                    </SelectItem>
                    <div className="border-t border-lia-border-subtle my-1" />
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.name} - {user.role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {customGoalForm.userId === '__all__' && (
                  <p className={`${textStyles.caption} mt-1`}>
                    A meta será criada para todos os {users.length} usuários
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                  Nome da Meta *
                </label>
                <input
                  type="text"
                  value={customGoalForm.name}
                  onChange={(e) => setCustomGoalForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  placeholder="Ex: Aumentar taxa de conversão"
                />
              </div>

              <div>
                <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                  Descrição
                </label>
                <textarea
                  value={customGoalForm.description}
                  onChange={(e) => setCustomGoalForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  rows={2}
                  placeholder="Descreva a meta..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Meta *
                  </label>
                  <input
                    type="number"
                    value={customGoalForm.target}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, target: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Unidade
                  </label>
                  <input
                    type="text"
                    value={customGoalForm.unit}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, unit: e.target.value }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                    placeholder="Ex: %, dias, contratações"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Período
                  </label>
                  <select
                    value={customGoalForm.period}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, period: e.target.value as CustomGoalForm['period'] }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  >
                    <option value="monthly">Mensal</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="yearly">Anual</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Categoria
                  </label>
                  <select
                    value={customGoalForm.category}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, category: e.target.value as CustomGoalForm['category'] }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  >
                    <option value="recruitment">Recrutamento</option>
                    <option value="quality">Qualidade</option>
                    <option value="efficiency">Eficiência</option>
                    <option value="satisfaction">Satisfação</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Data Início
                  </label>
                  <input
                    type="date"
                    value={customGoalForm.startDate}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, startDate: e.target.value }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Data Fim
                  </label>
                  <input
                    type="date"
                    value={customGoalForm.endDate}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, endDate: e.target.value }))}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => {
                  setShowCustomGoal(false)
                  setSelectedUser(null)
                }}>
                  Cancelar
                </Button>
                <Button onClick={handleCreateCustomGoal} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Criar Meta
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-lia-bg-primary rounded-md p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Editar Meta</h3>
              <Button variant="ghost" onClick={() => setEditingGoal(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                  Nome da Meta
                </label>
                <input
                  type="text"
                  value={editingGoal.name}
                  onChange={(e) => setEditingGoal(prev => prev ? { ...prev, name: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Meta
                  </label>
                  <input
                    type="number"
                    value={editingGoal.target}
                    onChange={(e) => setEditingGoal(prev => prev ? { ...prev, target: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                    Atual
                  </label>
                  <input
                    type="number"
                    value={editingGoal.current}
                    onChange={(e) => setEditingGoal(prev => prev ? { ...prev, current: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-1">
                  Status
                </label>
                <select
                  value={editingGoal.status}
                  onChange={(e) => setEditingGoal(prev => prev ? { ...prev, status: e.target.value as UserGoal['status'] } : null)}
                  className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                >
                  <option value="pending">Pendente</option>
                  <option value="in_progress">Em Progresso</option>
                  <option value="achieved">Atingida</option>
                  <option value="overdue">Atrasada</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setEditingGoal(null)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={() => handleUpdateGoal(editingGoal, editingGoal)}
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Salvar Alterações
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmGoal && (
        <DeleteConfirmModal
          goal={deleteConfirmGoal}
          isDeleting={isDeleting}
          onCancel={() => setDeleteConfirmGoal(null)}
          onConfirm={confirmDeleteGoal}
        />
      )}

      {editingTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-lia-bg-primary rounded-md w-full max-w-md mx-4 overflow-hidden">
            <div className="bg-gray-50 px-5 py-3 border-b border-lia-border-subtle">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-200">
                  <Settings className="w-4 h-4 lia-text-700" />
                </div>
                <div>
                  <h3 className={textStyles.h4}>Editar Template</h3>
                  <p className={textStyles.caption}>Personalize os valores padrão</p>
                </div>
              </div>
            </div>

            <div className="p-5 space-y-3">
              <div>
                <label className={`${textStyles.label} block mb-1`}>Nome da Meta</label>
                <input
                  type="text"
                  value={editingTemplate.name}
                  onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, name: e.target.value } : null)}
                  className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                />
              </div>

              <div>
                <label className={`${textStyles.label} block mb-1`}>Descrição</label>
                <input
                  type="text"
                  value={editingTemplate.description}
                  onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, description: e.target.value } : null)}
                  className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Meta Padrão</label>
                  <input
                    type="number"
                    value={editingTemplate.defaultTarget}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, defaultTarget: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                  />
                </div>
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Unidade</label>
                  <input
                    type="text"
                    value={editingTemplate.unit}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, unit: e.target.value } : null)}
                    className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Período</label>
                  <select
                    value={editingTemplate.period}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, period: e.target.value as GoalTemplate['period'] } : null)}
                    className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                  >
                    <option value="monthly">Mensal</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="yearly">Anual</option>
                  </select>
                </div>
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Categoria</label>
                  <select
                    value={editingTemplate.category}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, category: e.target.value as GoalTemplate['category'] } : null)}
                    className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-md text-xs font-['Open_Sans',sans-serif]"
                  >
                    <option value="recruitment">Recrutamento</option>
                    <option value="quality">Qualidade</option>
                    <option value="efficiency">Eficiência</option>
                    <option value="satisfaction">Satisfação</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setEditingTemplate(null)}
                  className="text-xs h-8 font-['Open_Sans',sans-serif]"
                >
                  Cancelar
                </Button>
                <Button 
                  size="sm"
                  onClick={() => {
                    if (editingTemplate) {
                      setTemplateOverrides(prev => ({
                        ...prev,
                        [editingTemplate.id]: {
                          name: editingTemplate.name,
                          description: editingTemplate.description,
                          defaultTarget: editingTemplate.defaultTarget,
                          unit: editingTemplate.unit,
                          period: editingTemplate.period,
                          category: editingTemplate.category
                        }
                      }))
                      setEditingTemplate(null)
                    }
                  }}
                  className="text-xs h-8 font-['Open_Sans',sans-serif] bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                >
                  <Save className="w-3 h-3 mr-1.5" />
                  Salvar Alterações
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
