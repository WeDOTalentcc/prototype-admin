"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  Plus, Save, X, Users, Loader2, Settings
} from "lucide-react"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { textStyles } from "@/lib/design-tokens"
import { DeleteConfirmModal } from "./goals"
import type { GoalTemplate, UserGoal, CustomGoalForm } from "./use-goals-management"

interface GoalsMgmtUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

interface GoalsCustomGoalModalProps {
  onClose: () => void
  users: GoalsMgmtUser[]
  selectedUser: GoalsMgmtUser | null
  setSelectedUser: (user: GoalsMgmtUser | null) => void
  customGoalForm: CustomGoalForm
  setCustomGoalForm: React.Dispatch<React.SetStateAction<CustomGoalForm>>
  isSaving: boolean
  handleCreateCustomGoal: () => void
}

export function GoalsCustomGoalModal({
  onClose,
  users,
  selectedUser,
  setSelectedUser,
  customGoalForm,
  setCustomGoalForm,
  isSaving,
  handleCreateCustomGoal,
}: GoalsCustomGoalModalProps) {
  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-xl p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Nova Meta Customizada</h3>
          <Button variant="ghost" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
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
                    <Users className="w-4 h-4 text-lia-text-primary" />
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
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Nome da Meta *
            </label>
            <input
              type="text"
              value={customGoalForm.name}
              onChange={(e) => setCustomGoalForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
              placeholder="Ex: Aumentar taxa de conversão"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Descrição
            </label>
            <textarea
              value={customGoalForm.description}
              onChange={(e) => setCustomGoalForm(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
              rows={2}
              placeholder="Descreva a meta..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Meta *
              </label>
              <input
                type="number"
                value={customGoalForm.target}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, target: parseFloat(e.target.value) || 0 }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
                min="0"
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Unidade
              </label>
              <input
                type="text"
                value={customGoalForm.unit}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, unit: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
                placeholder="Ex: %, dias, contratações"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Período
              </label>
              <select
                value={customGoalForm.period}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, period: e.target.value as CustomGoalForm['period'] }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
              >
                <option value="monthly">Mensal</option>
                <option value="quarterly">Trimestral</option>
                <option value="yearly">Anual</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Categoria
              </label>
              <select
                value={customGoalForm.category}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, category: e.target.value as CustomGoalForm['category'] }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
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
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={customGoalForm.startDate}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={customGoalForm.endDate}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-xl text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={onClose}>
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
  )
}

interface GoalsEditGoalModalProps {
  editingGoal: UserGoal
  setEditingGoal: React.Dispatch<React.SetStateAction<UserGoal | null>>
  handleUpdateGoal: (goal: UserGoal, updates: UserGoal) => void
  isSaving: boolean
}

export function GoalsEditGoalModal({
  editingGoal,
  setEditingGoal,
  handleUpdateGoal,
  isSaving,
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
  setEditingTemplate: React.Dispatch<React.SetStateAction<GoalTemplate | null>>
  setTemplateOverrides: React.Dispatch<React.SetStateAction<Record<string, Partial<GoalTemplate>>>>
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
              className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
            />
          </div>

          <div>
            <label className={`${textStyles.label} block mb-1`}>Descrição</label>
            <input
              type="text"
              value={editingTemplate.description}
              onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, description: e.target.value } : null)}
              className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`${textStyles.label} block mb-1`}>Meta Padrão</label>
              <input
                type="number"
                value={editingTemplate.defaultTarget}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, defaultTarget: parseFloat(e.target.value) || 0 } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
              />
            </div>
            <div>
              <label className={`${textStyles.label} block mb-1`}>Unidade</label>
              <input
                type="text"
                value={editingTemplate.unit}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, unit: e.target.value } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`${textStyles.label} block mb-1`}>Período</label>
              <select
                value={editingTemplate.period}
                onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, period: e.target.value as GoalTemplate['period'] } : null)}
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
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
                className="w-full px-2.5 py-1.5 border border-lia-border-subtle rounded-xl text-xs font-['Open_Sans',sans-serif]"
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
              className="text-xs h-8 font-['Open_Sans',sans-serif] bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
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
