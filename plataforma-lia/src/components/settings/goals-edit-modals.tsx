"use client"

import { Button } from "@/components/ui/button"
import {
  X, Save, Settings, Loader2
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import type { GoalTemplate, UserGoal } from "./use-goals-management"

interface GoalsEditGoalModalProps {
  editingGoal: UserGoal
  isSaving: boolean
  setEditingGoal: (val: UserGoal | null | ((prev: UserGoal | null) => UserGoal | null)) => void
  handleUpdateGoal: (goal: UserGoal, updates: UserGoal) => void
}

export function GoalsEditGoalModal({
  editingGoal,
  isSaving,
  setEditingGoal,
  handleUpdateGoal,
}: GoalsEditGoalModalProps) {
  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-xl p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Editar Meta</h3>
          <Button variant="ghost" onClick={() => setEditingGoal(null)}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Nome da Meta
            </label>
            <input
              type="text"
              value={editingGoal.name}
              onChange={(e) => setEditingGoal(prev => prev ? { ...prev, name: e.target.value } : null)}
              className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Meta
              </label>
              <input
                type="number"
                value={editingGoal.target}
                onChange={(e) => setEditingGoal(prev => prev ? { ...prev, target: parseFloat(e.target.value) || 0 } : null)}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
                min="0"
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Atual
              </label>
              <input
                type="number"
                value={editingGoal.current}
                onChange={(e) => setEditingGoal(prev => prev ? { ...prev, current: parseFloat(e.target.value) || 0 } : null)}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
                min="0"
                step="0.1"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Status
            </label>
            <select
              value={editingGoal.status}
              onChange={(e) => setEditingGoal(prev => prev ? { ...prev, status: e.target.value as UserGoal['status'] } : null)}
              className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
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
  )
}

interface GoalsEditTemplateModalProps {
  editingTemplate: GoalTemplate
  setEditingTemplate: (val: GoalTemplate | null | ((prev: GoalTemplate | null) => GoalTemplate | null)) => void
  setTemplateOverrides: (val: Record<string, Partial<GoalTemplate>> | ((prev: Record<string, Partial<GoalTemplate>>) => Record<string, Partial<GoalTemplate>>)) => void
}

export function GoalsEditTemplateModal({
  editingTemplate,
  setEditingTemplate,
  setTemplateOverrides,
}: GoalsEditTemplateModalProps) {
  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="bg-lia-bg-secondary px-5 py-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-lia-interactive-active">
              <Settings className="w-4 h-4 text-lia-text-primary" />
            </div>
            <div>
              <h3 className={textStyles.h4}>Editar Modelo</h3>
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
              className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
            />
          </div>

          <div>
            <label className={`${textStyles.label} block mb-1`}>Descrição</label>
            <input
              type="text"
              value={editingTemplate.description}
              onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, description: e.target.value } : null)}
              className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`${textStyles.label} block mb-1`}>Meta Padrão</label>
              <input
                type="number"
                value={editingTemplate.defaultTarget}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, defaultTarget: parseFloat(e.target.value) || 0 } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
              />
            </div>
            <div>
              <label className={`${textStyles.label} block mb-1`}>Unidade</label>
              <input
                type="text"
                value={editingTemplate.unit}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, unit: e.target.value } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`${textStyles.label} block mb-1`}>Período</label>
              <select
                value={editingTemplate.period}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, period: e.target.value as GoalTemplate['period'] } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
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
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
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
              className="text-xs h-8"
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
              className="text-xs h-8 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <Save className="w-3 h-3 mr-1.5" />
              Salvar Alterações
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
