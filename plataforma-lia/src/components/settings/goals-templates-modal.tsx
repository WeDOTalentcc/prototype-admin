"use client"

import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Plus, Edit, X, BarChart3,
  CheckCircle, Search, Loader2
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"
import { getCategoryIcon, getCategoryColor } from"./goals"
import type { GoalTemplate, UserGoal } from"./use-goals-management"

interface GoalsMgmtUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

interface GoalsTemplatesModalProps {
  users: GoalsMgmtUser[]
  selectedUser: GoalsMgmtUser | null
  searchTerm: string
  filterCategory: string
  filterPeriod: string
  isSaving: boolean
  selectedTemplateIds: Set<string>
  templateApplyMode: 'all' | 'selected'
  hiddenTemplates: Set<string>
  filteredTemplates: GoalTemplate[]
  userGoalsMap: Record<string, { monthly?: UserGoal[]; quarterly?: UserGoal[]; yearly?: UserGoal[] }>
  setSearchTerm: (val: string) => void
  setFilterCategory: (val: string) => void
  setFilterPeriod: (val: string) => void
  setSelectedTemplateIds: (val: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setTemplateApplyMode: (val: 'all' | 'selected') => void
  setHiddenTemplates: (val: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setShowTemplates: (val: boolean) => void
  setEditingTemplate: (val: GoalTemplate | null) => void
  isTemplateAppliedToUser: (templateId: string, userId: string) => boolean
  toggleTemplateSelection: (id: string) => void
  handleApplySelectedTemplates: () => void
}

export function GoalsTemplatesModal({
  users,
  selectedUser,
  searchTerm,
  filterCategory,
  filterPeriod,
  isSaving,
  selectedTemplateIds,
  templateApplyMode,
  hiddenTemplates,
  filteredTemplates,
  userGoalsMap,
  setSearchTerm,
  setFilterCategory,
  setFilterPeriod,
  setSelectedTemplateIds,
  setTemplateApplyMode,
  setHiddenTemplates,
  setShowTemplates,
  setEditingTemplate,
  isTemplateAppliedToUser,
  toggleTemplateSelection,
  handleApplySelectedTemplates,
}: GoalsTemplatesModalProps) {
  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className={textStyles.h4}>Modelos de Metas</h3>
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
          <div className="border rounded-md px-2.5 py-1.5 mb-3 flex items-center justify-between bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-lia-text-primary" />
              <span className={textStyles.caption}>
                <strong>{selectedTemplateIds.size}</strong> template(s) selecionado(s)
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <select
                value={templateApplyMode}
                onChange={(e) => setTemplateApplyMode(e.target.value as 'all' | 'selected')}
                className="border rounded-full px-1.5 py-0.5 text-micro bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default text-lia-text-primary"
              >
                <option value="all">Aplicar a todos usuários</option>
                {selectedUser && <option value="selected">Aplicar a {selectedUser.name}</option>}
              </select>
              <Button
                size="sm"
                onClick={handleApplySelectedTemplates}
                disabled={isSaving}
                className="text-micro h-6 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                {isSaving ? <Loader2 className="w-2.5 h-2.5 animate-spin motion-reduce:animate-none mr-1" /> : <Plus className="w-2.5 h-2.5 mr-1" />}
                Aplicar Selecionados
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedTemplateIds(new Set())}
                className="text-micro h-6"
              >
                Limpar
              </Button>
            </div>
          </div>
        )}

        <div className="flex gap-2 mb-3">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-lia-text-tertiary" />
              <input
                type="text"
                placeholder="Buscar modelos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-7 pr-2.5 py-1 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary text-micro"
              />
            </div>
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary px-2 py-1 text-micro"
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
            className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary px-2 py-1 text-micro"
          >
            <option value="all">Todos Períodos</option>
            <option value="monthly">Mensal</option>
            <option value="quarterly">Trimestral</option>
            <option value="yearly">Anual</option>
          </select>
        </div>

        {hiddenTemplates.size > 0 && (
          <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl px-3 py-1.5 mb-4 flex items-center justify-between">
            <span className={`${textStyles.bodySmall} !text-status-warning`}>
              {hiddenTemplates.size} template(s) oculto(s)
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHiddenTemplates(new Set())}
              className="text-xs text-status-warning hover:text-status-warning hover:bg-status-warning/15 h-7"
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
                    ? 'border-lia-btn-primary-bg bg-lia-bg-secondary ring-2 ring-lia-border-medium'
                    : isPartiallyApplied 
                      ? 'border-status-warning/30 bg-status-warning/10 hover:border-lia-border-medium' 
                      : 'border-lia-border-subtle hover:border-lia-border-medium hover:bg-lia-bg-secondary'
              }`}
            >
              <div className="flex items-start justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-colors motion-reduce:transition-none ${
                    isAppliedToAll 
                      ? 'bg-status-success border-status-success/30'
                      : isSelected 
                        ? 'bg-lia-btn-primary-bg border-lia-btn-primary-bg dark:border-lia-border-subtle' 
                        : 'border-lia-border-default bg-lia-bg-primary'
                  }`}>
                    {(isSelected || isAppliedToAll) && <CheckCircle className="w-2.5 h-2.5 text-white" />}
                  </div>
                  {getCategoryIcon(template.category)}
                  <div>
                    <h4 className={textStyles.label}>{template.name}</h4>
                    <p className={textStyles.caption}>{template.description}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-0.5">
                  <Chip variant="neutral" muted className={`text-micro px-1.5 py-0.5 ${getCategoryColor(template.category)}`}>
                    {template.category}
                  </Chip>
                  {isAppliedToAll && (
                    <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5  border-status-success/30">
                      <CheckCircle className="w-2.5 h-2.5 mr-0.5" />
                      Aplicado a Todos
                    </Chip>
                  )}
                  {isPartiallyApplied && (
                    <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5  border-status-warning/30">
                      {appliedCount}/{users.length} usuários
                    </Chip>
                  )}
                  {selectedUser && isAppliedToSelectedUser && !isAppliedToAll && (
                    <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle">
                      Já aplicado a {selectedUser.name.split(' ')[0]}
                    </Chip>
                  )}
                </div>
              </div>
              
              <div className="bg-lia-bg-secondary rounded-md px-1.5 py-1 mb-2 border-l-2 border-lia-border-medium ml-6">
                <div className="flex items-start gap-1">
                  <BarChart3 className="w-2.5 h-2.5 text-lia-text-secondary mt-0.5 flex-shrink-0" />
                  <p className={textStyles.caption}>
                    <span className="font-medium text-lia-text-secondary">Como é calculado:</span>{' '}
                    {template.formula}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between text-micro ml-6">
                <span className={textStyles.caption}>
                  Meta: {template.defaultTarget} {template.unit}
                </span>
                <div className="flex items-center gap-1.5">
                  <Chip variant="neutral" className="text-micro px-1.5 py-0.5">
                    {template.period === 'monthly' ? 'Mensal' :
                     template.period === 'quarterly' ? 'Trimestral' : 'Anual'}
                  </Chip>
                  <div className="flex items-center gap-0.5">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setEditingTemplate(template)
                      }}
                      className="h-5 w-5 p-0 hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
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
  )
}
